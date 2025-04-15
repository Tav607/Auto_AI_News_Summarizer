#!/bin/bash

# Set working directory to the script location
cd "$(dirname "$0")"
echo "Starting AI news pipeline..."

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Step 1: Run 0_wechat_news_url.py
echo "Step 1: Fetching WeChat news URLs..."
python 0_wechat_news_url.py
WECHAT_URL_FILE=$(ls -t url/wechat_news_urls_*.txt | head -n 1)
echo "WeChat URLs saved to $WECHAT_URL_FILE"

# Step 2: Run 0_techcrunch_news_url.py
echo "Step 2: Fetching TechCrunch news URLs..."
python 0_techcrunch_news_url.py
TECHCRUNCH_URL_FILE=$(ls -t url/techcrunch_news_urls_*.txt | head -n 1)
echo "TechCrunch URLs saved to $TECHCRUNCH_URL_FILE"

# Step 3: Process WeChat URLs with the updated wrapper script
echo "Step 3: Processing WeChat URLs to abstract markdown..."
python 1_url_to_abstract_md_wrapper.py "$WECHAT_URL_FILE"
# Find the most recent abstract file
WECHAT_MD_FILE=$(ls -t abstract_md/abstract_md_*.md | head -n 1)
echo "WeChat abstracts saved to $WECHAT_MD_FILE"

# Step 4: Process TechCrunch URLs with the updated wrapper script
echo "Step 4: Processing TechCrunch URLs to abstract markdown..."
python 1_url_to_abstract_md_wrapper.py "$TECHCRUNCH_URL_FILE"
# Find the most recent abstract file after processing TechCrunch URLs
# We need to find a different file than the one used for WeChat
LATEST_MD_FILES=$(ls -t abstract_md/abstract_md_*.md | head -n 2)
for file in $LATEST_MD_FILES; do
    if [ "$file" != "$WECHAT_MD_FILE" ]; then
        TECHCRUNCH_MD_FILE="$file"
        break
    fi
done
echo "TechCrunch abstracts saved to $TECHCRUNCH_MD_FILE"

# Step 5: Generate summary from both abstract markdown files
echo "Step 5: Generating combined summary from abstracts..."
# Check if both files exist before proceeding
if [ -f "$WECHAT_MD_FILE" ] && [ -f "$TECHCRUNCH_MD_FILE" ]; then
    python 2_abstract_md_to_summary.py "$WECHAT_MD_FILE" "$TECHCRUNCH_MD_FILE"
    # Find the summary file using the new naming pattern
    SUMMARY_FILE=$(ls -t deliverable/"AI News Update "*.md 2>/dev/null | head -n 1)
    # Check if summary file was found
    if [ -z "$SUMMARY_FILE" ]; then
        echo "Error: Could not find the summary file with pattern 'AI News Update *.md' in deliverable/"
    else
        echo "Summary saved to $SUMMARY_FILE"

        # Step 6: Convert summary markdown to PDF
        echo "Step 6: Converting summary to PDF..."
        python 3_md_to_pdf.py "$SUMMARY_FILE"
        # PDF file is now correctly placed in deliverable by 3_md_to_pdf.py
        # Extract the PDF filename based on the summary filename
        PDF_FILE="$SUMMARY_FILE"
        PDF_FILE="${PDF_FILE%.md}.pdf"
        echo "PDF saved to $PDF_FILE"
    fi # End of check for SUMMARY_FILE
else
    echo "Error: One or both abstract files are missing. Cannot proceed to summary generation."
    echo "WeChat file: $WECHAT_MD_FILE"
    echo "TechCrunch file: $TECHCRUNCH_MD_FILE"
fi

echo "AI news pipeline completed successfully!"

# Deactivate virtual environment
echo "Deactivating virtual environment..."
deactivate 