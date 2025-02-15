import feedparser
from datetime import datetime
import logging

class Scraper:
    def __init__(self):
        self.name = "Hindustan Times"
        self.rss_url = "https://www.hindustantimes.com/feeds/rss/latest/rssfeed.xml"
        
    def scrape(self):
        """Scrape articles from Hindustan Times RSS feed"""
        try:
            feed = feedparser.parse(self.rss_url)
            articles = []
            
            for entry in feed.entries:
                article = {
                    'title': entry.title,
                    'description': entry.description,
                    'image_url': entry.media_content[0]['url'] if hasattr(entry, 'media_content') else None,
                    'source': self.name,
                    'scraped_at': datetime.now().isoformat()
                }
                articles.append(article)
                
            return articles
            
        except Exception as e:
            logging.error(f"Error scraping {self.name}: {str(e)}")
            raise e 