import subprocess
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel

from api.settings import config


class Lang(str, Enum):
    eng = "eng"
    fra = "fra"
    dan = "dan"
    nld = "nld"
    fin = "fin"
    deu = "deu"
    hun = "hun"
    ita = "ita"
    nor = "nor"
    por = "por"
    ron = "ron"
    rus = "rus"
    spa = "spa"
    swe = "swe"
    tur = "tur"


class Document(BaseModel):
    pid: UUID
    lang: List[Lang]
    status: str
    input: Path
    output: Path
    output_json: Path
    output_txt: Path
    result: Optional[str] = None
    code: Optional[int] = None
    created: datetime
    processing: Optional[datetime] = None
    expire: datetime
    finished: Optional[datetime] = None

    def ocr(self):
        self.status = "processing"
        self.processing = datetime.now()
        self.save_state()
        try:
            output = subprocess.check_output(
                " ".join(
                    [
                        config.base_command_ocr,
                        config.base_command_option,
                        f"-l {'+'.join([l.value for l in self.lang])}",
                        f"--sidecar {self.output_txt.resolve().relative_to(config.basedir).as_posix()}",
                        self.input.resolve().relative_to(config.basedir).as_posix(),
                        self.output.resolve().relative_to(config.basedir).as_posix(),
                    ]
                ),
                stderr=subprocess.STDOUT,
                shell=True,
            )
        except subprocess.CalledProcessError as e:
            self.status = "error"
            self.code = e.returncode
            self.result = e.output.strip()
            self.finished = datetime.now()
        else:
            self.status = "done"
            self.code = 0
            self.result = str(output).strip()
            self.finished = datetime.now()
        finally:
            self.save_state()

    def save_state(self):
        with open(self.output_json, "w") as ff:
            ff.write(self.json())

    def delete_all_files(self):
        if self.input.exists():
            self.input.unlink()
        if self.output.exists():
            self.output.unlink()
        if self.output_json.exists():
            self.output_json.unlink()
        if self.output_txt.exists():
            self.output_txt.unlink()
