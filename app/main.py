from flask import Flask, request, jsonify
from flask_cors import CORS
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from pymongo import MongoClient
import logging
import os
from dotenv import load_dotenv

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# MongoDB setup
try:
    MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    client = MongoClient(MONGO_URI)
    db = client['data_scout']
    products_collection = db['products']
    logger.info("Successfully connected to MongoDB")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {str(e)}")
    raise

def process_query(query):
    """Process the natural language query"""
    query = query.lower()
    tokens = word_tokenize(query)
    stop_words = set(stopwords.words('english'))
    keywords = [word for word in tokens if word not in stop_words and word.isalnum()]
    return keywords

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Smart Search API is running",
        "endpoints": {
            "search": "/api/v1/search [POST]",
            "health": "/api/v1/health [GET]"
        },
        "version": "1.0.0"
    })

@app.route('/api/v1/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                "error": "Missing required field: query",
                "status": "error"
            }), 400

        # Process query
        query = data['query']
        keywords = process_query(query)
        
        if not keywords:
            return jsonify({
                "results": [],
                "total": 0,
                "status": "success"
            }), 200

        # Perform text search
        results = list(products_collection.find(
            {"$text": {"$search": " ".join(keywords)}},
            {
                'TITLE': 1,
                'PRODUCT_TYPE_ID': 1,
                'overall_rating': 1,
                'prices': 1,
                'score': {'$meta': 'textScore'}
            }
        ).sort([('score', {'$meta': 'textScore'})]).limit(20))

        # Format results
        formatted_results = [{
            "title": product.get('TITLE'),
            "type": product.get('PRODUCT_TYPE_ID'),
            "price": product.get('prices', {}).get('asins'),
            "rating": product.get('overall_rating'),
            "relevance_score": product.get('score', 0)
        } for product in results]

        return jsonify({
            "results": formatted_results,
            "total": len(formatted_results),
            "status": "success",
            "debug_info": {
                "processed_keywords": keywords
            }
        }), 200

    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e),
            "status": "error"
        }), 500

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    try:
        # Check MongoDB connection
        client.server_info()
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "app_version": "1.0.0",
            "nltk_data": {
                "punkt": nltk.data.find('tokenizers/punkt') is not None,
                "stopwords": nltk.data.find('corpora/stopwords') is not None
            }
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    # Get port from environment variable or default to 8000
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)