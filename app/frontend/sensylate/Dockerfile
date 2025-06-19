# Multi-stage Dockerfile for React application

# Development stage
FROM node:18-alpine as development

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Default command for development
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# Build stage
FROM node:18-alpine as build

# Build arguments
ARG BUILD_DATE
ARG VERSION
ARG VITE_API_URL=/api
ARG VITE_GRAPHQL_URL=/graphql
ARG VITE_USE_GRAPHQL=true

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies for build
RUN npm ci

# Copy source code
COPY . .

# Set build-time environment variables
ENV VITE_API_URL=$VITE_API_URL \
    VITE_GRAPHQL_URL=$VITE_GRAPHQL_URL \
    VITE_USE_GRAPHQL=$VITE_USE_GRAPHQL \
    NODE_ENV=production

# Build application with production optimizations
RUN npm run build:pwa

# Production stage
FROM nginx:alpine as production

# Build arguments
ARG BUILD_DATE
ARG VERSION

# Labels
LABEL maintainer="trading-app"
LABEL version="${VERSION}"
LABEL build-date="${BUILD_DATE}"

# Install curl for health checks
RUN apk add --no-cache curl

# Create nginx user and directories
RUN adduser -D -s /bin/false nginx-user && \
    mkdir -p /var/cache/nginx /var/log/nginx && \
    chown -R nginx-user:nginx-user /var/cache/nginx /var/log/nginx /etc/nginx

# Copy built application
COPY --from=build --chown=nginx-user:nginx-user /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY --chown=nginx-user:nginx-user nginx.conf /etc/nginx/nginx.conf

# Copy security headers configuration
COPY --chown=nginx-user:nginx-user nginx-security.conf /etc/nginx/conf.d/security.conf

# Create health check endpoint
RUN echo "OK" > /usr/share/nginx/html/health

# Switch to non-root user
USER nginx-user

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
