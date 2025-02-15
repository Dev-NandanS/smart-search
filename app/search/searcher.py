from ..database.mongodb import get_db
from ..utils.text_utils import calculate_text_similarity
import logging

logger = logging.getLogger(__name__)

class ProductSearcher:
    def __init__(self):
        self.db = get_db()
        self.collection = self.db['products']
    
    def search(self, processed_query, page=1, page_size=10):
        """
        Search for products using processed query information
        """
        try:
            query_info = processed_query
            search_query = self._build_search_query(query_info)
            sort_options = self._get_sort_options(query_info.get('filters', {}))
            
            # Execute search
            skip = (page - 1) * page_size
            cursor = self.collection.find(
                search_query,
                self._get_projection()
            ).sort(sort_options).skip(skip).limit(page_size)
            
            # Get results and total count
            results = list(cursor)
            total_count = self.collection.count_documents(search_query)
            
            # Enhance results with relevance scoring
            enhanced_results = self._enhance_results(results, query_info)
            
            return {
                'results': enhanced_results,
                'total': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size
            }
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return None
    
    def _build_search_query(self, query_info):
        """
        Build MongoDB query from processed query information
        """
        must_clauses = []
        
        # Text search
        if query_info.get('tokens'):
            must_clauses.append({
                "$text": {
                    "$search": " ".join(query_info['tokens'])
                }
            })
        
        # Attribute filters
        attributes = query_info.get('attributes', {})
        if attributes.get('color'):
            must_clauses.append({
                "$or": [
                    {"TITLE": {"$regex": attributes['color'], "$options": "i"}},
                    {"BULLET_POINTS": {"$regex": attributes['color'], "$options": "i"}}
                ]
            })
        
        # Price range
        filters = query_info.get('filters', {})
        if 'price_min' in filters or 'price_max' in filters:
            price_clause = {}
            if 'price_min' in filters:
                price_clause['$gte'] = filters['price_min']
            if 'price_max' in filters:
                price_clause['$lte'] = filters['price_max']
            must_clauses.append({'prices.asins': price_clause})
        
        # Rating filter
        if 'min_rating' in filters:
            must_clauses.append({
                'overall_rating': {'$gte': filters['min_rating']}
            })
        
        return {"$and": must_clauses} if must_clauses else {}
    
    def _get_sort_options(self, filters):
        """
        Get sort options based on filters
        """
        sort_options = []
        
        if 'sort_by' in filters:
            if filters['sort_by'] == 'price_asc':
                sort_options.append(('prices.asins', 1))
            elif filters['sort_by'] == 'price_desc':
                sort_options.append(('prices.asins', -1))
            elif filters['sort_by'] == 'rating':
                sort_options.append(('overall_rating', -1))
        
        # Always add text score as secondary sort
        sort_options.append(('score', {'$meta': 'textScore'}))
        
        return sort_options
    
    def _get_projection(self):
        """
        Get fields to return in search results
        """
        return {
            'TITLE': 1,
            'PRODUCT_TYPE_ID': 1,
            'BULLET_POINTS': 1,
            'overall_rating': 1,
            'prices': 1,
            'DESCRIPTION': 1,
            'score': {'$meta': 'textScore'}
        }
    
    def _enhance_results(self, results, query_info):
        """
        Enhance search results with additional information
        """
        enhanced = []
        query_text = " ".join(query_info.get('tokens', []))
        
        for result in results:
            # Calculate text similarity score
            title_similarity = calculate_text_similarity(
                query_text,
                result.get('TITLE', '')
            )
            
            # Format price
            price = result.get('prices', {}).get('asins', 'N/A')
            
            # Enhanced result
            enhanced_result = {
                'title': result.get('TITLE'),
                'type': result.get('PRODUCT_TYPE_ID'),
                'rating': result.get('overall_rating'),
                'price': price,
                'bullet_points': result.get('BULLET_POINTS'),
                'relevance_score': title_similarity,
                'text_score': result.get('score', 0)
            }
            
            enhanced.append(enhanced_result)
        
        return enhanced