import os
import json
import redis
from datetime import datetime, timedelta
import logging

class RedisDB:
    def __init__(self):
        redis_url = os.getenv('REDIS_URL')
        if not redis_url:
            raise ValueError("REDIS_URL environment variable is not set")
        
        self.redis_client = redis.from_url(redis_url)
        self.ARTICLES_KEY = "news_articles"
        self.EXPIRY_DAYS = 3

    def save_articles(self, articles):
        """Save articles to Redis"""
        try:
            # Add timestamp to each article
            timestamp = datetime.utcnow().isoformat()
            key = f"{self.ARTICLES_KEY}:{timestamp}"
            
            # Convert articles to JSON string
            articles_json = json.dumps([
                {**article, 'stored_at': timestamp}
                for article in articles
            ])
            
            # Save to Redis with expiration
            self.redis_client.setex(
                key,
                timedelta(days=self.EXPIRY_DAYS),
                articles_json
            )
            
            # Save the key to a list of all article keys
            self.redis_client.lpush(f"{self.ARTICLES_KEY}:keys", key)
            
            logging.info(f"Successfully saved {len(articles)} articles to Redis")
            return len(articles)
            
        except Exception as e:
            logging.error(f"Error saving to Redis: {str(e)}")
            raise e

    def get_latest_articles(self):
        """Get the most recent articles"""
        try:
            # Get the most recent key
            latest_key = self.redis_client.lindex(f"{self.ARTICLES_KEY}:keys", 0)
            if not latest_key:
                return []
                
            articles_json = self.redis_client.get(latest_key)
            if not articles_json:
                return []
                
            return json.loads(articles_json)
            
        except Exception as e:
            logging.error(f"Error retrieving from Redis: {str(e)}")
            return []

    def cleanup_old_articles(self):
        """Redis automatically handles cleanup through key expiration"""
        pass

    def get_articles_by_source(self, source_name):
        """Get articles filtered by news source"""
        try:
            latest_articles = self.get_latest_articles()
            return [article for article in latest_articles if article['source'] == source_name]
        except Exception as e:
            logging.error(f"Error getting articles by source: {str(e)}")
            return []

    def get_top_trending_articles(self, limit=10):
        """Get top trending articles sorted by rank"""
        try:
            latest_articles = self.get_latest_articles()
            sorted_articles = sorted(latest_articles, key=lambda x: x.get('rank', float('inf')))
            return sorted_articles[:limit]
        except Exception as e:
            logging.error(f"Error getting top trending articles: {str(e)}")
            return []

    def get_sources_list(self):
        """Get list of all news sources"""
        try:
            latest_articles = self.get_latest_articles()
            return list(set(article['source'] for article in latest_articles))
        except Exception as e:
            logging.error(f"Error getting sources list: {str(e)}")
            return [] 