import shutil
from pathlib import Path

from fastapi import UploadFile


def save_upload_file(upload_file: UploadFile, destination: Path) -> None:
    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()


def special_win_wslpath(path: Path) -> str:
    """
    This is a special function returning a compatible path for user of OCRmyPDF inside WSL
    """
    return f"`wslpath -a '{str(path)}'`"
