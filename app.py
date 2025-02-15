from flask import Flask, jsonify
from main import main as scrape_engine
import threading
import schedule
import time

app = Flask(__name__)

# Store the last scraped results
last_scraped_data = None

def run_scraper():
    global last_scraped_data
    try:
        scrape_engine()
        return {"status": "success", "message": "Scraping completed successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def schedule_scraper():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Schedule the scraper to run every 6 hours
schedule.every(24).hours.do(run_scraper)

# Start the scheduler in a separate thread
scheduler_thread = threading.Thread(target=schedule_scraper)
scheduler_thread.start()

@app.route('/api/scrape', methods=['GET'])
def trigger_scrape():
    return jsonify(run_scraper())

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000) 