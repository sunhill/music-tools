
# Stage 1: Build Frontend
FROM node:20-slim AS frontend-build

# Set working directory
WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy frontend source code
COPY frontend/ .

# Build frontend
RUN npm run build

EXPOSE 3000

CMD ["/bin/bash", "-c", "cd /app/frontend && npm start"]