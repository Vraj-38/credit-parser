# Dockerfile for FastAPI backend (Python)
FROM python:3.10-slim

# System dependencies for OCR and PDF parsing
RUN apt-get update && \
    apt-get install -y tesseract-ocr poppler-utils gcc && \
    rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy backend code
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Expose FastAPI port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
