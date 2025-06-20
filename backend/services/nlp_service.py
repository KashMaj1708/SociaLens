import re
import spacy
from langdetect import detect, LangDetectException
from transformers import pipeline
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NLPService:
    def __init__(self):
        """Initialize NLP models and pipelines"""
        self.nlp = None
        self.sentiment_analyzer = None
        self._initialized = False
    
    def _initialize_models(self):
        """Lazy load models only when needed"""
        if self._initialized:
            return
            
        try:
            # Load spaCy model for NER
            self.nlp = spacy.load("en_core_web_sm")
            
            # Initialize sentiment analysis pipeline with updated API
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                top_k=None  # Use top_k instead of return_all_scores
            )
            
            self._initialized = True
            logger.info("NLP models loaded successfully")
            
        except OSError:
            logger.warning("spaCy model not found. Installing...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
            self._initialized = True
        except Exception as e:
            logger.error(f"Error loading NLP models: {e}")
            # Create fallback services
            self._create_fallback_services()
    
    def _create_fallback_services(self):
        """Create simple fallback services if ML models fail to load"""
        logger.info("Using fallback NLP services")
        self._initialized = True
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove mentions (@username)
        text = re.sub(r'@\w+', '', text)
        
        # Remove hashtags but keep the text
        text = re.sub(r'#(\w+)', r'\1', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove emojis (basic approach)
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        text = emoji_pattern.sub(r'', text)
        
        return text.strip()
    
    def detect_language(self, text: str) -> Optional[str]:
        """Detect language of the text"""
        try:
            return detect(text)
        except LangDetectException:
            return None
    
    def extract_entities(self, text: str) -> List[str]:
        """Extract named entities from text"""
        if not text:
            return []
        
        try:
            self._initialize_models()
            if not self.nlp:
                return []
            
            doc = self.nlp(text)
            entities = []
            
            for ent in doc.ents:
                if ent.label_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT', 'EVENT']:
                    entities.append(ent.text)
            
            return list(set(entities))  # Remove duplicates
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return []
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of the text"""
        if not text:
            return {"sentiment": "neutral", "confidence": 0.0}
        
        try:
            self._initialize_models()
            if not self.sentiment_analyzer:
                return {"sentiment": "neutral", "confidence": 0.0}
            
            results = self.sentiment_analyzer(text)
            
            # Get the highest scoring sentiment
            best_result = max(results[0], key=lambda x: x['score'])
            
            # Map to our sentiment types
            sentiment_map = {
                'POSITIVE': 'positive',
                'NEGATIVE': 'negative'
            }
            
            return {
                "sentiment": sentiment_map.get(best_result['label'], 'neutral'),
                "confidence": best_result['score']
            }
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return {"sentiment": "neutral", "confidence": 0.0}
    
    def process_text(self, text: str) -> Dict[str, Any]:
        """Complete text processing pipeline"""
        cleaned_text = self.clean_text(text)
        language = self.detect_language(cleaned_text)
        entities = self.extract_entities(cleaned_text)
        sentiment_result = self.analyze_sentiment(cleaned_text)
        
        return {
            "cleaned_text": cleaned_text,
            "language": language,
            "entities": entities,
            "sentiment": sentiment_result["sentiment"],
            "sentiment_confidence": sentiment_result["confidence"]
        }

# Global NLP service instance
nlp_service = NLPService() 