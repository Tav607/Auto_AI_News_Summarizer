# AI News Summary Tool

This tool automatically extracts AI-related articles from a FreshRSS SQLite database, generates article abstracts, compiles a weekly summary, and outputs Markdown and PDF documents.

## Features

- Extract AI news articles from a FreshRSS SQLite database
- Generate individual article abstracts in Markdown
- Merge abstracts to produce a weekly summary Markdown file
- Convert Markdown documents to PDF
- Support parallel processing for improved performance

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

Create a `.env` file in the project root with the following content:

```dotenv
# Path to the FreshRSS SQLite database file
DB_PATH=/path/to/freshrss.db

# Volcengine service configuration (for abstract generation)
Volcengine_API_KEY="YOUR_VOLCENGINE_API_KEY"
Volcengine_MODEL_ID="YOUR_VOLCENGINE_MODEL_ID"
Volcengine_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"

# Google service configuration (for weekly summary)
Google_API_KEY="YOUR_GOOGLE_API_KEY"
Google_MODEL_ID="YOUR_GOOGLE_MODEL_ID"
Google_BASE_URL="https://generativelanguage.googleapis.com/v1beta/models/"
```

Ensure the environment variables are correctly set before running any script.

## Project Structure

```
.
├── 0_sqlite_to_articles.py         # Extract articles from FreshRSS database
├── 1_article_to_abstract_md.py     # Generate article abstracts in Markdown
├── 2_abstract_to_summary.py        # Compile abstracts into a weekly summary
├── 3_md_to_pdf.py                  # Convert Markdown to PDF
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
./run.sh --db <DB_PATH> [--hours <hours>] [--end-hour <end_hour>]
```

## Notes

- Ensure all required environment variables are set in the `.env` file.
- Processing a large number of articles may take some time.
- Comply with website terms of service when crawling or extracting content.