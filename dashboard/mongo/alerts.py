import logging
from typing import List, Dict, Any
from dashboard.mongo.base import MongoBaseRepository

logger = logging.getLogger(__name__)

class MongoAlertsRepository(MongoBaseRepository):
    def fetch_data(self, limit: int) -> List[Dict[str, Any]]:
        try:
            collection = self.get_collection()
            
            # Auto-detect sort field
            sort_field = "receivedAt"
            if collection.estimated_document_count() > 0:
                sample = collection.find_one()
                if sample:
                    if "receivedAt" in sample: sort_field = "receivedAt"
                    elif "alertTimestamp" in sample: sort_field = "alertTimestamp"
                    else: sort_field = "_id"

            cursor = collection.find({}, limit=limit).sort(sort_field, -1)
            alerts = list(cursor)
            
            # ObjectId to string
            for alert in alerts:
                if "_id" in alert:
                    alert["_id"] = str(alert["_id"])
            
            return alerts
        except Exception as e:
            logger.error(f"Error fetching alerts: {e}")
            return []
