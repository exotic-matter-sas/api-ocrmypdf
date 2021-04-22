import logging
import os
import secrets
import subprocess
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from threading import BoundedSemaphore
from typing import Optional, List, Dict
from uuid import UUID

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import (
    FastAPI,
    File,
    UploadFile,
    HTTPException,
    BackgroundTasks,
    Depends,
    Security,
    Response,
    Query,
)
from fastapi.openapi.models import APIKey
from fastapi.responses import FileResponse
from fastapi.security import APIKeyHeader
from pydantic import ValidationError
from starlette.status import HTTP_403_FORBIDDEN

from api.models import Document, Lang
from api.settings import config
from api.tools import save_upload_file

logger = logging.getLogger("gunicorn.error")

app = FastAPI(
    title="Fast ocrmypdf",
    description="Basic API for ocrmypdf",
    version="0.1.1",
    redoc_url=None,
)
Schedule = AsyncIOScheduler({"apscheduler.timezone": "UTC"})
Schedule.start()

pool_ocr = BoundedSemaphore(value=config.max_ocr_process)

documents: Dict[UUID, Document] = {}
workdir = config.workdir

script_directory = Path(os.path.dirname(os.path.abspath(__file__))).resolve()
expiration_delta = timedelta(hours=config.document_expire_hour)

if not workdir.exists():
    workdir.mkdir()


def clean_docs():
    logger.info("Cleaning documents")
    now = datetime.now()
    for key, document in documents.items():
        d = Document.parse_obj(document)
        if d.expire < now:
            logger.info(f"Deleting expired document {key}")
            d.delete_all_files()


def do_ocr(_doc: Document):
    pool_ocr.acquire()
    _doc.ocr(config.enable_wsl_compat)
    pool_ocr.release()


api_key_header = APIKeyHeader(name="X-API-KEY")


@app.on_event("startup")
async def startup_event():
    now = datetime.now()
    for f_json in (script_directory / workdir).glob("o_*_*.json"):
        try:
            d = Document.parse_file(f_json)
        except ValidationError as e:
            logging.exception(e)
        else:
            if d.pid not in documents:
                if d.expire > now and d.output.exists():
                    documents[d.pid] = d
                    logger.info(f"Loaded existing document {d.pid}")
                else:
                    logger.info(f"Deleting expired document {d.pid}")
                    d.delete_all_files()

    Schedule.add_job(
        clean_docs, "interval", minutes=1, id="cleaning_docs_task", coalesce=True
    )


async def check_api_key(x_api_key: str = Security(api_key_header)):
    if secrets.compare_digest(x_api_key, config.api_key_secret):
        return api_key_header
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )


@app.get("/", include_in_schema=False, status_code=204, response_class=Response)
def root():
    pass


@app.get("/status", include_in_schema=False)
def status():
    ocrmypdf = subprocess.check_output(
        f"{config.base_command_ocr} --version", shell=True
    )
    return {"status": "ok", "version_ocr": ocrmypdf.strip()}


@app.get("/ocr/{pid}", response_model=Document)
def get_doc_detail(pid: UUID, api_key: APIKey = Depends(check_api_key)):
    if pid in documents:
        return documents[pid]
    raise HTTPException(status_code=404)


@app.get("/ocr/{pid}/pdf")
def get_doc_pdf(pid: UUID, api_key: APIKey = Depends(check_api_key)):
    if pid in documents:
        output_doc = documents[pid].output

        if output_doc.resolve().exists():
            return FileResponse(
                str(output_doc.resolve()),
                headers={"Content-Type": "application/pdf"},
                filename=f"{pid}.pdf",
            )

    raise HTTPException(status_code=404)


@app.get("/ocr/{pid}/txt")
def get_doc_txt(pid: UUID, api_key: APIKey = Depends(check_api_key)):
    if pid in documents:
        output_doc_txt = documents[pid].output_txt

        if output_doc_txt.resolve().exists():
            return FileResponse(
                str(output_doc_txt.resolve()),
                headers={"Content-Type": "text/plain; charset=utf-8"},
                filename=f"{pid}.txt",
            )

    raise HTTPException(status_code=404)


@app.post(
    "/ocr", response_model=Document, status_code=202,
)
async def ocr(
    background_tasks: BackgroundTasks,
    lang: Optional[List[str]] = Query([Lang.eng]),
    file: UploadFile = File(...),
    api_key: APIKey = Depends(check_api_key),
):
    pid = uuid.uuid4()
    now = datetime.now()
    expire = now + expiration_delta
    filename = f"{pid}_{int(expire.timestamp())}"

    input_file = workdir / Path(f"i_{filename}.pdf")
    save_upload_file(file, input_file)
    output_file = workdir / Path(f"o_{filename}.pdf")
    output_file_json = workdir / Path(f"o_{filename}.json")
    output_file_txt = workdir / Path(f"o_{filename}.txt")
    documents[pid] = Document.parse_obj(
        {
            "pid": pid,
            "lang": lang,
            "input": input_file,
            "output": output_file,
            "output_json": output_file_json,
            "output_txt": output_file_txt,
            "status": "received",
            "created": now,
            "expire": expire,
        }
    )
    documents[pid].save_state()

    background_tasks.add_task(do_ocr, documents[pid])

    return documents[pid]
