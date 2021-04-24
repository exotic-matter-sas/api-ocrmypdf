# OCRmyPDF - API (using FastAPI)

API server for OCRmyPDF

[OCRmyPDF](https://ocrmypdf.readthedocs.io) is a command line tool for applying Optical Character Recognition on PDF
documents. This project aims to provide a basic API to use OCRmyPDF as a server.

This was mainly done for use with [Paper Matter](https://gitlab.com/exotic-matter/ftl-app), an easy to use document
management system.

**Fair warning: this is work in progress project.**

## Usage

Latest master image available here: `registry.gitlab.com/exotic-matter/api-ocrmypdf:master`

## Settings

There are some settings which can be configured via environment variable. The list is available in `settings.py`. Simply
apply upper case to the name of the setting.

## Development

 * Python 3.7+
 * OCRmyPDF 12.+ Refer to [OCRmyPDF docs](https://ocrmypdf.readthedocs.io) for
instructions.

```shell
pip install -r requirements.txt
pip install -r requirements_dev.txt
uvicorn main:app --reload
```

### On Windows

Development on Windows (excluding OCRmyPDF itself) is possible if you use WSL, a compatible Linux distro such as
Ubuntu (available on the Windows Store) and install OCRmyPDF inside WSL. You will need to set some settings for
api-ocrmypdf to make it work.

Environment variables to set before starting server

 * `BASE_COMMAND_OCR = wsl [path to ocrmypdf bin inside WSL]`
 * `WORKDIR = [absolute directory to the work directory]`
 * `ENABLE_WSL_COMPAT = 1`

##### Example
```shell
BASE_COMMAND_OCR=wsl /home/mywinuser/.local/bin/ocrmypdf
WORKDIR=C:\dev\api-ocrmypdf\workdir;
ENABLE_WSL_COMPAT=1
```

## Tests

```shell
python -m pytest
```

## License

MIT (be aware, OCRmyPDF has its own licenses due to multiple dependencies)