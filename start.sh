#!/bin/bash

# Exit on error
set -e

# Build frontend
cd frontend
npm ci
npm run build
cd ..

# Copy frontend build to backend
mkdir -p backend/frontend_build
cp -r frontend/build/* backend/frontend_build/

# Install Python dependencies
pip install -r backend/requirements.txt

# Start the FastAPI server
cd backend
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
