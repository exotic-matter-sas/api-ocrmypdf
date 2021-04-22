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

Require `ocrmypdf` to be installed on your system. Refer to [OCRmyPDF docs](https://ocrmypdf.readthedocs.io) for
instructions.

```shell
pip install -r requirements.txt
pip install -r requirements_dev.txt
uvicorn main:app --reload
```

## Tests

```shell
cd tests && pytest
```

## License

MIT (be aware, OCRmyPDF has its own licenses due to multiple dependencies)