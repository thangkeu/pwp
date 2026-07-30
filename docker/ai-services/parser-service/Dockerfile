FROM python:3.12-slim AS base

# tesseract-ocr: bắt buộc cho ImageOcrAdapter (FR-KB-01 "ảnh có chữ qua OCR").
# vie: gói ngôn ngữ tiếng Việt cho tesseract, khớp PARSER_OCR_LANGUAGES=eng+vie mặc định.
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-vie \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV PYTHONUNBUFFERED=1
EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
