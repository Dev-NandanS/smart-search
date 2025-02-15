import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # MongoDB settings
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    MONGODB_DB = os.getenv('MONGODB_DB', 'data_scout')
    
    # Search settings
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100
    MIN_SEARCH_CHARS = 2
    
    # Suggestion settings
    MAX_SUGGESTIONS = 5
    SUGGESTION_SIMILARITY_THRESHOLD = 0.3
    
    # Analytics settings
    MAX_RECENT_SEARCHES = 1000
    
    # Cache settings
    CACHE_TIMEOUT = 3600  # 1 hour
    
    # API settings
    CORS_ORIGINS = ['http://localhost:3000']  # Add your frontend origins
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Text processing settings
    STOP_WORDS_LANGUAGE = 'english'
    MIN_WORD_LENGTH = 2
    
    # Search relevance settings
    MIN_RELEVANCE_SCORE = 0.3
    TEXT_SCORE_WEIGHT = 0.7
    SIMILARITY_SCORE_WEIGHT = 0.3