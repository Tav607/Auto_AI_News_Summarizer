#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract and format articles from FreshRSS SQLite DB into individual text files.
Usage:
    python 0_sqlite_to_articles.py --db <DB_PATH> [--hours 168] [--end-hour 18]
"""
import os
import sys
import argparse
import sqlite3
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

def parse_args():
    parser = argparse.ArgumentParser(description="Extract and format articles from FreshRSS SQLite DB")
    parser.add_argument("--db", required=True, help="Path to FreshRSS SQLite database file")
    parser.add_argument("--hours", type=int, default=168, help="Time window in hours (default: 168)")
    parser.add_argument("--end-hour", type=int, default=18, help="End hour of day (0-23) for the window end (default: 18)")
    return parser.parse_args()


def main():
    args = parse_args()
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
    if not os.path.exists(args.db):
        print(f"Error: database file '{args.db}' not found.")
        sys.exit(1)

    conn = sqlite3.connect(args.db)
    cursor = conn.cursor()
    query = '''
    SELECT e.link, e.title, e.content, e.date, f.name
    FROM entry e
    JOIN feed f ON e.id_feed = f.id
    WHERE e.date BETWEEN ? AND ?
      AND (
        f.name = 'TechCrunch AI News'
        OR f.name = 'Reuters AI News'
        OR f.name = 'The Verge - AI'
        OR (f.category = 2 AND f.url LIKE '%wechat2rss%')
      )
    ORDER BY e.date DESC
    '''
    cursor.execute(query, (start_ts, end_ts))
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