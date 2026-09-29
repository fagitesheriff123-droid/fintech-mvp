FROM python:3.11-slim
WORKDIR /app
# tesseract-ocr: needed for scanned/image-only bank statement PDFs (no text layer),
# which pdfplumber alone can't read. Digital PDFs never touch this path.
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
