#!/usr/bin/env python3
import sys
import os
import tempfile
import markdown
import re # Import re module for regex replacement
from weasyprint import HTML # Import WeasyPrint

def md_to_pdf(md_file):
    # Check if input file exists
    if not os.path.exists(md_file):
        print(f"Error: File '{md_file}' not found.")
        return False
    
    # Get the base name without extension for output file
    base_name_with_ext = os.path.basename(md_file) # Get filename with extension
    base_name = os.path.splitext(base_name_with_ext)[0] # Get base name
    
    # Define output directory as the same directory where the markdown file resides
    output_dir = os.path.dirname(md_file) 
    # Ensure the directory exists (it should, if the input file exists)
    os.makedirs(output_dir, exist_ok=True)

    # Construct the PDF filename using the base name and place it in the correct output directory
    pdf_file = os.path.join(output_dir, f"{base_name}.pdf")
    
    try:
        # Read markdown content
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # Replace '---' with a page break element before converting to HTML
        # Use regex to handle potential whitespace around '---' and ensure it's on its own line
        md_content_with_breaks = re.sub(r'^---\s*$', r'<div style="page-break-after: always;"></div>', md_content, flags=re.MULTILINE)
        
        # Convert potentially modified markdown to HTML
        html_content = markdown.markdown(md_content_with_breaks, extensions=['extra', 'codehilite'])
        
        # Add custom styling
        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{os.path.basename(base_name)}</title>
            <style>
                body {{
                    font-family: 'Calibri', 'DengXian', sans-serif; /* Use Calibri for English, DengXian for Chinese */
                    line-height: 1.6;
                    margin: 1em;
                    font-size: 14px; /* Base font size */
                }}
                h1, h2, h3, h4, h5, h6 {{
                    color: #333;
                }}
                h1 {{
                    font-size: 24px; /* h1 = h2 + 4px */
                    color: #385D4E; /* Custom color for h1 */
                }}
                 h2 {{
                    font-size: 20px; /* h2 = h3 + 6px */
                    color: #385D4E; /* Custom color for h2 */
                }}
                 h3 {{
                    font-size: 16px; /* Base size for h3 */
                }}
                code {{
                    background-color: #f5f5f5;
                    padding: 2px 4px;
                    border-radius: 4px;
                    font-family: Consolas, monospace; /* Ensure code uses a monospace font */
                }}
                pre {{
                    background-color: #f5f5f5;
                    padding: 10px;
                    border-radius: 4px;
                    overflow-x: auto;
                    font-family: Consolas, monospace; /* Ensure preformatted text uses a monospace font */
                }}
                blockquote {{
                    border-left: 4px solid #ddd;
                    padding-left: 1em;
                    color: #777;
                }}
                img {{
                    max-width: 100%;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                }}
                table, th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # Convert HTML string to PDF using WeasyPrint
        # Use the directory of the markdown file as the base_url to resolve relative paths (e.g., for images)
        html = HTML(string=styled_html, base_url=output_dir)
        html.write_pdf(pdf_file)

        print(f"Successfully converted '{md_file}' to '{pdf_file}'")
        return True
    
    except Exception as e:
        print(f"Error converting file: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python 3_md_to_pdf.py <markdown_file>")
        sys.exit(1)
    
    md_file = sys.argv[1]
    success = md_to_pdf(md_file)
    sys.exit(0 if success else 1) 