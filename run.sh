#!/usr/bin/env bash
set -e

# Usage message
print_usage() { echo "Usage: $0 --db <DB_PATH> [--hours <hours>] [--end-hour <end_hour>]"; exit 1; }

# Default parameters
DB_PATH="${DB_PATH:-$(grep DB_PATH .env | cut -d '=' -f2)}"
HOURS=168
END_HOUR=18

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --db) DB_PATH="$2"; shift 2;;
        --hours) HOURS="$2"; shift 2;;
        --end-hour) END_HOUR="$2"; shift 2;;
        -h|--help) print_usage;;
        *) echo "Unknown option: $1"; print_usage;;
    esac
done

# Check mandatory DB_PATH
if [[ -z "$DB_PATH" ]]; then
    echo "Error: --db <DB_PATH> is required."
    print_usage
fi

# Change to script directory
cd "$(dirname "$0")"

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Step 1: Extracting articles from DB..."
python 0_sqlite_to_articles.py --db "$DB_PATH" --hours "$HOURS" --end-hour "$END_HOUR"
# Determine the output directory created by the Python script based on timestamp
OUTPUT_DIR=$(ls -td articles/articles_* | head -n 1)
ARTICLES_LIST="$OUTPUT_DIR/successful_articles.txt"
if [[ ! -f "$ARTICLES_LIST" ]]; then
    echo "Error: Article list file not found at $ARTICLES_LIST"
    exit 1
fi
echo "Articles list: $ARTICLES_LIST"

echo "Step 2: Generating abstracts..."
python 1_article_to_abstract_md.py "$ARTICLES_LIST"
ABSTRACT_MD_FILE=$(ls -t abstract_md/abstract_md_*.md | head -n 1)
if [[ ! -f "$ABSTRACT_MD_FILE" ]]; then
    echo "Error: Abstract markdown file not found."
    exit 1
fi
echo "Abstract markdown: $ABSTRACT_MD_FILE"

echo "Step 3: Generating final summary..."
python 2_abstract_to_summary.py --input-md "$ABSTRACT_MD_FILE"
SUMMARY_MD=$(ls -t deliverable/"AI News Update "*.md 2>/dev/null | head -n 1)
if [[ -z "$SUMMARY_MD" ]]; then
    echo "Error: Summary markdown file not found."
    exit 1
fi
echo "Summary markdown: $SUMMARY_MD"

echo "Step 4: Converting summary to PDF..."
python 3_md_to_pdf.py "$SUMMARY_MD"
PDF_FILE="${SUMMARY_MD%.md}.pdf"
if [[ ! -f "$PDF_FILE" ]]; then
    echo "Error: PDF file not created."
    exit 1
fi
echo "PDF file: $PDF_FILE"

echo "Pipeline completed successfully!"

echo "Deactivating virtual environment..."
deactivate 