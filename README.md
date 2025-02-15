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
   pip3 install feedparser requests
   ```

2. Run the scraper:
   ```bash
   python3 main.py
   ```

