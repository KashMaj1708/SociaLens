import os
import asyncio
from celery import Celery
from typing import List, Dict, Any
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Celery configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery(
    "socialens",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Reduce memory usage
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=100,
)

@celery_app.task
def process_upload_task(file_id: str, posts: List[Dict[str, Any]]):
    """Background task to process uploaded social media data"""
    try:
        logger.info(f"Starting processing for file {file_id} with {len(posts)} posts")
        
        # Import services only when needed to reduce memory usage
        from services.database import get_sync_database, POSTS_COLLECTION
        
        db = get_sync_database()
        processed_count = 0
        
        for post in posts:
            try:
                # Process text with NLP (lazy loading)
                text_result = process_text_simple(post.get("raw_text", ""))
                
                # Update post with NLP results
                post.update({
                    "cleaned_text": text_result["cleaned_text"],
                    "language": text_result["language"],
                    "entities": text_result["entities"],
                    "sentiment": text_result["sentiment"],
                    "sentiment_confidence": text_result["sentiment_confidence"]
                })
                
                # Process media files (simplified for now)
                media_items = post.get("media", [])
                processed_media = []
                
                for media_item in media_items:
                    if media_item.get("type") == "image":
                        # Simple media processing without heavy CV models
                        media_item.update({
                            "tags": ["image"],
                            "caption": "Image content",
                            "similarity_score": 0.5
                        })
                    
                    processed_media.append(media_item)
                
                post["media"] = processed_media
                
                # Update post in database
                db[POSTS_COLLECTION].update_one(
                    {"post_id": post["post_id"]},
                    {"$set": post}
                )
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing post {post.get('post_id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Completed processing {processed_count} posts for file {file_id}")
        return {"status": "completed", "processed_count": processed_count}
        
    except Exception as e:
        logger.error(f"Error in process_upload_task for file {file_id}: {e}")
        return {"status": "error", "error": str(e)}

def process_text_simple(text: str) -> Dict[str, Any]:
    """Simple text processing without heavy ML models"""
    import re
    
    # Clean text
    cleaned_text = re.sub(r'http[s]?://\S+', '', text)  # Remove URLs
    cleaned_text = re.sub(r'@\w+', '', cleaned_text)    # Remove mentions
    cleaned_text = re.sub(r'#(\w+)', r'\1', cleaned_text)  # Remove hashtags
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    
    # Simple language detection (English assumed for now)
    language = "en"
    
    # Simple entity extraction (basic keywords)
    entities = []
    keywords = ["tech", "food", "travel", "music", "sport", "news"]
    for keyword in keywords:
        if keyword.lower() in text.lower():
            entities.append(keyword)
    
    # Simple sentiment (basic keyword-based)
    positive_words = ["good", "great", "awesome", "love", "happy", "excellent"]
    negative_words = ["bad", "terrible", "hate", "awful", "sad", "disappointing"]
    
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    if positive_count > negative_count:
        sentiment = "positive"
        confidence = 0.7
    elif negative_count > positive_count:
        sentiment = "negative"
        confidence = 0.7
    else:
        sentiment = "neutral"
        confidence = 0.5
    
    return {
        "cleaned_text": cleaned_text,
        "language": language,
        "entities": entities,
        "sentiment": sentiment,
        "sentiment_confidence": confidence
    }

@celery_app.task
def process_single_post_task(post_id: str):
    """Process a single post with simplified processing"""
    try:
        from services.database import get_sync_database, POSTS_COLLECTION
        
        db = get_sync_database()
        
        # Get post from database
        post = db[POSTS_COLLECTION].find_one({"post_id": post_id})
        if not post:
            return {"status": "error", "error": "Post not found"}
        
        # Process text with simple method
        text_result = process_text_simple(post.get("raw_text", ""))
        post.update({
            "cleaned_text": text_result["cleaned_text"],
            "language": text_result["language"],
            "entities": text_result["entities"],
            "sentiment": text_result["sentiment"],
            "sentiment_confidence": text_result["sentiment_confidence"]
        })
        
        # Update post
        db[POSTS_COLLECTION].update_one(
            {"post_id": post_id},
            {"$set": post}
        )
        
        return {"status": "completed", "post_id": post_id}
        
    except Exception as e:
        logger.error(f"Error processing post {post_id}: {e}")
        return {"status": "error", "error": str(e)} 