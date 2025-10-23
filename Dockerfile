# This is a multi-service Dockerfile for Railway deployment
# Railway will use the individual service Dockerfiles instead

# This file exists to prevent Railway from looking for a Dockerfile
# Use the individual service Dockerfiles:
# - backend/Dockerfile for backend service
# - frontend/Dockerfile for frontend service

# For Railway deployment, deploy each service separately:
# 1. Deploy backend service using backend/Dockerfile
# 2. Deploy frontend service using frontend/Dockerfile

FROM alpine:latest
RUN echo "This is a placeholder Dockerfile. Use individual service Dockerfiles for deployment."
CMD ["echo", "Please deploy backend and frontend services separately using their respective Dockerfiles."]
