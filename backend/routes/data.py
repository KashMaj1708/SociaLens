from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from datetime import datetime
import json

from schemas.models import DataFilter, SocialMediaPost
from services.database import get_database, POSTS_COLLECTION

router = APIRouter()

@router.get("/", response_model=List[SocialMediaPost])
async def get_posts(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment"),
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    language: Optional[str] = Query(None, description="Filter by language"),
    has_media: Optional[bool] = Query(None, description="Filter by media presence"),
    search_text: Optional[str] = Query(None, description="Search in text content"),
    limit: int = Query(50, description="Number of posts to return"),
    skip: int = Query(0, description="Number of posts to skip")
):
    """Get social media posts with optional filtering"""
    
    # Build filter query
    filter_query = {}
    
    if platform:
        filter_query["platform"] = platform
    
    if sentiment:
        filter_query["sentiment"] = sentiment
    
    if language:
        filter_query["language"] = language
    
    if has_media is not None:
        if has_media:
            filter_query["media"] = {"$ne": []}
        else:
            filter_query["media"] = []
    
    # Date range filter
    if date_from or date_to:
        date_filter = {}
        if date_from:
            try:
                date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
                date_filter["$gte"] = date_from_dt
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_from format")
        
        if date_to:
            try:
                date_to_dt = datetime.strptime(date_to, "%Y-%m-%d")
                date_filter["$lte"] = date_to_dt
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_to format")
        
        filter_query["timestamp"] = date_filter
    
    # Text search
    if search_text:
        filter_query["$or"] = [
            {"raw_text": {"$regex": search_text, "$options": "i"}},
            {"cleaned_text": {"$regex": search_text, "$options": "i"}}
        ]
    
    # Get posts from database
    db = await get_database()
    cursor = db[POSTS_COLLECTION].find(
        filter_query,
        {"_id": 0}  # Exclude MongoDB _id field
    ).skip(skip).limit(limit).sort("timestamp", -1)
    
    posts = await cursor.to_list(length=limit)
    
    return posts

@router.get("/{post_id}", response_model=SocialMediaPost)
async def get_post(post_id: str):
    """Get a specific post by ID"""
    
    db = await get_database()
    post = await db[POSTS_COLLECTION].find_one(
        {"post_id": post_id},
        {"_id": 0}
    )
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return post

@router.get("/stats/overview")
async def get_stats():
    """Get overview statistics"""
    
    db = await get_database()
    
    # Total posts
    total_posts = await db[POSTS_COLLECTION].count_documents({})
    
    # Posts by platform
    platform_stats = await db[POSTS_COLLECTION].aggregate([
        {"$group": {"_id": "$platform", "count": {"$sum": 1}}}
    ]).to_list(None)
    
    # Posts by sentiment
    sentiment_stats = await db[POSTS_COLLECTION].aggregate([
        {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}}
    ]).to_list(None)
    
    # Posts by language
    language_stats = await db[POSTS_COLLECTION].aggregate([
        {"$group": {"_id": "$language", "count": {"$sum": 1}}}
    ]).to_list(None)
    
    # Posts with media
    posts_with_media = await db[POSTS_COLLECTION].count_documents({"media": {"$ne": []}})
    
    return {
        "total_posts": total_posts,
        "platforms": {stat["_id"]: stat["count"] for stat in platform_stats},
        "sentiments": {stat["_id"]: stat["count"] for stat in sentiment_stats if stat["_id"]},
        "languages": {stat["_id"]: stat["count"] for stat in language_stats if stat["_id"]},
        "posts_with_media": posts_with_media
    }

@router.put("/{post_id}")
async def update_post(post_id: str, post_data: dict):
    """Update a specific post"""
    
    db = await get_database()
    
    # Remove _id if present
    if "_id" in post_data:
        del post_data["_id"]
    
    result = await db[POSTS_COLLECTION].update_one(
        {"post_id": post_id},
        {"$set": post_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return {"message": "Post updated successfully"}

@router.delete("/{post_id}")
async def delete_post(post_id: str):
    """Delete a specific post"""
    
    db = await get_database()
    
    result = await db[POSTS_COLLECTION].delete_one({"post_id": post_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return {"message": "Post deleted successfully"} 