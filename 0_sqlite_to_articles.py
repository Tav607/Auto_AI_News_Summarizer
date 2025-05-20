#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract and format articles from FreshRSS SQLite DB into individual text files.
Usage:
    python 0_sqlite_to_articles.py [--db <DB_PATH>] [--hours 168] [--end-hour 18]
"""
import os
import sys
import argparse
import sqlite3
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from dotenv import load_dotenv

def parse_args():
    parser = argparse.ArgumentParser(description="Extract and format articles from FreshRSS SQLite DB")
    parser.add_argument("--db", help="Path to FreshRSS SQLite database file (overrides DB_PATH in .env)")
    parser.add_argument("--hours", type=int, default=168, help="Time window in hours (default: 168)")
    parser.add_argument("--end-hour", type=int, default=18, help="End hour of day (0-23) for the window end (default: 18)")
    return parser.parse_args()


def main():
    load_dotenv() # Load environment variables from .env file
    args = parse_args()

    db_path = args.db  # Prioritize command-line argument
    if not db_path:
        db_path = os.getenv("DB_PATH") # Fallback to .env variable

    if not db_path:
        print("Error: Database path not provided. Set --db argument or DB_PATH in .env file.")
        sys.exit(1)

    # Compute window end timestamp: today at end_hour or yesterday if before end_hour
    now = datetime.now()
    if now.hour >= args.end_hour:
        end_dt = now.replace(hour=args.end_hour, minute=0, second=0, microsecond=0)
    else:
        end_dt = (now - timedelta(days=1)).replace(hour=args.end_hour, minute=0, second=0, microsecond=0)
    start_dt = end_dt - timedelta(hours=args.hours)
    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())
    print(f"Extracting entries from {start_dt} to {end_dt} (timestamps {start_ts}-{end_ts})")

    # Validate database file
    if not os.path.exists(db_path):
        print(f"Error: database file '{db_path}' not found.")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Load query conditions from environment variables
    # These are expected to be set in the .env file as they are for customization.
    allowed_feed_names_str = os.getenv("ALLOWED_FEED_NAMES")
    # WECHAT_CATEGORY_ID and WECHAT_URL_PATTERN_CONTAINS are optional with defaults.
    wechat_category_id = os.getenv("WECHAT_CATEGORY_ID", "0")
    wechat_url_pattern = os.getenv("WECHAT_URL_PATTERN_CONTAINS", "wechat")

    missing_vars = []
    if not allowed_feed_names_str: # Checks for None or empty string
        missing_vars.append("ALLOWED_FEED_NAMES")
    # Removed WECHAT_CATEGORY_ID and WECHAT_URL_PATTERN_CONTAINS from mandatory checks

    if missing_vars:
        print(f"Error: The following environment variables must be set and non-empty in the .env file: {', '.join(missing_vars)}")
        sys.exit(1)

    # Process ALLOWED_FEED_NAMES: split, strip, and filter out empty strings
    allowed_feed_names = [name.strip() for name in allowed_feed_names_str.split(',') if name.strip()]

    if not allowed_feed_names:
        print(f"Error: ALLOWED_FEED_NAMES environment variable was set but resulted in an empty list of feed names. Please provide valid, comma-separated feed names.")
        sys.exit(1)

    # Dynamically build the WHERE clause for feed names
    feed_name_conditions = " OR ".join(["f.name = ?"] * len(allowed_feed_names))
    
    query_template = f'''
    SELECT e.link, e.title, e.content, e.date, f.name
    FROM entry e
    JOIN feed f ON e.id_feed = f.id
    WHERE e.date BETWEEN ? AND ?
      AND (
        {feed_name_conditions}
        OR (f.category = ? AND f.url LIKE ?)
      )
    ORDER BY e.date DESC
    '''
    
    params = [start_ts, end_ts] + allowed_feed_names + [wechat_category_id, f'%{wechat_url_pattern}%']
    
    cursor.execute(query_template, tuple(params))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("No entries found in the specified time window.")
        sys.exit(0)

    # Prepare output directory based on current timestamp
    base_dir = "articles"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_dir = os.path.join(base_dir, f"articles_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    list_file = os.path.join(output_dir, "successful_articles.txt")

    # Write each article as a text file and record the path
    with open(list_file, "w", encoding="utf-8") as list_f:
        for idx, (link, title, content, date_val, feed_name) in enumerate(rows, start=1):
            file_name = f"article_{idx}.txt"
            file_path = os.path.join(output_dir, file_name)
            # Clean HTML content
            soup = BeautifulSoup(content or "", "html.parser")
            text = soup.get_text().strip()
            # Format date
            try:
                dt_str = datetime.fromtimestamp(date_val).strftime("%Y年%m月%d日")
            except Exception:
                dt_str = str(date_val)
            # Write file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(link + "\n\n")
                f.write(title + "\n\n")
                f.write(f"{feed_name} {dt_str}" + "\n\n")
                f.write(text)
            list_f.write(file_path + "\n")

    print(f"Extracted {len(rows)} articles. List file: {list_file}")


if __name__ == "__main__":
    main() 