from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import csv
import json
import io
from typing import List, Optional
from datetime import datetime

from schemas.models import ExportRequest, DataFilter
from services.database import get_database, POSTS_COLLECTION

router = APIRouter()

@router.post("/csv")
async def export_csv(export_request: ExportRequest):
    """Export data as CSV"""
    
    # Build filter query
    filter_query = build_filter_query(export_request.filters)
    
    # Get posts from database
    db = await get_database()
    cursor = db[POSTS_COLLECTION].find(filter_query, {"_id": 0})
    posts = await cursor.to_list(None)
    
    if not posts:
        raise HTTPException(status_code=404, detail="No data found for export")
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    if export_request.fields:
        headers = export_request.fields
    else:
        # Default fields
        headers = [
            "post_id", "platform", "raw_text", "cleaned_text", "language",
            "timestamp", "user_id", "sentiment", "entities", "media_count"
        ]
    
    writer.writerow(headers)
    
    # Write data
    for post in posts:
        row = []
        for field in headers:
            if field == "media_count":
                row.append(len(post.get("media", [])))
            elif field == "entities":
                row.append(", ".join(post.get("entities", [])))
            elif field == "timestamp":
                timestamp = post.get("timestamp")
                if timestamp:
                    if isinstance(timestamp, datetime):
                        row.append(timestamp.isoformat())
                    else:
                        row.append(str(timestamp))
                else:
                    row.append("")
            else:
                row.append(str(post.get(field, "")))
        writer.writerow(row)
    
    output.seek(0)
    
    # Create response
    filename = f"socialens_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/json")
async def export_json(export_request: ExportRequest):
    """Export data as JSON"""
    
    # Build filter query
    filter_query = build_filter_query(export_request.filters)
    
    # Get posts from database
    db = await get_database()
    cursor = db[POSTS_COLLECTION].find(filter_query, {"_id": 0})
    posts = await cursor.to_list(None)
    
    if not posts:
        raise HTTPException(status_code=404, detail="No data found for export")
    
    # Filter fields if specified
    if export_request.fields:
        filtered_posts = []
        for post in posts:
            filtered_post = {}
            for field in export_request.fields:
                if field in post:
                    filtered_post[field] = post[field]
            filtered_posts.append(filtered_post)
        posts = filtered_posts
    
    # Create response
    filename = f"socialens_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    return StreamingResponse(
        io.BytesIO(json.dumps(posts, indent=2, default=str).encode('utf-8')),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

def build_filter_query(filters: Optional[DataFilter]) -> dict:
    """Build MongoDB filter query from DataFilter"""
    if not filters:
        return {}
    
    filter_query = {}
    
    if filters.platform:
        filter_query["platform"] = filters.platform
    
    if filters.sentiment:
        filter_query["sentiment"] = filters.sentiment
    
    if filters.language:
        filter_query["language"] = filters.language
    
    if filters.has_media is not None:
        if filters.has_media:
            filter_query["media"] = {"$ne": []}
        else:
            filter_query["media"] = []
    
    # Date range filter
    if filters.date_from or filters.date_to:
        date_filter = {}
        if filters.date_from:
            date_filter["$gte"] = filters.date_from
        
        if filters.date_to:
            date_filter["$lte"] = filters.date_to
        
        filter_query["timestamp"] = date_filter
    
    # Text search
    if filters.search_text:
        filter_query["$or"] = [
            {"raw_text": {"$regex": filters.search_text, "$options": "i"}},
            {"cleaned_text": {"$regex": filters.search_text, "$options": "i"}}
        ]
    
    return filter_query 