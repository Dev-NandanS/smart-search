from pymongo import MongoClient
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class MongoDB:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        """
        Connect to MongoDB
        """
        try:
            mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
            self.client = MongoClient(mongo_uri)
            self.db = self.client[os.getenv('MONGODB_DB', 'data_scout')]
            
            # Test connection
            self.client.server_info()
            logger.info("Successfully connected to MongoDB")
            
            # Create text index if it doesn't exist
            self._ensure_indexes()
            
        except Exception as e:
            logger.error(f"MongoDB connection error: {str(e)}")
            raise
    
    def _ensure_indexes(self):
        """
        Ensure required indexes exist
        """
        try:
            # Create text index on relevant fields
            self.db.products.create_index([
                ('TITLE', 'text'),
                ('BULLET_POINTS', 'text'),
                ('DESCRIPTION', 'text')
            ])
            
            # Create index on product type
            self.db.products.create_index('PRODUCT_TYPE_ID')
            
            # Create index on rating
            self.db.products.create_index('overall_rating')
            
            logger.info("MongoDB indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {str(e)}")
            raise
    
    def get_db(self):
        """
        Get database instance
        """
        return self.db

def get_db():
    """
    Utility function to get database instance
    """
    return MongoDB.get_instance().get_db()