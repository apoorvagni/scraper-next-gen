import importlib
import os
from datetime import datetime
import logging
import csv
import pathlib
import requests
from difflib import SequenceMatcher
from serpapi import GoogleSearch
from database import RedisDB

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Log to console instead of a file
    ]
)

def get_trending_topics():
    """Fetch trending topics from Google Trends API and assign ranking based on the API order"""
    api_key = os.getenv('SERPAPI_KEY', 'ae1e73def8d507930792faa819041fbb885842560679c306dc21ddf24abc98eb')
    params = {
        "api_key": api_key,
        "engine": "google_trends_trending_now",
        "geo": "IN"
    }
    
    try:
        search = GoogleSearch(params)
        data = search.get_dict()
        
        trending_topics = []
        
        if 'trending_searches' in data:
            trends = data['trending_searches']
        elif 'trending_now' in data:
            trends = data['trending_now']
        else:
            logging.error(f"Unexpected API response format: {data.keys()}")
            return []
        
        # Use the order returned by the API as the ranking.
        for rank, trend in enumerate(trends, start=1):
            if isinstance(trend, dict):
                query = trend.get('title', trend.get('query', ''))
                trending_topics.append({
                    "query": query.lower(),
                    "rank": rank
                })
            elif isinstance(trend, str):
                trending_topics.append({
                    "query": trend.lower(),
                    "rank": rank
                })
                
        if not trending_topics:
            logging.warning("No trending topics found in the API response")
            
        return trending_topics
    except Exception as e:
        logging.error(f"Error fetching Google Trends: {str(e)}")
        if hasattr(e, 'response'):
            logging.error(f"API Response: {e.response.text}")
        return []

def is_similar(str1, str2, threshold=0.6):
    """Check if two strings are similar using SequenceMatcher"""
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio() > threshold

def is_related_to_trends(article, trending_topics):
    """Check if article is related to trending topics based on simple text matching"""
    title = article['title'].lower()
    description = article['description'].lower()
    
    for topic in trending_topics:
        if topic["query"] in title or topic["query"] in description:
            return True
            
    title_words = set(title.split())
    for topic in trending_topics:
        topic_words = set(topic["query"].split())
        for word in title_words:
            for topic_word in topic_words:
                if is_similar(word, topic_word):
                    return True
                    
    return False

def get_article_trending_metrics(article, trending_topics):
    """
    Find the first matching trending topic (in API order) for the article.
    Returns the matching topic dictionary or None if no match is found.
    """
    article_text = article['title'].lower() + " " + article['description'].lower()
    for topic in trending_topics:
        if topic["query"] in article_text:
            return topic
        else:
            for breakdown in topic.get("trend_breakdown", []):
                if breakdown.lower() in article_text:
                    return topic
    return None

def remove_duplicates(articles):
    """Remove duplicate articles about the same topic"""
    unique_articles = []
    seen_topics = set()
    
    for article in articles:
        title_words = set(article['title'].lower().split())
        is_duplicate = False
        
        for seen_title in seen_topics:
            seen_words = set(seen_title.split())
            common_words = title_words & seen_words
            
            if len(common_words) / len(title_words) > 0.4:
                is_duplicate = True
                break
                
        if not is_duplicate:
            unique_articles.append(article)
            seen_topics.add(article['title'].lower())
            
    return unique_articles

def save_to_csv(articles, output_dir="output"):
    """Save scraped articles to CSV file with date-based naming"""
    pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Use date-only format for filename
    date = datetime.now().strftime("%Y%m%d")
    filename = f"{output_dir}/articles_{date}.csv"
    
    fieldnames = ['title', 'description', 'image_url', 'source', 'scraped_at', 'search_volume', 'increase_percentage']
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for article in articles:
                # Create a copy without the rank field
                article_copy = {k: v for k, v in article.items() if k in fieldnames}
                writer.writerow(article_copy)
        logging.info(f"Successfully saved {len(articles)} articles to {filename}")
        return filename
    except Exception as e:
        logging.error(f"Error saving to CSV: {str(e)}")
        raise e

def load_scrapers():
    """Dynamically load all scraper modules from the websites directory"""
    scrapers = []
    websites_dir = "websites"
    
    for file in os.listdir(websites_dir):
        if file.endswith(".py") and not file.startswith("__"):
            module_name = f"websites.{file[:-3]}"
            try:
                module = importlib.import_module(module_name)
                scrapers.append(module.Scraper())
                logging.info(f"Loaded scraper: {module_name}")
            except Exception as e:
                logging.error(f"Failed to load {module_name}: {str(e)}")
    
    return scrapers

def cleanup_old_files(output_dir="output", days=3):
    """Delete CSV files older than specified number of days"""
    try:
        current_time = datetime.now()
        for file in pathlib.Path(output_dir).glob("articles_*.csv"):
            # Extract date from filename
            try:
                file_date_str = file.stem.split('_')[1]
                file_date = datetime.strptime(file_date_str, "%Y%m%d")
                
                # Calculate age in days
                age = (current_time - file_date).days
                
                # Delete if older than specified days
                if age > days:
                    file.unlink()
                    logging.info(f"Deleted old file: {file}")
            except (IndexError, ValueError):
                logging.warning(f"Skipping file with invalid name format: {file}")
                
    except Exception as e:
        logging.error(f"Error cleaning up old files: {str(e)}")

def save_to_database(articles):
    """Save scraped articles to Redis"""
    try:
        db = RedisDB()
        saved_count = db.save_articles(articles)
        logging.info(f"Successfully saved {saved_count} articles to Redis")
    except Exception as e:
        logging.error(f"Error saving to database: {str(e)}")
        raise e

def main():
    """Main function to run all scrapers and sort articles based on trending metrics"""
    logging.info("Starting RSS feed scraping")
    
    # Clean up old files before processing
    cleanup_old_files()
    
    trending_topics = get_trending_topics()
    if not trending_topics:
        logging.error("Failed to fetch trending topics")
        return
        
    scrapers = load_scrapers()
    all_articles = []
    
    for scraper in scrapers:
        try:
            articles = scraper.scrape()
            trending_articles = []
            for article in articles:
                topic = get_article_trending_metrics(article, trending_topics)
                if topic:
                    # Generate a unique newsId using timestamp and a hash of the title
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    article_hash = str(hash(article['title']))[-4:]  # Last 4 digits of title hash
                    article["newsId"] = f"NEWS_{timestamp}_{article_hash}"
                    trending_articles.append(article)
            all_articles.extend(trending_articles)
            logging.info(f"Found {len(trending_articles)} trending articles out of {len(articles)} from {scraper.name}")
        except Exception as e:
            logging.error(f"Error scraping {scraper.name}: {str(e)}")
    
    if all_articles:
        unique_articles = remove_duplicates(all_articles)
        logging.info(f"Removed {len(all_articles) - len(unique_articles)} duplicate articles")
        
        try:
            save_to_database(unique_articles)
            logging.info(f"All trending articles saved to database")
        except Exception as e:
            logging.error(f"Failed to save articles: {str(e)}")

if __name__ == "__main__":
    main() 