FROM ubuntu:focal

RUN apt-get update && \
    apt-get -y --no-install-recommends install \
        tzdata \
        ghostscript \
        icc-profiles-free \
        liblept5 \
        libxml2 \
        pngquant \
        python3-pip \
        tesseract-ocr \
        tesseract-ocr-eng \
        tesseract-ocr-fra \
        tesseract-ocr-dan \
        tesseract-ocr-nld \
        tesseract-ocr-fin \
        tesseract-ocr-deu \
        tesseract-ocr-hun \
        tesseract-ocr-ita \
        tesseract-ocr-nor \
        tesseract-ocr-por \
        tesseract-ocr-ron \
        tesseract-ocr-rus \
        tesseract-ocr-spa \
        tesseract-ocr-swe \
        tesseract-ocr-tur \
        zlib1g && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip3 install ocrmypdf==11.7.3

ADD requirements.txt /app/requirements.txt
RUN pip3 install -r requirements.txt

ADD main.py /app/main.py
ADD models.py /app/models.py
ADD settings.py /app/settings.py
ADD tools.py /app/tools.py

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]