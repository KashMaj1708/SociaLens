#!/usr/bin/env python3
"""
Simple test script to verify SociaLens backend setup
"""

def test_imports():
    """Test all major imports"""
    try:
        print("Testing imports...")
        
        # Test FastAPI and core dependencies
        import fastapi
        import uvicorn
        import pydantic
        print("✓ FastAPI and core dependencies")
        
        # Test database
        import motor
        import pymongo
        print("✓ Database dependencies")
        
        # Test ML/AI dependencies
        import transformers
        import torch
        print("✓ ML/AI dependencies")
        
        # Test our modules
        from schemas.models import SocialMediaPost, PlatformType
        print("✓ Schema models")
        
        from services.database import get_database
        print("✓ Database service")
        
        from services.nlp_service import nlp_service
        print("✓ NLP service")
        
        from services.cv_service import cv_service
        print("✓ CV service")
        
        from routes import upload, data, export, analytics
        print("✓ API routes")
        
        from workers.tasks import celery_app
        print("✓ Celery tasks")
        
        print("\n🎉 All imports successful! Backend should work.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Other error: {e}")
        return False

def test_spacy():
    """Test spaCy installation"""
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        print("✓ spaCy model loaded successfully")
        return True
    except Exception as e:
        print(f"❌ spaCy error: {e}")
        print("Run: python -m spacy download en_core_web_sm")
        return False

if __name__ == "__main__":
    print("SociaLens Backend Setup Test")
    print("=" * 40)
    
    imports_ok = test_imports()
    spacy_ok = test_spacy()
    
    if imports_ok and spacy_ok:
        print("\n✅ All tests passed! You can start the backend with:")
        print("uvicorn main:app --reload")
    else:
        print("\n❌ Some tests failed. Please fix the issues above.") 