from ..utils.text_utils import preprocess_text, extract_product_attributes, generate_search_variations
import logging

logger = logging.getLogger(__name__)

class SearchQueryProcessor:
    def __init__(self):
        self.recent_queries = []
    
    def process_query(self, query, filters=None):
        """
        Process search query and extract relevant information
        """
        try:
            # Preprocess the query
            processed_tokens = preprocess_text(query)
            
            # Extract attributes
            attributes = extract_product_attributes(query)
            
            # Generate query variations
            variations = generate_search_variations(query)
            
            # Process filters
            processed_filters = self._process_filters(filters) if filters else {}
            
            # Store query for analytics
            self._store_query(query)
            
            return {
                'tokens': processed_tokens,
                'attributes': attributes,
                'variations': variations,
                'filters': processed_filters
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return None
    
    def _process_filters(self, filters):
        """
        Process and validate search filters
        """
        processed = {}
        
        try:
            if 'price_range' in filters:
                price_range = filters['price_range']
                processed['price_min'] = float(price_range.get('min', 0))
                processed['price_max'] = float(price_range.get('max', float('inf')))
            
            if 'rating' in filters:
                processed['min_rating'] = float(filters['rating'])
            
            if 'category' in filters:
                processed['category'] = filters['category']
            
            if 'sort_by' in filters:
                processed['sort_by'] = filters['sort_by']
                
        except (ValueError, TypeError) as e:
            logger.error(f"Error processing filters: {str(e)}")
            
        return processed
    
    def _store_query(self, query):
        """
        Store query for analytics purposes
        """
        self.recent_queries.append(query)
        if len(self.recent_queries) > 1000:  # Keep only last 1000 queries
            self.recent_queries.pop(0)
    
    def get_popular_queries(self, limit=10):
        """
        Get most popular recent queries
        """
        from collections import Counter
        
        query_counts = Counter(self.recent_queries)
        return [query for query, count in query_counts.most_common(limit)]