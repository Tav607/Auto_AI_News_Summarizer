# AI News Summary Tool

This tool automatically extracts AI-related articles from a FreshRSS SQLite database, generates article abstracts, compiles a weekly summary, and outputs Markdown and PDF documents.

## Features

- Extract AI news articles from a FreshRSS SQLite database
- Generate individual article abstracts in Markdown
- Merge abstracts to produce a weekly summary Markdown file
- Convert Markdown documents to PDF
- Support parallel processing for improved performance
- Automatically upload summary Markdown and PDF files to the root of the Dropbox App folder

## Requirements

- Python 3.7+
- Operating Systems: Windows, macOS, or Linux
- For PDF generation, install the markdown and weasyprint libraries

## Installation

1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd ai_news_summary
   ```
2. Create and activate a virtual environment:
   - Linux/macOS:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - Windows (PowerShell):
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Create a `.env` file in the project root. The `run.sh` script and individual Python scripts will load configurations from this file.

```dotenv
# --- General Configuration ---
# Path to the FreshRSS SQLite database file.
# This is used by `run.sh` and is the primary way to set the DB path.
# `0_sqlite_to_articles.py` will use the --db argument if provided by `run.sh`,
# otherwise, it will fall back to this DB_PATH from the .env file.
DB_PATH=/path/to/freshrss.db

# --- Article Extraction (0_sqlite_to_articles.py) ---
# Comma-separated list of exact feed names to include.
# This is a **MANDATORY** setting. Example: "TechCrunch AI News,Reuters AI News,The Verge - AI"
ALLOWED_FEED_NAMES="YOUR_ALLOWED_FEED_NAMES_HERE"

# Optional: Category ID for WeChat articles (or similar) to be included.
# Defaults to "0" if not set.
WECHAT_CATEGORY_ID="where_you_put_your_wechat_rss"

# Optional: A string that should be present in the URL for WeChat articles (or similar).
# This is used in a LIKE '%value%' SQL clause.
# Defaults to "wechat" if not set.
WECHAT_URL_PATTERN_CONTAINS="wechat2rss_or_other_service_provider"

# --- Volcengine service configuration (for abstract generation) ---
Volcengine_API_KEY="YOUR_VOLCENGINE_API_KEY"
Volcengine_MODEL_ID="YOUR_VOLCENGINE_MODEL_ID"
Volcengine_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"

# Google service configuration (for weekly summary)
Google_API_KEY="YOUR_GOOGLE_API_KEY"
Google_MODEL_ID="YOUR_GOOGLE_MODEL_ID"
Google_BASE_URL="https://generativelanguage.googleapis.com/v1beta/models/"

## --- Dropbox Configuration (for file upload) ---
DROPBOX_ACCESS_TOKEN="YOUR_DROPBOX_APP_ACCESS_TOKEN"
```

Ensure the environment variables are correctly set before running any script.

## Project Structure

```
.
├── 0_sqlite_to_articles.py         # Extract articles from FreshRSS database
├── 1_article_to_abstract_md.py     # Generate article abstracts in Markdown
├── 2_abstract_to_summary.py        # Compile abstracts into a weekly summary
├── 3_md_to_pdf.py                  # Convert Markdown to PDF
├── 4_save_to_dropbox.py            # Upload files to Dropbox
├── run.sh                          # Run the entire pipeline with one command
├── articles/                       # Stores extracted article text files
├── abstract_md/                    # Stores generated abstract Markdown files
├── deliverable/                    # Stores summary Markdown and PDF files
├── system_prompt/                  # Stores AI prompt templates
├── requirements.txt                # Project dependencies
└── README.md                       # Project documentation
```

## Usage

### Run Individual Steps

1. Extract articles (creates `articles/articles_YYYYMMDD_HHMM` directory):
   ```bash
   python 0_sqlite_to_articles.py --db <DB_PATH> [--hours <hours>] [--end-hour <end_hour>]
   ```
2. Generate article abstracts (creates `abstract_md/abstract_md_YYYYMMDD_HHMMSS.md`):
   ```bash
   python 1_article_to_abstract_md.py <articles_list.txt> [--output-md <OUTPUT_MD>]
   ```
3. Generate weekly summary (creates `deliverable/AI News Update YYYY MM DD.md`):
   ```bash
   python 2_abstract_to_summary.py --input-md <ABSTRACT_MD> [--output-md <OUTPUT_MD>]
   ```
4. Convert summary Markdown to PDF:
   ```bash
   python 3_md_to_pdf.py <SUMMARY_MD>
   ```

### Run Full Pipeline

Make the pipeline script executable and run:

```bash
chmod +x run.sh
./run.sh [--db <DB_PATH>] [--hours <hours>] [--end-hour <end_hour>]
```

If `--db` is not provided, the script will attempt to use `DB_PATH` from the `.env` file.

## Notes

- Ensure all required environment variables are set in the `.env` file.
- Processing a large number of articles may take some time.
- Comply with website terms of service when crawling or extracting content.