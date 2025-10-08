#!/bin/bash
"""
VulnGuard Deployment Script
This script helps deploy and test the VulnGuard MVP components.
"""

set -e

echo "🚀 VulnGuard MVP Deployment Script"
echo "=================================="

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command_exists docker; then
    echo "❌ Docker is required but not installed."
    exit 1
fi

if ! command_exists docker-compose; then
    echo "❌ Docker Compose is required but not installed."
    exit 1
fi

if ! command_exists node; then
    echo "❌ Node.js is required but not installed."
    exit 1
fi

if ! command_exists python3; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

echo "✅ All prerequisites are installed"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p vulnguard/{frontend,backend,ml-service,scan-engine}/{logs,data,reports}

# Build and start services
echo "🐳 Building and starting services..."

# Start ML Service
echo "Starting ML Service..."
cd vulnguard/ml-service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
nohup uvicorn app:app --host 0.0.0.0 --port 8001 > ../logs/ml-service.log 2>&1 &
echo $! > ../ml-service.pid
cd ..

# Start Scan Engine
echo "Starting Scan Engine..."
cd vulnguard/scan-engine
docker-compose up -d
cd ..

# Start Backend API
echo "Starting Backend API..."
cd vulnguard/backend
npm install
nohup npm start > ../logs/backend.log 2>&1 &
echo $! > ../backend.pid
cd ..

# Start Frontend
echo "Starting Frontend..."
cd vulnguard/frontend
npm install
nohup npm run dev > ../logs/frontend.log 2>&1 &
echo $! > ../frontend.pid
cd ..

echo ""
echo "🎉 VulnGuard MVP is now running!"
echo ""
echo "📊 Service Status:"
echo "  • ML Service:     http://localhost:8001"
echo "  • Scan Engine:    http://localhost:8080"
echo "  • Backend API:    http://localhost:3001"
echo "  • Frontend:       http://localhost:3000"
echo ""
echo "📋 Available Endpoints:"
echo "  • Frontend Dashboard: http://localhost:3000"
echo "  • API Health:         http://localhost:3001/health"
echo "  • ML Service Health:  http://localhost:8001/health"
echo "  • ZAP Status:         http://localhost:8080/JSON/core/view/version/"
echo ""
echo "🧪 Quick Test:"
echo "  curl http://localhost:8001/health"
echo "  curl http://localhost:3001/api/status"
echo ""
echo "📁 Logs are available in: vulnguard/logs/"
echo ""
echo "🔧 To stop all services:"
echo "  pkill -F vulnguard/ml-service.pid"
echo "  pkill -F vulnguard/backend.pid"
echo "  pkill -F vulnguard/frontend.pid"
echo "  cd vulnguard/scan-engine && docker-compose down"
echo ""
echo "✅ Deployment complete!"
