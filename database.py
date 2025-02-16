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
        self.CURRENT_KEY = "current_articles"  # New key for current articles
        self.EXPIRY_DAYS = 3

    def save_articles(self, articles):
        """Save articles to Redis"""
        try:
            # Save current articles with newsId as key
            pipeline = self.redis_client.pipeline()
            
            # Clear previous day's data
            pipeline.delete(self.CURRENT_KEY)
            
            # Save new articles
            articles_dict = {
                article['newsId']: json.dumps({
                    **article,
                    'stored_at': datetime.utcnow().isoformat()
                })
                for article in articles
            }
            
            if articles_dict:
                pipeline.hset(self.CURRENT_KEY, mapping=articles_dict)
            
            # Execute all commands
            pipeline.execute()
            
            logging.info(f"Successfully saved {len(articles)} articles to Redis")
            return len(articles)
            
        except Exception as e:
            logging.error(f"Error saving to Redis: {str(e)}")
            raise e

    def get_latest_articles(self):
        """Get the current articles"""
        try:
            articles_dict = self.redis_client.hgetall(self.CURRENT_KEY)
            return [json.loads(article) for article in articles_dict.values()]
        except Exception as e:
            logging.error(f"Error retrieving from Redis: {str(e)}")
            return []

    def get_article_by_id(self, news_id):
        """Get specific article by newsId"""
        try:
            article_json = self.redis_client.hget(self.CURRENT_KEY, news_id)
            return json.loads(article_json) if article_json else None
        except Exception as e:
            logging.error(f"Error retrieving article by ID: {str(e)}")
            return None

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
        """Get most recent articles, limited by count"""
        try:
            latest_articles = self.get_latest_articles()
            # Sort by stored_at timestamp in descending order (newest first)
            sorted_articles = sorted(latest_articles, 
                                   key=lambda x: x.get('stored_at', ''), 
                                   reverse=True)
            return sorted_articles[:limit]
        except Exception as e:
            logging.error(f"Error getting top articles: {str(e)}")
            return []

    def get_sources_list(self):
        """Get list of all news sources"""
        try:
            latest_articles = self.get_latest_articles()
            return list(set(article['source'] for article in latest_articles))
        except Exception as e:
            logging.error(f"Error getting sources list: {str(e)}")
            return [] 