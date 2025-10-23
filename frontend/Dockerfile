# Dockerfile for React frontend
FROM node:18-alpine as build

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm install

COPY . ./
RUN npm run build

# Serve with nginx
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
