#!/usr/bin/env python3
"""
VulnGuard ML Classifier Service
A FastAPI service for classifying HTTP responses for SQL injection vulnerabilities.
"""

import json
import logging
import os
import re
from typing import Dict, List, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="VulnGuard ML Classifier",
    description="ML service for classifying HTTP responses for SQL injection vulnerabilities",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class HTTPResponse(BaseModel):
    url: str
    method: str
    status_code: int
    headers: Dict[str, str]
    body: str
    request_payload: Optional[str] = None

class ClassificationResult(BaseModel):
    url: str
    classification: str  # "HIT", "MISS", "LIKELY"
    confidence: float
    vulnerability_type: str
    explanation: str

class BatchClassificationRequest(BaseModel):
    responses: List[HTTPResponse]

class BatchClassificationResponse(BaseModel):
    results: List[ClassificationResult]
    summary: Dict[str, int]

# Global variables for the ML model
model = None
vectorizer = None
MODEL_PATH = "models/sqli_classifier.joblib"
VECTORIZER_PATH = "models/tfidf_vectorizer.joblib"

# SQL injection patterns and indicators
SQL_INJECTION_PATTERNS = [
    r"SQL syntax.*MySQL|Oracle|PostgreSQL|SQLite",
    r"syntax error.*mysqli?|pdo|mysql",
    r"You have an error in your SQL syntax",
    r"mysql_fetch_row|mysql_fetch_array|pg_query",
    r"SQLite|PostgreSQL|Oracle error",
    r"unclosed quotation mark",
    r"quoted string not properly terminated",
    r"Warning.*mysql",
    r"mysql_num_rows|mysql_query",
    r"pg_execute|pg_prepare",
    r"ORA-\d{5}",  # Oracle error codes
    r"Microsoft OLE DB Provider for SQL Server",
    r"System\.Data\.SqlClient",
    r"Driver.*SQL",
    r"Invalid column name",
    r"Table.*doesn't exist",
    r"Unknown column",
    r"mysql_real_escape_string|addslashes",
    r"near \"|\" at line",
    r"expecting.*EOF|got.*",
]

# Response patterns that indicate normal behavior (not vulnerable)
NORMAL_PATTERNS = [
    r"Welcome|Login|Home|Dashboard",
    r"200 OK|HTTP/1\.[01] 200",
    r"Content-Type.*text/html",
    r"<!DOCTYPE html>",
    r"<html",
    r"window\.location|document\.cookie",
    r"Set-Cookie",
    r"Cache-Control",
    r"Expires",
]

def extract_features(response_body: str, status_code: int, headers: Dict[str, str]) -> Dict[str, any]:
    """Extract features from HTTP response for ML classification"""
    features = {}

    # Basic response characteristics
    features['status_code'] = status_code
    features['body_length'] = len(response_body)
    features['has_error_headers'] = 1 if any(
        header.lower() in ['x-error', 'x-mysql-error', 'x-oracle-error']
        for header in headers.keys()
    ) else 0

    # Text-based features
    body_lower = response_body.lower()

    # SQL error indicators
    sql_error_count = sum(1 for pattern in SQL_INJECTION_PATTERNS if re.search(pattern, body_lower, re.IGNORECASE))
    features['sql_error_count'] = sql_error_count

    # Normal response indicators
    normal_count = sum(1 for pattern in NORMAL_PATTERNS if re.search(pattern, body_lower, re.IGNORECASE))
    features['normal_response_count'] = normal_count

    # Database-specific indicators
    features['has_mysql'] = 1 if 'mysql' in body_lower else 0
    features['has_oracle'] = 1 if 'oracle' in body_lower else 0
    features['has_postgresql'] = 1 if 'postgresql' in body_lower or 'postgres' in body_lower else 0
    features['has_sqlite'] = 1 if 'sqlite' in body_lower else 0

    # Syntax error indicators
    features['has_syntax_error'] = 1 if 'syntax error' in body_lower else 0
    features['has_unclosed_quote'] = 1 if 'unclosed quotation' in body_lower or 'quoted string not properly terminated' in body_lower else 0

    # Response type indicators
    features['is_json'] = 1 if 'content-type' in [h.lower() for h in headers.keys()] and 'application/json' in headers.get('content-type', '').lower() else 0
    features['is_html'] = 1 if 'content-type' in [h.lower() for h in headers.keys()] and 'text/html' in headers.get('content-type', '').lower() else 0

    # Length-based features
    features['body_too_short'] = 1 if len(response_body) < 100 else 0
    features['body_too_long'] = 1 if len(response_body) > 10000 else 0

    return features

def load_model():
    """Load the trained ML model and vectorizer"""
    global model, vectorizer

    try:
        if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
            logger.info("Loading existing model and vectorizer...")
            model = joblib.load(MODEL_PATH)
            vectorizer = joblib.load(VECTORIZER_PATH)
            logger.info("Model loaded successfully")
            return True
        else:
            logger.info("No existing model found, creating new model...")
            return create_and_train_model()
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return False

def create_and_train_model():
    """Create and train a new ML model for SQL injection detection"""
    global model, vectorizer

    try:
        # Sample training data (in production, use a proper dataset)
        training_data = [
            # Positive examples (SQL injection responses)
            ("You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version", "HIT"),
            ("SQL syntax error near ' OR '1'='1", "HIT"),
            ("mysql_fetch_array() expects parameter 1 to be resource", "HIT"),
            ("ORA-01756: quoted string not properly terminated", "HIT"),
            ("PostgreSQL query failed: ERROR: syntax error at or near", "HIT"),
            ("SQLite error: unrecognized token", "HIT"),
            ("System.Data.SqlClient.SqlException", "HIT"),
            ("Warning: mysql_query(): Access denied for user", "HIT"),
            ("unclosed quotation mark after the character string", "HIT"),

            # Negative examples (normal responses)
            ("Welcome to our website", "MISS"),
            ("Login successful", "MISS"),
            ("200 OK", "MISS"),
            ("<!DOCTYPE html><html><body>Welcome</body></html>", "MISS"),
            ("{\"status\": \"success\", \"data\": []}", "MISS"),
            ("Page not found - 404", "MISS"),
            ("Internal server error", "MISS"),
            ("Access denied", "MISS"),
            ("Please log in to continue", "MISS"),
            ("Thank you for your submission", "MISS"),
        ]

        # Prepare data
        texts, labels = zip(*training_data)
        labels_numeric = [1 if label == "HIT" else 0 for label in labels]

        # Create TF-IDF vectorizer
        vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            stop_words='english',
            lowercase=True
        )

        # Transform text data
        X_text = vectorizer.fit_transform(texts)

        # Create additional features DataFrame
        features_data = []
        for text in texts:
            # Mock HTTP response for feature extraction
            mock_headers = {'content-type': 'text/html'}
            mock_features = extract_features(text, 200, mock_headers)
            features_data.append(list(mock_features.values()))

        X_features = pd.DataFrame(features_data, columns=list(extract_features("", 200, {}).keys()))

        # Combine text and additional features
        X_combined = np.hstack([X_text.toarray(), X_features.values])

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_combined, labels_numeric, test_size=0.2, random_state=42
        )

        # Train model
        model = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            max_depth=10
        )

        model.fit(X_train, y_train)

        # Evaluate model
        y_pred = model.predict(X_test)
        logger.info("Model training completed")
        logger.info(f"Training accuracy: {model.score(X_train, y_train):.3f}")
        logger.info(f"Test accuracy: {model.score(X_test, y_test):.3f}")

        # Save model and vectorizer
        os.makedirs("models", exist_ok=True)
        joblib.dump(model, MODEL_PATH)
        joblib.dump(vectorizer, VECTORIZER_PATH)
        logger.info("Model and vectorizer saved")

        return True

    except Exception as e:
        logger.error(f"Error creating/training model: {e}")
        return False

def classify_response(response: HTTPResponse) -> ClassificationResult:
    """Classify a single HTTP response for SQL injection"""
    try:
        # Extract features
        features = extract_features(response.body, response.status_code, response.headers)

        # Get text features
        text_features = vectorizer.transform([response.body])

        # Combine features
        feature_vector = np.hstack([
            text_features.toarray(),
            np.array(list(features.values())).reshape(1, -1)
        ])

        # Get prediction
        prediction_proba = model.predict_proba(feature_vector)[0]
        prediction = model.predict(feature_vector)[0]

        # Determine classification and confidence
        if prediction == 1:  # HIT
            classification = "HIT"
            confidence = float(prediction_proba[1])
        else:  # MISS
            classification = "MISS"
            confidence = float(prediction_proba[0])

        # Adjust classification based on heuristics
        if features['sql_error_count'] > 0 and confidence > 0.3:
            classification = "HIT"
            confidence = min(confidence + 0.2, 1.0)
        elif features['normal_response_count'] > 2 and confidence < 0.7:
            classification = "MISS"
            confidence = max(confidence - 0.1, 0.1)

        # Generate explanation
        explanation = generate_explanation(features, response, classification, confidence)

        return ClassificationResult(
            url=response.url,
            classification=classification,
            confidence=confidence,
            vulnerability_type="SQL Injection",
            explanation=explanation
        )

    except Exception as e:
        logger.error(f"Error classifying response: {e}")
        return ClassificationResult(
            url=response.url,
            classification="ERROR",
            confidence=0.0,
            vulnerability_type="SQL Injection",
            explanation=f"Classification error: {str(e)}"
        )

def generate_explanation(features: Dict, response: HTTPResponse, classification: str, confidence: float) -> str:
    """Generate a human-readable explanation for the classification"""
    explanations = []

    if classification == "HIT":
        if features['sql_error_count'] > 0:
            explanations.append(f"Found {features['sql_error_count']} SQL error pattern(s)")
        if features['has_mysql'] or features['has_oracle'] or features['has_postgresql']:
            db_types = []
            if features['has_mysql']: db_types.append("MySQL")
            if features['has_oracle']: db_types.append("Oracle")
            if features['has_postgresql']: db_types.append("PostgreSQL")
            explanations.append(f"Database-specific error indicators for: {', '.join(db_types)}")
        if features['has_syntax_error']:
            explanations.append("SQL syntax error detected")
        if response.status_code >= 500:
            explanations.append(f"Server error status code: {response.status_code}")

    elif classification == "MISS":
        if features['normal_response_count'] > 0:
            explanations.append(f"Found {features['normal_response_count']} normal response pattern(s)")
        if features['is_html'] or features['is_json']:
            explanations.append("Response appears to be normal HTML/JSON content")
        if 200 <= response.status_code < 300:
            explanations.append(f"Successful status code: {response.status_code}")

    explanations.append(f"ML confidence score: {confidence:.3f}")

    return "; ".join(explanations) if explanations else "No specific indicators found"

# API endpoints
@app.on_event("startup")
async def startup_event():
    """Initialize the ML model on startup"""
    logger.info("Starting VulnGuard ML Classifier Service...")
    if not load_model():
        logger.error("Failed to load ML model")
        # In production, you might want to exit here
        # sys.exit(1)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "VulnGuard ML Classifier Service", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "model_loaded": model is not None}

@app.post("/classify", response_model=ClassificationResult)
async def classify_single_response(response: HTTPResponse):
    """Classify a single HTTP response"""
    if model is None:
        raise HTTPException(status_code=503, detail="ML model not loaded")

    return classify_response(response)

@app.post("/classify/batch", response_model=BatchClassificationResponse)
async def classify_batch_responses(request: BatchClassificationRequest, background_tasks: BackgroundTasks):
    """Classify multiple HTTP responses"""
    if model is None:
        raise HTTPException(status_code=503, detail="ML model not loaded")

    results = []
    for response in request.responses:
        result = classify_response(response)
        results.append(result)

    # Calculate summary
    summary = {
        "total": len(results),
        "HIT": sum(1 for r in results if r.classification == "HIT"),
        "MISS": sum(1 for r in results if r.classification == "MISS"),
        "LIKELY": sum(1 for r in results if r.classification == "LIKELY"),
        "ERROR": sum(1 for r in results if r.classification == "ERROR")
    }

    return BatchClassificationResponse(results=results, summary=summary)

@app.post("/retrain")
async def retrain_model(background_tasks: BackgroundTasks):
    """Retrain the ML model (background task)"""
    def _retrain():
        logger.info("Starting model retraining...")
        success = create_and_train_model()
        if success:
            logger.info("Model retraining completed successfully")
        else:
            logger.error("Model retraining failed")

    background_tasks.add_task(_retrain)
    return {"message": "Model retraining started in background"}

@app.get("/model/info")
async def model_info():
    """Get information about the current ML model"""
    if model is None:
        return {"error": "No model loaded"}

    return {
        "model_type": type(model).__name__,
        "vectorizer_features": len(vectorizer.get_feature_names_out()) if vectorizer else 0,
        "model_features": len(extract_features("", 200, {}))
    }

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
