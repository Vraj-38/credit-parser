# ---------- Build frontend ----------
FROM node:18-alpine as frontend
WORKDIR /app
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm ci
COPY frontend ./frontend
RUN cd frontend && npm run build

# ---------- Backend image ----------
FROM python:3.9-slim
WORKDIR /app

# System deps for pdf2image (poppler) and tesseract
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils tesseract-ocr \
  && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Copy built frontend into a public dir to be served by FastAPI
COPY --from=frontend /app/frontend/build /app/frontend_build

# Environment
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

# Expose port for Railway to detect
EXPOSE 8000

# Start server (FastAPI will read PORT env)
CMD ["bash", "-lc", "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
