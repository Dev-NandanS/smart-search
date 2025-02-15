from ..database.mongodb import get_db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SearchAnalytics:
    def __init__(self):
        self.db = get_db()
        self.collection = self.db['search_analytics']
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """
        Create necessary indexes for analytics
        """
        try:
            # Index on timestamp for time-based queries
            self.collection.create_index('timestamp')
            # Index on query for aggregations
            self.collection.create_index('query')
            
        except Exception as e:
            logger.error(f"Error creating analytics indexes: {str(e)}")
    
    def track_search(self, query, user_id=None, results_count=0, filters=None):
        """
        Track a search event
        """
        try:
            search_event = {
                'timestamp': datetime.utcnow(),
                'query': query,
                'user_id': user_id,
                'results_count': results_count,
                'filters': filters or {}
            }
            
            self.collection.insert_one(search_event)
            
        except Exception as e:
            logger.error(f"Error tracking search: {str(e)}")
    
    def track_suggestion_click(self, suggestion, user_id=None):
        """
        Track when a user clicks a suggestion
        """
        try:
            click_event = {
                'timestamp': datetime.utcnow(),
                'suggestion': suggestion,
                'user_id': user_id,
                'event_type': 'suggestion_click'
            }
            
            self.collection.insert_one(click_event)
            
        except Exception as e:
            logger.error(f"Error tracking suggestion click: {str(e)}")
    
    def get_popular_searches(self, time_range=None, limit=10):
        """
        Get most popular searches within time range
        """
        try:
            match_stage = {}
            if time_range:
                match_stage['timestamp'] = {
                    '$gte': datetime.utcnow() - time_range
                }
            
            pipeline = [
                {'$match': match_stage},
                {'$group': {
                    '_id': '$query',
                    'count': {'$sum': 1},
                    'avg_results': {'$avg': '$results_count'}
                }},
                {'$sort': {'count': -1}},
                {'$limit': limit}
            ]
            
            results = list(self.collection.aggregate(pipeline))
            return results
            
        except Exception as e:
            logger.error(f"Error getting popular searches: {str(e)}")
            return []
    
    def get_search_statistics(self, time_range=None):
        """
        Get general search statistics
        """
        try:
            match_stage = {}
            if time_range:
                match_stage['timestamp'] = {
                    '$gte': datetime.utcnow() - time_range
                }
            
            pipeline = [
                {'$match': match_stage},
                {'$group': {
                    '_id': None,
                    'total_searches': {'$sum': 1},
                    'avg_results': {'$avg': '$results_count'},
                    'unique_queries': {'$addToSet': '$query'},
                    'filtered_searches': {
                        '$sum': {'$cond': [{'$gt': [{'$size': {'$objectToArray': '$filters'}}, 0]}, 1, 0]}
                    }
                }}
            ]
            
            results = list(self.collection.aggregate(pipeline))
            if results:
                stats = results[0]
                stats['unique_queries'] = len(stats['unique_queries'])
                return stats
            return None
            
        except Exception as e:
            logger.error(f"Error getting search statistics: {str(e)}")
            return None