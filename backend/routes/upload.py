from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import json
import csv
import zipfile
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import aiofiles

from schemas.models import UploadResponse, SocialMediaPost, PlatformType
from services.database import get_database, POSTS_COLLECTION, UPLOADS_COLLECTION
from workers.tasks import process_upload_task

router = APIRouter()

@router.post("/", response_model=UploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload and process social media data files"""
    
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    allowed_extensions = {'.json', '.csv', '.zip'}
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Generate unique file ID
    file_id = str(uuid.uuid4())
    upload_dir = f"uploads/{file_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save uploaded file
    file_path = os.path.join(upload_dir, file.filename)
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Parse and validate data
    posts = []
    try:
        if file_extension == '.json':
            posts = await parse_json_file(file_path)
        elif file_extension == '.csv':
            posts = await parse_csv_file(file_path)
        elif file_extension == '.zip':
            posts = await parse_zip_file(file_path, upload_dir)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing file: {str(e)}")
    
    # Save upload metadata
    db = await get_database()
    upload_metadata = {
        "file_id": file_id,
        "filename": file.filename,
        "upload_time": datetime.utcnow(),
        "total_posts": len(posts),
        "status": "uploaded",
        "file_path": file_path
    }
    
    await db[UPLOADS_COLLECTION].insert_one(upload_metadata)
    
    # Save raw posts to database
    if posts:
        await db[POSTS_COLLECTION].insert_many(posts)
    
    # Start background processing
    background_tasks.add_task(process_upload_task, file_id, posts)
    
    return UploadResponse(
        message="File uploaded successfully",
        file_id=file_id,
        total_posts=len(posts),
        processing_status="processing"
    )

async def parse_json_file(file_path: str) -> List[Dict[str, Any]]:
    """Parse JSON file containing social media posts"""
    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
        content = await f.read()
        data = json.loads(content)
    
    print(f"Parsed JSON data type: {type(data)}")
    print(f"Data length: {len(data) if isinstance(data, list) else 'Not a list'}")
    
    posts = []
    if isinstance(data, list):
        posts = data
    elif isinstance(data, dict) and 'posts' in data:
        posts = data['posts']
    else:
        raise ValueError("Invalid JSON structure")
    
    print(f"Found {len(posts)} posts before normalization")
    
    # Validate and normalize posts
    normalized_posts = []
    for i, post in enumerate(posts):
        print(f"Processing post {i+1}: {post.get('post_id', 'no_id')} - {post.get('raw_text', 'no_text')[:50]}...")
        normalized_post = normalize_post_data(post)
        if normalized_post:
            normalized_posts.append(normalized_post)
        else:
            print(f"Post {i+1} was rejected during normalization")
    
    print(f"Successfully normalized {len(normalized_posts)} posts")
    return normalized_posts

async def parse_csv_file(file_path: str) -> List[Dict[str, Any]]:
    """Parse CSV file containing social media posts"""
    posts = []
    
    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
        content = await f.read()
        lines = content.split('\n')
        
        if not lines:
            return posts
        
        # Parse header
        reader = csv.DictReader(lines)
        
        for row in reader:
            normalized_post = normalize_post_data(row)
            if normalized_post:
                posts.append(normalized_post)
    
    return posts

async def parse_zip_file(file_path: str, extract_dir: str) -> List[Dict[str, Any]]:
    """Parse ZIP file containing data and media files"""
    posts = []
    
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    # Look for data files in extracted directory
    for root, dirs, files in os.walk(extract_dir):
        for file in files:
            if file.endswith('.json'):
                json_path = os.path.join(root, file)
                json_posts = await parse_json_file(json_path)
                posts.extend(json_posts)
            elif file.endswith('.csv'):
                csv_path = os.path.join(root, file)
                csv_posts = await parse_csv_file(csv_path)
                posts.extend(csv_posts)
    
    return posts

def normalize_post_data(post: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Normalize post data to standard format"""
    try:
        # Extract common fields with better fallback logic
        post_id = post.get("post_id") or post.get("id") or str(uuid.uuid4())
        raw_text = post.get("raw_text") or post.get("text") or post.get("content") or post.get("message") or ""
        
        # If no text content, try to create a summary from other fields
        if not raw_text:
            # Try to extract meaningful content from other fields
            summary_parts = []
            if post.get("title"):
                summary_parts.append(post.get("title"))
            if post.get("description"):
                summary_parts.append(post.get("description"))
            if post.get("caption"):
                summary_parts.append(post.get("caption"))
            
            if summary_parts:
                raw_text = " | ".join(summary_parts)
            else:
                # If still no text, create a minimal description
                raw_text = f"Post from {post.get('platform', 'unknown')} platform"
        
        normalized = {
            "platform": post.get("platform", "unknown"),
            "post_id": str(post_id),
            "raw_text": raw_text,
            "timestamp": parse_timestamp(post.get("timestamp", post.get("created_at", post.get("date", "")))),
            "user_id": str(post.get("user_id", post.get("author", post.get("username", "")))),
            "media": parse_media(post.get("media", post.get("images", post.get("videos", [])))),
            "metadata": {k: v for k, v in post.items() if k not in ["platform", "id", "post_id", "text", "content", "message", "timestamp", "created_at", "date", "user_id", "author", "username", "media", "images", "videos", "raw_text"]}
        }
        
        # Only reject if we have absolutely no content
        if not normalized["raw_text"].strip():
            print(f"Rejecting post with no text content: {post}")
            return None
        
        return normalized
        
    except Exception as e:
        print(f"Error normalizing post: {e}")
        print(f"Post data: {post}")
        return None

def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse timestamp string to datetime object"""
    if not timestamp_str:
        return datetime.utcnow()
    
    # Common timestamp formats
    formats = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue
    
    return datetime.utcnow()

def parse_media(media_data: Any) -> List[Dict[str, Any]]:
    """Parse media data to standard format"""
    if not media_data:
        return []
    
    media_list = []
    
    if isinstance(media_data, list):
        for item in media_data:
            if isinstance(item, dict):
                media_item = {
                    "type": item.get("type", "image"),
                    "url": item.get("url", item.get("src", "")),
                    "filename": item.get("filename", "")
                }
                media_list.append(media_item)
            elif isinstance(item, str):
                media_list.append({
                    "type": "image",
                    "url": item,
                    "filename": ""
                })
    elif isinstance(media_data, str):
        media_list.append({
            "type": "image",
            "url": media_data,
            "filename": ""
        })
    
    return media_list 