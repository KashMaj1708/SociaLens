from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, timedelta

from schemas.models import AnalyticsResponse
from services.database import get_database, POSTS_COLLECTION

router = APIRouter()

@router.get("/dashboard", response_model=AnalyticsResponse)
async def get_dashboard_analytics(
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)")
):
    """Get comprehensive analytics for dashboard"""
    
    # Build date filter
    date_filter = {}
    if date_from:
        try:
            date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
            date_filter["$gte"] = date_from_dt
        except ValueError:
            date_from_dt = None
    
    if date_to:
        try:
            date_to_dt = datetime.strptime(date_to, "%Y-%m-%d")
            date_filter["$lte"] = date_to_dt
        except ValueError:
            date_to_dt = None
    
    filter_query = {}
    if date_filter:
        filter_query["timestamp"] = date_filter
    
    db = await get_database()
    
    # Total posts
    total_posts = await db[POSTS_COLLECTION].count_documents(filter_query)
    
    # Posts by platform
    platform_pipeline = [
        {"$match": filter_query} if filter_query else {"$match": {}},
        {"$group": {"_id": "$platform", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    platform_stats = await db[POSTS_COLLECTION].aggregate(platform_pipeline).to_list(None)
    platforms = {stat["_id"]: stat["count"] for stat in platform_stats}
    
    # Posts by sentiment
    sentiment_pipeline = [
        {"$match": filter_query} if filter_query else {"$match": {}},
        {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    sentiment_stats = await db[POSTS_COLLECTION].aggregate(sentiment_pipeline).to_list(None)
    sentiments = {stat["_id"]: stat["count"] for stat in sentiment_stats if stat["_id"]}
    
    # Posts by language
    language_pipeline = [
        {"$match": filter_query} if filter_query else {"$match": {}},
        {"$group": {"_id": "$language", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    language_stats = await db[POSTS_COLLECTION].aggregate(language_pipeline).to_list(None)
    languages = {stat["_id"]: stat["count"] for stat in language_stats if stat["_id"]}
    
    # Media types
    media_pipeline = [
        {"$match": filter_query} if filter_query else {"$match": {}},
        {"$unwind": "$media"},
        {"$group": {"_id": "$media.type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    media_stats = await db[POSTS_COLLECTION].aggregate(media_pipeline).to_list(None)
    media_types = {stat["_id"]: stat["count"] for stat in media_stats if stat["_id"]}
    
    # Top entities
    entity_pipeline = [
        {"$match": filter_query} if filter_query else {"$match": {}},
        {"$unwind": "$entities"},
        {"$group": {"_id": "$entities", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    entity_stats = await db[POSTS_COLLECTION].aggregate(entity_pipeline).to_list(None)
    top_entities = [{"entity": stat["_id"], "count": stat["count"]} for stat in entity_stats]
    
    # Top tags from media
    tag_pipeline = [
        {"$match": filter_query} if filter_query else {"$match": {}},
        {"$unwind": "$media"},
        {"$unwind": "$media.tags"},
        {"$group": {"_id": "$media.tags", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    tag_stats = await db[POSTS_COLLECTION].aggregate(tag_pipeline).to_list(None)
    top_tags = [{"tag": stat["_id"], "count": stat["count"]} for stat in tag_stats]
    
    # Daily posts trend
    daily_pipeline = [
        {"$match": filter_query} if filter_query else {"$match": {}},
        {
            "$group": {
                "_id": {
                    "year": {"$year": "$timestamp"},
                    "month": {"$month": "$timestamp"},
                    "day": {"$dayOfMonth": "$timestamp"}
                },
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}},
        {"$limit": 30}
    ]
    daily_stats = await db[POSTS_COLLECTION].aggregate(daily_pipeline).to_list(None)
    daily_posts = []
    for stat in daily_stats:
        date_obj = stat["_id"]
        date_str = f"{date_obj['year']}-{date_obj['month']:02d}-{date_obj['day']:02d}"
        daily_posts.append({"date": date_str, "count": stat["count"]})
    
    return AnalyticsResponse(
        total_posts=total_posts,
        platforms=platforms,
        sentiments=sentiments,
        languages=languages,
        media_types=media_types,
        top_entities=top_entities,
        top_tags=top_tags,
        daily_posts=daily_posts
    )

@router.get("/trends/sentiment")
async def get_sentiment_trends(
    days: int = Query(30, description="Number of days to analyze")
):
    """Get sentiment trends over time"""
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    pipeline = [
        {
            "$match": {
                "timestamp": {"$gte": start_date, "$lte": end_date},
                "sentiment": {"$exists": True, "$ne": None}
            }
        },
        {
            "$group": {
                "_id": {
                    "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                    "sentiment": "$sentiment"
                },
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id.date": 1}}
    ]
    
    db = await get_database()
    results = await db[POSTS_COLLECTION].aggregate(pipeline).to_list(None)
    
    # Organize by date
    trends = {}
    for result in results:
        date = result["_id"]["date"]
        sentiment = result["_id"]["sentiment"]
        count = result["count"]
        
        if date not in trends:
            trends[date] = {"positive": 0, "negative": 0, "neutral": 0}
        
        trends[date][sentiment] = count
    
    return {"trends": trends}

@router.get("/insights/popular-content")
async def get_popular_content(
    limit: int = Query(10, description="Number of items to return")
):
    """Get insights about popular content"""
    
    db = await get_database()
    
    # Most engaging posts (posts with media)
    engaging_posts = await db[POSTS_COLLECTION].find(
        {"media": {"$ne": []}},
        {"post_id": 1, "raw_text": 1, "platform": 1, "media": 1, "sentiment": 1}
    ).limit(limit).to_list(None)
    
    # Most common entities
    entity_pipeline = [
        {"$unwind": "$entities"},
        {"$group": {"_id": "$entities", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]
    common_entities = await db[POSTS_COLLECTION].aggregate(entity_pipeline).to_list(None)
    
    # Most common tags
    tag_pipeline = [
        {"$unwind": "$media"},
        {"$unwind": "$media.tags"},
        {"$group": {"_id": "$media.tags", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]
    common_tags = await db[POSTS_COLLECTION].aggregate(tag_pipeline).to_list(None)
    
    return {
        "engaging_posts": engaging_posts,
        "common_entities": common_entities,
        "common_tags": common_tags
    } 