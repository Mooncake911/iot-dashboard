import logging
from typing import List, Dict, Any
from dashboard.mongo.base import MongoBaseRepository

logger = logging.getLogger(__name__)


class MongoAnalyticsRepository(MongoBaseRepository):
    def fetch_data(self, limit: int) -> List[Dict[str, Any]]:
        try:
            collection = self.get_collection()

            cursor = collection.find().sort("timestamp", -1).limit(limit)
            docs = list(cursor)

            # ObjectId to string
            for doc in docs:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])

            return docs

        except Exception as e:
            logger.error(f"Error fetching analytics: {e}")
            return []
