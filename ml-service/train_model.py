#!/usr/bin/env python3
"""
Model training script for VulnGuard ML Classifier
"""

import os
import sys
import logging
from app import create_and_train_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Train the ML model"""
    print("VulnGuard ML Classifier - Model Training")
    print("=" * 50)

    success = create_and_train_model()

    if success:
        print("\n✅ Model training completed successfully!")
        print(f"Model saved to: models/sqli_classifier.joblib")
        print(f"Vectorizer saved to: models/tfidf_vectorizer.joblib")
        return 0
    else:
        print("\n❌ Model training failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
