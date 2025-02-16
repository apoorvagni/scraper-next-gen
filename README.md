# RSS News Scraper with Trending Topics

This project is a Python-based RSS feed scraper that collects news articles and filters them based on current Google Trends. The scraper removes duplicate articles and only keeps trending news topics.

## Features

- Scrapes news articles from multiple RSS feeds
- Filters articles based on trending topics
- Removes duplicate articles about the same topic
- Exports filtered articles to CSV files
- Modular design for easy addition of new news sources

## Running the Scraper

1. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the scraper:
   ```bash
   python3 main.py
   ```

## API curl commands

curl -X GET http://localhost:8000/api/articles

curl -X GET https://scraper-next-gen.vercel.app/api/scrape

curl -X GET https://scraper-next-gen.vercel.app/api/articles

curl -X GET https://scraper-next-gen.vercel.app/api/articles/trending?limit=5

curl -X GET https://scraper-next-gen.vercel.app/api/articles/source/Hindustan%20Times

curl -X GET https://scraper-next-gen.vercel.app/api/health

