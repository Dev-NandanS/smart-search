from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from fuzzywuzzy import fuzz
import nltk
import re

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def preprocess_text(text):
    """
    Preprocess text by converting to lowercase, removing special characters,
    and lemmatizing words
    """
    # Convert to lowercase and remove special characters
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Remove stopwords and lemmatize
    processed_tokens = [lemmatizer.lemmatize(token) for token in tokens 
                       if token not in stop_words and len(token) > 1]
    
    return processed_tokens

def calculate_text_similarity(text1, text2):
    """
    Calculate similarity between two texts using fuzzy matching
    """
    return fuzz.ratio(text1.lower(), text2.lower()) / 100.0

def extract_product_attributes(text):
    """
    Extract product attributes from text using regex patterns
    """
    attributes = {
        'color': None,
        'size': None,
        'price_range': None,
        'brand': None
    }
    
    # Color detection
    colors = ['red', 'blue', 'green', 'black', 'white', 'yellow']
    color_pattern = r'\b(' + '|'.join(colors) + r')\b'
    color_match = re.search(color_pattern, text.lower())
    if color_match:
        attributes['color'] = color_match.group(1)
    
    # Price range detection
    price_pattern = r'under\s*\$?(\d+)|less than\s*\$?(\d+)|around\s*\$?(\d+)'
    price_match = re.search(price_pattern, text.lower())
    if price_match:
        price = next(p for p in price_match.groups() if p is not None)
        attributes['price_range'] = float(price)
    
    return attributes

def generate_search_variations(query):
    """
    Generate variations of the search query for better matching
    """
    variations = set([query])
    
    # Tokenize and process
    tokens = preprocess_text(query)
    
    # Generate combinations
    for i in range(len(tokens)):
        for j in range(i + 1, len(tokens) + 1):
            variation = ' '.join(tokens[i:j])
            if variation:
                variations.add(variation)
    
    return list(variations)