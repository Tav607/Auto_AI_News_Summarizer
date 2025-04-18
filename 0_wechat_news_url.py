#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import sqlite3
import datetime
from pathlib import Path
import argparse

def extract_recent_news_urls(db_path, hours_back=168, output_dir=None):
    """
    Extract news URLs from the database that were published within the specified time range.
    
    Args:
        db_path: Path to the wewe-rss.db SQLite database
        hours_back: Number of hours to look back from 17:00 today
        output_dir: Directory to save the output URLs file, if None, will print to stdout
    """
    # Calculate the target timestamp range
    now = datetime.datetime.now()
    target_time = now.replace(hour=17, minute=0, second=0, microsecond=0)
    
    # If current time is before 17:00, use 17:00 of the previous day
    if now.hour < 17:
        target_time = target_time - datetime.timedelta(days=1)
    
    start_time = target_time - datetime.timedelta(hours=hours_back)
    
    # Convert to Unix timestamp (seconds since epoch)
    start_timestamp = int(start_time.timestamp())
    end_timestamp = int(target_time.timestamp())
    
    print(f"Extracting articles from {start_time} to {target_time}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Query the database for articles in the specified time range
    cursor.execute(
        "SELECT id, publish_time FROM articles WHERE publish_time >= ? AND publish_time <= ? ORDER BY publish_time DESC",
        (start_timestamp, end_timestamp)
    )
    
    articles = cursor.fetchall()
    conn.close()
    
    # Format URLs and create list of (url, publish_date) tuples
    urls = [(f"https://mp.weixin.qq.com/s/{article_id}", datetime.datetime.fromtimestamp(timestamp)) 
            for article_id, timestamp in articles]
    
    # Sort by publish time (newest first)
    urls.sort(key=lambda x: x[1], reverse=True)
    
    # Extract just the URLs
    url_list = [url for url, _ in urls]
    
    # Output results
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        current_date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"wechat_news_urls_{current_date}.txt")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for url in url_list:
                f.write(f"{url}\n")
        print(f"Extracted {len(url_list)} URLs and saved to {output_file}")
    else:
        for url in url_list:
            print(url)
        print(f"Extracted {len(url_list)} URLs")
    
    return url_list

if __name__ == "__main__":
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.parent
    # Set database path relative to script directory
    db_path = str(script_dir / "wewe-rss-data" / "wewe-rss.db")
    
    # Default output directory is 'url' folder in script's directory
    default_output_dir = str(Path(__file__).parent / "url")

    # Set up argument parser
    parser = argparse.ArgumentParser(description='Extract recent WeChat news URLs.')
    parser.add_argument('--hours', type=int, default=168, 
                        help='Number of hours to look back (default: 168)')
    parser.add_argument('--output-dir', type=str, default=default_output_dir, 
                        help=f'Directory to save the output file (default: {default_output_dir})')
    
    args = parser.parse_args()
    
    # Extract URLs using parsed arguments
    extract_recent_news_urls(db_path, hours_back=args.hours, output_dir=args.output_dir) 