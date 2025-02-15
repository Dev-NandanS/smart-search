from flask import Flask, request, jsonify
from flask_cors import CORS
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from bson import ObjectId
import logging
import os
from dotenv import load_dotenv
import json
from bson.json_util import dumps, loads

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# MongoDB setup
try:
    MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    client = MongoClient(MONGO_URI)
    db = client['data_scout']
    products_collection = db['products']
    
    # Check existing indexes
    existing_indexes = products_collection.list_indexes()
    has_text_index = False
    for index in existing_indexes:
        if index.get('textIndexVersion'):
            has_text_index = True
            break
    
    # Create text index only if it doesn't exist
    if not has_text_index:
        products_collection.create_index([
            ("TITLE", TEXT),
            ("BULLET_POINTS", TEXT),
            ("DESCRIPTION", TEXT)
        ])
    
    # Create other indexes
    products_collection.create_index([("overall_rating", ASCENDING)])
    products_collection.create_index([("prices.asins", ASCENDING)])
    
    logger.info("Successfully connected to MongoDB and verified indexes")
except Exception as e:
    logger.error(f"MongoDB error: {str(e)}")
    raise

def process_query(query):
    """Process the natural language query"""
    query = query.lower()
    tokens = word_tokenize(query)
    stop_words = set(stopwords.words('english'))
    keywords = [word for word in tokens if word not in stop_words and word.isalnum()]
    return keywords

@app.route('/api/v1/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                "error": "Missing required field: query",
                "status": "error"
            }), 400

        query = data['query']
        filters = data.get('filters', {})
        
        # Process keywords
        keywords = process_query(query)
        if not keywords:
            return jsonify({"results": [], "total": 0, "status": "success"}), 200

        # Base query using text search
        base_query = {"$text": {"$search": " ".join(keywords)}}
        
        # Add filters if present
        filter_conditions = []
        if filters.get('price_min') is not None:
            filter_conditions.append({"prices.asins": {"$gte": float(filters['price_min'])}})
        if filters.get('price_max') is not None:
            filter_conditions.append({"prices.asins": {"$lte": float(filters['price_max'])}})
        if filters.get('min_rating') is not None:
            filter_conditions.append({"overall_rating": {"$gte": float(filters['min_rating'])}})

        # Combine base query with filters
        if filter_conditions:
            search_query = {"$and": [base_query] + filter_conditions}
        else:
            search_query = base_query

        # Sort options
        sort_options = []
        if filters.get('sort_by'):
            if filters['sort_by'] == 'price_asc':
                sort_options.append(('prices.asins', ASCENDING))
            elif filters['sort_by'] == 'price_desc':
                sort_options.append(('prices.asins', DESCENDING))
            elif filters['sort_by'] == 'rating':
                sort_options.append(('overall_rating', DESCENDING))
        
        # Add text score sort
        sort_options.append(('score', {'$meta': 'textScore'}))

        # Execute search
        projection = {
            'TITLE': 1,
            'PRODUCT_TYPE_ID': 1,
            'BULLET_POINTS': 1,
            'overall_rating': 1,
            'prices': 1,
            'score': {'$meta': 'textScore'}
        }

        cursor = products_collection.find(search_query, projection)
        if sort_options:
            cursor = cursor.sort(sort_options)
        
        results = list(cursor.limit(20))

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
                "processed_keywords": keywords,
                "query": json.loads(dumps(search_query))
            }
        }), 200

    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
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
        
        # Get collection stats
        stats = db.command("collstats", "products")
        
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "collection_info": {
                "document_count": stats.get("count", 0),
                "size_mb": round(stats.get("size", 0) / (1024 * 1024), 2)
            }
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)