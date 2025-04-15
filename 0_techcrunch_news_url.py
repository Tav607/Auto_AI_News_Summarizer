import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import re
import os
import argparse

def get_article_urls_from_page(url, days=7):
    """
    Extract article URLs and dates from a TechCrunch category page
    返回格式: [(url, date, is_within_date_range)]
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        article_count = 0
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Look for main article containers on TechCrunch
        articles = soup.select('div.post-block')
        
        if not articles:
            articles = soup.select('article')
            
        if articles:
            print(f"Found {len(articles)} article containers")
            for article in articles:
                article_count += 1
                
                # Find the article URL
                link = None
                
                # First try to find the title link
                title_link = article.select_one('h2 a, h3 a, h4 a')
                if title_link and title_link.has_attr('href'):
                    link = title_link['href']
                
                # If no title link, try any links in the article
                if not link:
                    for a_tag in article.select('a[href]'):
                        href = a_tag.get('href', '')
                        # Simple heuristic to identify article links
                        if ('/2025/' in href or '/2024/' in href) and '/category/' not in href and '/tag/' not in href:
                            link = href
                            break
                
                if not link or '/category/' in link or '/tag/' in link:
                    continue
                
                # Determine the article date
                article_date = None
                is_within_range = True
                
                # Try to find a date in the article element
                time_tag = article.select_one('time[datetime]')
                if time_tag and time_tag.has_attr('datetime'):
                    try:
                        date_str = time_tag['datetime']
                        if 'T' in date_str:
                            article_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    except Exception as e:
                        print(f"Date parsing error for time tag: {e}")
                
                # If we couldn't get a date from time tag, try to extract from URL
                if not article_date and (('/2025/' in link) or ('/2024/' in link)):
                    try:
                        # Extract YYYY/MM/DD pattern from URL
                        date_match = re.search(r'/(\d{4}/\d{2}/\d{2})/', link)
                        if date_match:
                            date_str = date_match.group(1).replace('/', '-')
                            article_date = datetime.strptime(date_str, '%Y-%m-%d')
                    except Exception as e:
                        print(f"Date parsing error from URL: {e}")
                
                # For special URL patterns like tech-layoffs list that might be regularly updated 
                # but have a fixed date in URL, we need special handling
                if '/tech-layoffs' in link and article_date:
                    print(f"Warning: Found special URL pattern that might be updated regularly: {link}")
                    # If we can't determine last update date, we'll be conservative
                    if article_date < cutoff_date:
                        print(f"Old date for special URL: {link} - {article_date.strftime('%Y-%m-%d')}")
                        is_within_range = False
                
                # 检查URL中的日期字段是否超出指定天数范围
                url_date_match = re.search(r'/(\d{4}/\d{2}/\d{2})/', link)
                if url_date_match:
                    try:
                        url_date_str = url_date_match.group(1).replace('/', '-')
                        url_date = datetime.strptime(url_date_str, '%Y-%m-%d')
                        article_date = url_date  # 使用URL日期作为文章日期
                        
                        # 检查是否在日期范围内，但不跳过，而是标记
                        if url_date < cutoff_date:
                            is_within_range = False
                            print(f"Old article by URL date: {link} - {url_date.strftime('%Y-%m-%d')}")
                    except Exception as e:
                        print(f"Error parsing date from URL: {e}")
                
                # For debugging: print the article URL and date
                if article_count <= 5:
                    date_display = article_date.strftime('%Y-%m-%d') if article_date else 'unknown date'
                    in_range_text = "✓" if is_within_range else "✗"
                    print(f"Article {article_count}: {link} - {date_display} {in_range_text}")
                
                # 添加到结果中，包括日期范围标记
                results.append((link, article_date, is_within_range))
        else:
            # Last resort: look for article links directly
            for link in soup.select('a[href*="/2025/"], a[href*="/2024/"]'):
                href = link.get('href', '')
                if '/category/' in href or '/tag/' in href or href.endswith('/page/'):
                    continue
                
                # Try to extract date from URL
                article_date = None
                is_within_range = True
                
                try:
                    date_match = re.search(r'/(\d{4}/\d{2}/\d{2})/', href)
                    if date_match:
                        date_str = date_match.group(1).replace('/', '-')
                        article_date = datetime.strptime(date_str, '%Y-%m-%d')
                        
                        # 检查是否在日期范围内，但不跳过，而是标记
                        if article_date < cutoff_date:
                            is_within_range = False
                            print(f"Old article by URL date: {href} - {article_date.strftime('%Y-%m-%d')}")
                except Exception:
                    pass
                
                # 添加到结果中，包括日期范围标记
                results.append((href, article_date, is_within_range))
        
        # Deduplicate results by URL
        unique_urls = {}
        filtered_results = []
        for url, date, is_within_range in results:
            if url not in unique_urls:
                unique_urls[url] = (date, is_within_range)
                filtered_results.append((url, date, is_within_range))
        
        print(f"Found {len(filtered_results)} unique articles on page (from {article_count} article elements)")
        return filtered_results
    
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []

def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Scrape TechCrunch AI articles')
    parser.add_argument('--days', type=int, default=7,
                      help='Number of days to look back (default: 7)')
    parser.add_argument('--max-pages', type=int, default=20,
                      help='Maximum number of pages to scrape (default: 20)')
    args = parser.parse_args()

    base_url = "https://techcrunch.com/category/artificial-intelligence"
    
    # Create url directory if it doesn't exist
    url_dir = "url"
    if not os.path.exists(url_dir):
        os.makedirs(url_dir)
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(url_dir, f"techcrunch_news_urls_{timestamp}.txt")
    
    # Calculate date range based on command line argument
    current_date = datetime.now()
    days_ago = current_date - timedelta(days=args.days)
    
    print(f"当前日期: {current_date.strftime('%Y-%m-%d')}")
    print(f"{args.days}天前日期: {days_ago.strftime('%Y-%m-%d')}")
    print(f"抓取 {days_ago.strftime('%Y-%m-%d')} 之后的文章")
    print(f"最大抓取页数: {args.max_pages}")
    
    all_articles = []
    current_page = 1
    old_article_threshold = 10  # 如果一页中有超过这个数量的旧文章，考虑停止
    consecutive_old_pages = 0  # 连续包含大量旧文章的页面数
    
    # Process all pages and check dates for each article
    while current_page <= args.max_pages:
        # Construct page URL
        page_url = base_url if current_page == 1 else f"{base_url}/page/{current_page}/"
        
        print(f"\nScraping page {current_page}: {page_url}")
        
        # Get articles from the current page
        articles = get_article_urls_from_page(page_url, args.days)
        
        if not articles:
            print(f"No articles found on page {current_page}, stopping")
            break
        
        # 统计该页面上旧文章和新文章的数量
        recent_count = 0
        old_count = 0
        
        # 处理该页的所有文章
        for article_url, article_date, is_within_range in articles:
            if is_within_range:
                recent_count += 1
                # 添加到总结果中 - 只包含日期符合要求的文章
                if article_date:  # 确保文章有日期
                    all_articles.append((article_url, article_date))
            else:
                old_count += 1
        
        # 计算旧文章比例
        old_article_ratio = old_count / len(articles) if articles else 0
        print(f"在第{current_page}页找到{old_count}/{len(articles)}篇URL中日期超出{args.days}天的文章 (比例: {old_article_ratio:.2f})")
        
        # 停止抓取的条件:
        # 1. 如果超过50%的文章都是旧的，并且已经至少抓取了2页，则停止
        # 2. 如果连续2页都有超过阈值的旧文章，则停止
        if (old_article_ratio > 0.5 and current_page >= 2) or (old_count >= old_article_threshold):
            consecutive_old_pages += 1
            print(f"检测到大量旧文章 (连续{consecutive_old_pages}页)")
            
            if consecutive_old_pages >= 2:
                print("连续多页发现大量旧文章，停止抓取")
                break
        else:
            consecutive_old_pages = 0
        
        print(f"Page {current_page} summary:")
        print(f"- Recent articles (within {args.days} days): {recent_count}")
        print(f"- Old articles (based on date): {old_count}")
        
        # 如果当前页面几乎没有新文章，则停止抓取
        if recent_count == 0 and current_page > 1:
            print("当前页面没有符合日期条件的文章，停止抓取")
            break
        
        current_page += 1
        time.sleep(2)  # Be nice to the server
    
    # 如果达到最大页面限制，输出提示
    if current_page > args.max_pages:
        print(f"达到最大页面限制 ({args.max_pages})，停止抓取")
    
    # 确保所有的URL没有重复
    unique_urls = {}
    for url, date in all_articles:
        # 确保URL是绝对URL
        if not url.startswith('http'):
            url = f"https://techcrunch.com{url}"
            
        # 如果URL已存在但日期更新，或URL不存在，添加/更新
        if url not in unique_urls or date > unique_urls[url]:
            unique_urls[url] = date
    
    # 转换回列表并排序
    unique_articles = [(url, date) for url, date in unique_urls.items()]
    unique_articles.sort(key=lambda x: x[1], reverse=True)
    
    # Write results to file
    with open(output_file, 'w', encoding='utf-8') as f:
        for article_url, article_date in unique_articles:
            f.write(f"{article_url}\n")
    
    print(f"\nScraping completed. Found {len(unique_articles)} unique articles within the last {args.days} days.")
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    main() 