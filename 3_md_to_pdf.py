#!/usr/bin/env python3
import sys
import os
import subprocess
import tempfile
import markdown
import re # Import re module for regex replacement

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
                    margin: 2em;
                    font-size: 16px; /* Base font size */
                }}
                h1, h2, h3, h4, h5, h6 {{
                    color: #333;
                }}
                h1 {{
                    font-size: 28px; /* h1 = h2 + 4px */
                    color: #385D4E; /* Custom color for h1 */
                }}
                 h2 {{
                    font-size: 24px; /* h2 = h3 + 6px */
                    color: #385D4E; /* Custom color for h2 */
                }}
                 h3 {{
                    font-size: 18px; /* Base size for h3 */
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
        
        # Create a temporary HTML file
        # Use 'w+' mode and explicitly encode to utf-8
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.html', delete=False, encoding='utf-8') as temp_html:
            temp_html_path = temp_html.name
            temp_html.write(styled_html) # Write the string directly
        
        # Convert HTML to PDF using wkhtmltopdf
        # Add --enable-local-file-access flag if needed for local resources like images
        cmd = ['wkhtmltopdf', '--enable-local-file-access', temp_html_path, pdf_file]
        result = subprocess.run(cmd, check=False, capture_output=True, text=True) # Capture output

        if result.returncode != 0:
             print(f"wkhtmltopdf error (return code {result.returncode}):")
             print(result.stderr)
             # Optionally print stdout as well if it contains useful info
             # print(result.stdout)
             # Attempt to clean up temp file even on error
             if os.path.exists(temp_html_path):
                 os.unlink(temp_html_path)
             return False
        
        # Remove temporary HTML file only on success
        os.unlink(temp_html_path)
        
        print(f"Successfully converted '{md_file}' to '{pdf_file}'")
        return True
    
    except Exception as e:
        print(f"Error converting file: {e}")
        # Attempt to clean up temp file if it exists and an exception occurred
        if 'temp_html_path' in locals() and os.path.exists(temp_html_path):
             os.unlink(temp_html_path)
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python 3_md_to_pdf.py <markdown_file>")
        sys.exit(1)
    
    md_file = sys.argv[1]
    success = md_to_pdf(md_file)
    sys.exit(0 if success else 1) 