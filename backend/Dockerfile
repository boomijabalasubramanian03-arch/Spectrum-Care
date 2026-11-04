FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for OpenCV and Tesseract
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Initialize DB tables if missing and start FastAPI server
ENV PORT=8000
EXPOSE 8000
CMD python init_db.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
