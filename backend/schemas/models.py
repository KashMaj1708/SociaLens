from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class PlatformType(str, Enum):
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"

class SentimentType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"

class MediaItem(BaseModel):
    type: MediaType
    url: str
    tags: List[str] = []
    caption: Optional[str] = None
    filename: Optional[str] = None

class SocialMediaPost(BaseModel):
    platform: PlatformType
    post_id: str
    raw_text: str
    cleaned_text: Optional[str] = None
    language: Optional[str] = None
    timestamp: datetime
    user_id: str
    media: List[MediaItem] = []
    sentiment: Optional[SentimentType] = None
    entities: List[str] = []
    similarity_score: Optional[float] = None
    metadata: Dict[str, Any] = {}

class UploadResponse(BaseModel):
    message: str
    file_id: str
    total_posts: int
    processing_status: str

class DataFilter(BaseModel):
    platform: Optional[PlatformType] = None
    sentiment: Optional[SentimentType] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    language: Optional[str] = None
    has_media: Optional[bool] = None
    search_text: Optional[str] = None

class ExportRequest(BaseModel):
    format: str = Field(..., pattern="^(csv|json)$")
    filters: Optional[DataFilter] = None
    fields: Optional[List[str]] = None

class AnalyticsResponse(BaseModel):
    total_posts: int
    platforms: Dict[str, int]
    sentiments: Dict[str, int]
    languages: Dict[str, int]
    media_types: Dict[str, int]
    top_entities: List[Dict[str, Any]]
    top_tags: List[Dict[str, Any]]
    daily_posts: List[Dict[str, Any]] 