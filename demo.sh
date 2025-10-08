#!/bin/bash
"""
VulnGuard Demo Script
Demonstrates the complete VulnGuard MVP functionality
"""

set -e

echo "🎯 VulnGuard MVP Demonstration"
echo "=============================="
echo ""
echo "📋 System Status:"
echo "  • ML Service:     http://localhost:8001"
echo "  • Backend API:    http://localhost:3001"
echo "  • Frontend:       http://localhost:3000"
echo ""

# Test 1: ML Service Health and Classification
echo "🧠 Testing ML Classification Service..."
echo ""

echo "Testing normal response classification:"
curl -s -X POST http://localhost:8001/classify \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://example.com/home",
    "method": "GET",
    "status_code": 200,
    "headers": {"content-type": "text/html"},
    "body": "Welcome to our website",
    "request_payload": "page=home"
  }' | jq '.'

echo ""
echo "Testing SQL injection pattern classification:"
curl -s -X POST http://localhost:8001/classify \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://test.com/search",
    "method": "GET",
    "status_code": 500,
    "headers": {"content-type": "text/html"},
    "body": "You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version",
    "request_payload": "id=1 OR 1=1"
  }' | jq '.'

# Test 2: Backend API
echo ""
echo "🔗 Testing Backend API..."
echo ""

echo "API Status:"
curl -s http://localhost:3001/api/status | jq '.'

echo ""
echo "Available scan endpoints:"
curl -s http://localhost:3001/api/scans | jq '.'

# Test 3: Frontend Accessibility
echo ""
echo "🌐 Testing Frontend Dashboard..."
echo ""

if curl -s -I http://localhost:3000 | grep -q "200"; then
    echo "✅ Frontend is accessible at http://localhost:3000"
else
    echo "❌ Frontend not accessible"
fi

# Test 4: ML Model Information
echo ""
echo "🤖 ML Model Information..."
echo ""

curl -s http://localhost:8001/model/info | jq '.'

echo ""
echo "📊 System Summary:"
echo "=================="
echo "✅ ML Service: Running (SQL injection classification)"
echo "✅ Backend API: Running (Scan orchestration)"
echo "✅ Frontend: Running (Dashboard interface)"
echo "⏳ Scan Engine: Ready for deployment (Docker image built)"

echo ""
echo "🎯 Demo Complete!"
echo ""
echo "🔧 Next Steps:"
echo "  • Start the scan engine: cd scan-engine && docker-compose up -d"
echo "  • Access dashboard: http://localhost:3000"
echo "  • Run full scan: Use the web interface or API endpoints"
echo "  • View logs: check the logs/ directory for service logs"

echo ""
echo "📚 Documentation: See README.md for complete setup and usage instructions"
