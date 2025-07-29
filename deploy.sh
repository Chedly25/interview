#!/bin/bash

# Automotive Assistant Deployment Script
# Usage: ./deploy.sh [environment]
# Examples: ./deploy.sh production, ./deploy.sh staging

set -e

ENVIRONMENT=${1:-production}
PROJECT_NAME="automotive-assistant"

echo "🚗 Deploying Automotive Assistant to $ENVIRONMENT environment..."

# Check if required files exist
if [ ! -f ".env.$ENVIRONMENT" ]; then
    echo "❌ Environment file .env.$ENVIRONMENT not found!"
    echo "📝 Please create it based on .env.example"
    exit 1
fi

# Load environment variables
export $(cat .env.$ENVIRONMENT | xargs)

# Validate required environment variables
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ ANTHROPIC_API_KEY is required!"
    exit 1
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -p $PROJECT_NAME down

# Pull latest images and rebuild
echo "🔄 Building and starting containers..."
if [ "$ENVIRONMENT" = "production" ]; then
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml -p $PROJECT_NAME up -d --build
else
    docker-compose -p $PROJECT_NAME up -d --build
fi

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check health
echo "🏥 Checking service health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    docker-compose -p $PROJECT_NAME logs backend
    exit 1
fi

if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is accessible"
else
    echo "❌ Frontend is not accessible"
    docker-compose -p $PROJECT_NAME logs frontend
    exit 1
fi

# Run database migrations (create tables)
echo "🗃️ Setting up database..."
docker-compose -p $PROJECT_NAME exec backend python -c "from database import create_tables; create_tables()"

# Optionally populate with sample data (only for development)
if [ "$ENVIRONMENT" != "production" ]; then
    echo "📊 Adding sample data..."
    docker-compose -p $PROJECT_NAME exec backend python sample_data.py
fi

# Set up scraper cron job for production
if [ "$ENVIRONMENT" = "production" ]; then
    echo "⏰ Setting up scraper cron job..."
    (crontab -l 2>/dev/null; echo "*/30 * * * * cd $(pwd) && docker-compose -p $PROJECT_NAME --profile scraper run --rm scraper") | crontab -
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📍 Access your application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "🔧 Useful commands:"
echo "   View logs:    docker-compose -p $PROJECT_NAME logs -f"
echo "   Stop:         docker-compose -p $PROJECT_NAME down"
echo "   Run scraper:  docker-compose -p $PROJECT_NAME --profile scraper run scraper"
echo ""