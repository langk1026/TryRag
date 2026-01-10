#!/bin/bash

set -e

echo "=========================================="
echo "RAG Application - Docker Setup"
echo "=========================================="
echo ""

if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✓ Docker installed"
echo "✓ Docker Compose installed"
echo ""

if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env file with your credentials:"
    echo "   - SHAREPOINT_SITE_URL"
    echo "   - SHAREPOINT_CLIENT_ID"
    echo "   - SHAREPOINT_CLIENT_SECRET"
    echo "   - SHAREPOINT_TENANT_ID"
    echo "   - GOOGLE_API_KEY"
    echo ""
    read -p "Press Enter after configuring .env file..."
fi

echo "Checking .env configuration..."

if grep -q "your_client_id" .env || grep -q "your_google_api_key" .env; then
    echo "❌ Error: .env file contains placeholder values"
    echo "Please configure .env with actual credentials"
    exit 1
fi

echo "✓ Environment configuration looks valid"
echo ""

echo "Building Docker images..."
docker-compose build

echo ""
echo "Starting services..."
docker-compose up -d

echo ""
echo "Waiting for services to start..."
sleep 5

echo ""
echo "Checking service health..."

if curl -s http://localhost:8000/api/v1/health > /dev/null; then
    echo "✓ Backend is healthy"
else
    echo "⚠️  Backend health check failed"
    echo "Check logs: docker-compose logs backend"
fi

if curl -s http://localhost:3000 > /dev/null; then
    echo "✓ Frontend is accessible"
else
    echo "⚠️  Frontend is not accessible"
    echo "Check logs: docker-compose logs frontend"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Services:"
echo "  Frontend:  http://localhost:3000"
echo "  API Docs:  http://localhost:8000/docs"
echo "  Health:    http://localhost:8000/api/v1/health"
echo ""
echo "Useful commands:"
echo "  View logs:        docker-compose logs -f"
echo "  View backend logs: docker-compose logs -f backend"
echo "  View cron logs:   docker-compose logs -f cron"
echo "  Restart services: docker-compose restart"
echo "  Stop services:    docker-compose stop"
echo "  Remove all:       docker-compose down -v"
echo ""
echo "Next steps:"
echo "1. Visit http://localhost:3000 to use the application"
echo "2. Wait for initial indexing to complete (check logs)"
echo "3. Try asking questions about your documents"
echo ""
echo "Configuration:"
echo "  HyDE enabled: $(grep HYDE_ENABLED .env | cut -d'=' -f2)"
echo "  Chunk size: $(grep CHUNK_SIZE .env | cut -d'=' -f2)"
echo "  Index interval: $(grep INDEX_SCHEDULE_MINUTES .env | cut -d'=' -f2) minutes"
echo ""
