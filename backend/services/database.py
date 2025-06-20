import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Database configuration
MONGO_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "socialens")

# Global database client
client: AsyncIOMotorClient = None
sync_client: MongoClient = None

async def init_db():
    """Initialize database connection"""
    global client, sync_client
    
    client = AsyncIOMotorClient(MONGO_URL)
    sync_client = MongoClient(MONGO_URL)
    
    # Test connection
    await client.admin.command('ping')
    print("Connected to MongoDB!")

async def get_database():
    """Get database instance"""
    return client[DATABASE_NAME]

def get_sync_database():
    """Get synchronous database instance for Celery workers"""
    return sync_client[DATABASE_NAME]

async def close_db():
    """Close database connection"""
    if client:
        client.close()
    if sync_client:
        sync_client.close()

# Collection names
POSTS_COLLECTION = "posts"
UPLOADS_COLLECTION = "uploads"
ANALYTICS_COLLECTION = "analytics" 