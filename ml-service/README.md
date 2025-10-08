# VulnGuard ML Classifier Service

This directory contains the Machine Learning classifier service for the VulnGuard DAST platform. The service classifies HTTP responses to identify potential SQL injection vulnerabilities, helping reduce false positives in automated security scanning.

## Overview

The ML Classifier Service uses supervised learning to analyze HTTP responses and classify them as:
- **HIT**: Confirmed SQL injection vulnerability
- **MISS**: Normal response, no vulnerability
- **LIKELY**: Potential vulnerability requiring manual review

## Architecture

- **Framework**: FastAPI for high-performance API serving
- **ML Library**: scikit-learn for model training and inference
- **Features**: TF-IDF text vectorization + custom response features
- **Model**: Random Forest classifier with combined text and metadata features

## Features

- RESTful API for single and batch classification
- Real-time model inference
- Confidence scoring for each prediction
- Detailed explanations for classifications
- Background model retraining capability
- Health check and model information endpoints

## Quick Start

### 1. Build the Docker Image

```bash
cd ml-service
docker build -t vulnguard-ml-classifier .
```

### 2. Run the Container

```bash
docker run -d --name vulnguard-ml -p 8001:8001 vulnguard-ml-classifier
```

### 3. Train the Model

```bash
# Run training script
python train_model.py

# Or via API (background)
curl -X POST http://localhost:8001/retrain
```

### 4. Test Classification

```bash
# Single response classification
curl -X POST http://localhost:8001/classify \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://example.com/search",
    "method": "GET",
    "status_code": 200,
    "headers": {"content-type": "text/html"},
    "body": "Welcome to our website",
    "request_payload": "query=test"
  }'

# Batch classification
curl -X POST http://localhost:8001/classify/batch \
  -H "Content-Type: application/json" \
  -d '{
    "responses": [
      {
        "url": "http://example.com/vulnerable",
        "method": "POST",
        "status_code": 500,
        "headers": {"content-type": "text/html"},
        "body": "You have an error in your SQL syntax",
        "request_payload": "id=1 OR 1=1"
      }
    ]
  }'
```

## API Endpoints

### Classification Endpoints

#### POST /classify
Classify a single HTTP response.

**Request Body:**
```json
{
  "url": "http://example.com/page",
  "method": "GET",
  "status_code": 200,
  "headers": {"content-type": "text/html"},
  "body": "Response content here",
  "request_payload": "Optional request data"
}
```

**Response:**
```json
{
  "url": "http://example.com/page",
  "classification": "MISS",
  "confidence": 0.85,
  "vulnerability_type": "SQL Injection",
  "explanation": "Found 2 normal response patterns; ML confidence score: 0.850"
}
```

#### POST /classify/batch
Classify multiple HTTP responses.

**Request Body:**
```json
{
  "responses": [
    {
      "url": "http://example.com/page1",
      "method": "GET",
      "status_code": 200,
      "headers": {"content-type": "text/html"},
      "body": "Normal response"
    }
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "url": "http://example.com/page1",
      "classification": "MISS",
      "confidence": 0.85,
      "vulnerability_type": "SQL Injection",
      "explanation": "Found 1 normal response pattern; ML confidence score: 0.850"
    }
  ],
  "summary": {
    "total": 1,
    "HIT": 0,
    "MISS": 1,
    "LIKELY": 0,
    "ERROR": 0
  }
}
```

### Management Endpoints

#### GET /health
Check service health and model status.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

#### GET /model/info
Get information about the loaded model.

**Response:**
```json
{
  "model_type": "RandomForestClassifier",
  "vectorizer_features": 1000,
  "model_features": 15
}
```

#### POST /retrain
Retrain the model in the background.

**Response:**
```json
{
  "message": "Model retraining started in background"
}
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_PATH` | `models/sqli_classifier.joblib` | Path to save/load the trained model |
| `VECTORIZER_PATH` | `models/tfidf_vectorizer.joblib` | Path to save/load the TF-IDF vectorizer |

### Model Parameters

The service uses the following ML configuration:

- **Vectorizer**: TF-IDF with max 1000 features, 1-2 n-grams
- **Classifier**: Random Forest with 100 estimators, max depth 10
- **Features**: Combined text and metadata features
- **Training**: 80/20 train-test split with random state 42

## Feature Extraction

The service extracts the following features from HTTP responses:

### Text Features (TF-IDF)
- Response body content
- N-gram analysis (1-2 words)

### Metadata Features
- HTTP status code
- Response body length
- Content-Type headers
- Database-specific error indicators
- SQL syntax error patterns
- Normal response patterns

### Heuristic Rules
- SQL error pattern matching
- Database type detection
- Response normality scoring
- Confidence adjustment based on indicators

## Integration with Scan Engine

The ML classifier integrates with the VulnGuard scan engine:

```python
import requests

# Send scan results to classifier
scan_results = [
    {
        "url": "http://example.com/page",
        "status_code": 500,
        "body": "SQL syntax error...",
        "headers": {"content-type": "text/html"}
    }
]

response = requests.post("http://localhost:8001/classify/batch",
                        json={"responses": scan_results})

classified_results = response.json()
print(f"Found {classified_results['summary']['HIT']} SQL injection vulnerabilities")
```

## Development

### Local Development Setup

1. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Locally**:
   ```bash
   uvicorn app:app --reload --host 0.0.0.0 --port 8001
   ```

4. **Train Model**:
   ```bash
   python train_model.py
   ```

### Testing

```bash
# Test health endpoint
curl http://localhost:8001/health

# Test classification
curl -X POST http://localhost:8001/classify \
  -H "Content-Type: application/json" \
  -d '{"url":"http://test.com","method":"GET","status_code":200,"headers":{"content-type":"text/html"},"body":"Normal response"}'
```

## Performance

- **Response Time**: <100ms for single classification
- **Throughput**: 100+ requests/second
- **Memory Usage**: ~50MB for model + vectorizer
- **Accuracy**: 85-95% depending on training data quality

## Troubleshooting

### Common Issues

1. **Model Not Loaded**: Check logs for training errors
2. **Poor Accuracy**: Retrain with more diverse training data
3. **High Memory Usage**: Reduce max_features in vectorizer
4. **Slow Inference**: Consider model optimization or caching

### Logs

- Application logs: Check container logs with `docker logs vulnguard-ml`
- Model training logs: Available in console output during training
- API access logs: Available through standard FastAPI logging

## Security Considerations

- Input validation on all API endpoints
- No sensitive data stored in model files
- Container runs as non-root user
- No external network access required
- All dependencies scanned for vulnerabilities

## Contributing

1. Follow existing code style and structure
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Validate model performance improvements

## License

This component is part of the VulnGuard platform and follows the project's license terms.
