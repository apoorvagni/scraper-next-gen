from flask import Flask, jsonify, request
from flask_cors import CORS
from main import main as scrape_engine
import threading
import schedule
import time
from datetime import datetime
import pytz
from database import RedisDB

app = Flask(__name__)

# Enable CORS for all routes
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],
        "methods": ["POST", "GET", "OPTIONS"],
        "allow_headers": "*",
        "expose_headers": "*",
    }
})

# Store the last scraped results
last_scraped_data = None

def run_scraper():
    global last_scraped_data
    try:
        # Log the execution time
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S %Z')
        print(f"Scraper running at {current_time}")
        
        scrape_engine()
        return {"status": "success", "message": "Scraping completed successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def schedule_scraper():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Schedule the scraper to run daily at 4 AM IST
schedule.every().day.at("04:00").do(run_scraper)

# Start the scheduler in a separate thread
scheduler_thread = threading.Thread(target=schedule_scraper, daemon=True)
scheduler_thread.start()

@app.route('/api/scrape', methods=['GET'])
def trigger_scrape():
    return jsonify(run_scraper())

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

@app.route('/api/articles', methods=['GET'])
def get_articles():
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=6, type=int)
    
    db = RedisDB()
    all_articles = db.get_latest_articles()
    
    # Calculate start and end indices for pagination
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    paginated_articles = all_articles[start_idx:end_idx]
    total_articles = len(all_articles)
    total_pages = (total_articles + per_page - 1) // per_page
    
    return jsonify({
        'articles': paginated_articles,
        'pagination': {
            'current_page': page,
            'per_page': per_page,
            'total_articles': total_articles,
            'total_pages': total_pages
        }
    })

@app.route('/api/articles/trending', methods=['GET'])
def get_trending():
    limit = request.args.get('limit', default=10, type=int)
    db = RedisDB()
    return jsonify(db.get_top_trending_articles(limit=limit))

@app.route('/api/articles/source/<source_name>', methods=['GET'])
def get_by_source(source_name):
    db = RedisDB()
    return jsonify(db.get_articles_by_source(source_name))

@app.route('/api/sources', methods=['GET'])
def get_sources():
    db = RedisDB()
    return jsonify(db.get_sources_list())

@app.route('/api/articles/<news_id>', methods=['GET'])
def get_article_by_id(news_id):
    db = RedisDB()
    article = db.get_article_by_id(news_id)
    if article:
        return jsonify(article)
    return jsonify({"error": "Article not found"}), 404

# Remove or modify this part
if __name__ == '__main__':
    # Only use this for local development
    app.run(debug=True) 