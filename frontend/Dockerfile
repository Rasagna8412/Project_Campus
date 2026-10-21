# ==============================================================================
# Project Campus — Production Frontend Container
# Multi-stage Node 20 build -> Nginx Alpine static web server
# ==============================================================================

# --- Stage 1: Build Frontend Assets ---
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency manifests
COPY package.json package-lock.json ./

# Reproducible installation using npm ci
RUN npm ci

# Copy application source code
COPY . .

# Build production assets (runs tsc && vite build)
RUN npm run build

# --- Stage 2: Minimal Static Runtime Server ---
FROM nginx:alpine AS runner

# Remove default Nginx welcome page
RUN rm -rf /usr/share/nginx/html/*

# Copy compiled static assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration with reverse proxy and SPA routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Health check verifying local HTTP responses from Nginx
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://127.0.0.1/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
