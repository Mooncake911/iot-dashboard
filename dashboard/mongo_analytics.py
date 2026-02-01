import logging
from typing import List, Dict, Any

from dashboard.mongo_alerts import get_mongo_client
from dashboard.mock import is_mock_mode, MockMongoAnalytics

logger = logging.getLogger(__name__)

def fetch_analytics_history(
    mongo_uri: str,
    db_name: str,
    collection_name: str,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Fetch historical analytics data from MongoDB.
    
    Args:
        mongo_uri: MongoDB connection URI
        db_name: Database name
        collection_name: Collection name
        limit: Maximum number of records to fetch
        
    Returns:
        List of analytics documents
    """
    if is_mock_mode():
        return MockMongoAnalytics.fetch_analytics_history(mongo_uri, db_name, collection_name, limit)

    try:
        client = get_mongo_client(mongo_uri)
        db = client[db_name]
        collection = db[collection_name]
        
        # Fetch newest first, then we'll reverse for the chart
        cursor = collection.find().sort("timestamp", -1).limit(limit)
        docs = list(cursor)
        
        # Convert ObjectId
        for doc in docs:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
                
        return docs
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        return []
