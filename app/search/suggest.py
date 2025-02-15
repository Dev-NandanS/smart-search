from ..database.mongodb import get_db
from ..utils.text_utils import preprocess_text, calculate_text_similarity
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class SearchSuggester:
    def __init__(self):
        self.db = get_db()
        self.collection = self.db['products']
        self.recent_searches = defaultdict(int)
        self._initialize_cache()
    
    def _initialize_cache(self):
        """
        Initialize suggestion cache
        """
        self.title_cache = set()
        self.category_cache = set()
        
        try:
            # Cache product titles
            titles = self.collection.distinct('TITLE')
            self.title_cache.update(titles)
            
            # Cache categories
            categories = self.collection.distinct('PRODUCT_TYPE_ID')
            self.category_cache.update(categories)
            
        except Exception as e:
            logger.error(f"Error initializing suggestion cache: {str(e)}")
    
    def get_suggestions(self, partial_query, limit=5):
        """
        Get search suggestions based on partial query
        """
        try:
            suggestions = []
            
            # Preprocess the partial query
            processed_query = " ".join(preprocess_text(partial_query))
            
            # Get title suggestions
            title_suggestions = self._get_title_suggestions(processed_query, limit)
            suggestions.extend(title_suggestions)
            
            # Get category suggestions
            if len(suggestions) < limit:
                remaining = limit - len(suggestions)
                category_suggestions = self._get_category_suggestions(processed_query, remaining)
                suggestions.extend(category_suggestions)
            
            # Get popular search suggestions
            if len(suggestions) < limit:
                remaining = limit - len(suggestions)
                popular_suggestions = self._get_popular_suggestions(processed_query, remaining)
                suggestions.extend(popular_suggestions)
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Error getting suggestions: {str(e)}")
            return []
    
    def _get_title_suggestions(self, query, limit):
        """
        Get suggestions based on product titles
        """
        suggestions = []
        
        for title in self.title_cache:
            similarity = calculate_text_similarity(query.lower(), title.lower())
            if similarity > 0.3:  # Threshold for similarity
                suggestions.append({
                    'type': 'product',
                    'text': title,
                    'score': similarity
                })
        
        # Sort by similarity score
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        return suggestions[:limit]
    
    def _get_category_suggestions(self, query, limit):
        """
        Get suggestions based on product categories
        """
        suggestions = []
        
        for category in self.category_cache:
            similarity = calculate_text_similarity(query.lower(), str(category).lower())
            if similarity > 0.3:
                suggestions.append({
                    'type': 'category',
                    'text': f'Category: {category}',
                    'score': similarity
                })
        
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        return suggestions[:limit]
    
    def _get_popular_suggestions(self, query, limit):
        """
        Get suggestions based on popular searches
        """
        suggestions = []
        
        # Sort recent searches by frequency
        popular_searches = sorted(
            self.recent_searches.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for search, count in popular_searches:
            similarity = calculate_text_similarity(query.lower(), search.lower())
            if similarity > 0.3:
                suggestions.append({
                    'type': 'popular',
                    'text': search,
                    'score': similarity * (count / max(self.recent_searches.values()))
                })
        
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        return suggestions[:limit]
    
    def add_to_recent_searches(self, query):
        """
        Add a search query to recent searches
        """
        self.recent_searches[query] += 1
        
        # Keep only top 1000 searches
        if len(self.recent_searches) > 1000:
            min_count = min(self.recent_searches.values())
            for query in list(self.recent_searches.keys()):
                if self.recent_searches[query] == min_count:
                    del self.recent_searches[query]
                    break