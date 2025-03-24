#!/usr/bin/env python3
import sys
import os
import subprocess
import tempfile
import markdown

def md_to_pdf(md_file):
    # Check if input file exists
    if not os.path.exists(md_file):
        print(f"Error: File '{md_file}' not found.")
        return False
    
    # Get the base name without extension for output file
    base_name = os.path.splitext(md_file)[0]
    pdf_file = f"{base_name}.pdf"
    
    try:
        # Read markdown content
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Convert markdown to HTML
        html_content = markdown.markdown(md_content, extensions=['extra', 'codehilite'])
        
        # Add basic styling
        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{os.path.basename(base_name)}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 2em;
                }}
                h1, h2, h3, h4, h5, h6 {{
                    color: #333;
                }}
                code {{
                    background-color: #f5f5f5;
                    padding: 2px 4px;
                    border-radius: 4px;
                }}
                pre {{
                    background-color: #f5f5f5;
                    padding: 10px;
                    border-radius: 4px;
                    overflow-x: auto;
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
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp_html:
            temp_html_path = temp_html.name
            temp_html.write(styled_html.encode('utf-8'))
        
        # Convert HTML to PDF using wkhtmltopdf
        cmd = ['wkhtmltopdf', temp_html_path, pdf_file]
        subprocess.run(cmd, check=True)
        
        # Remove temporary HTML file
        os.unlink(temp_html_path)
        
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