#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import pandas as pd
import time
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException, StaleElementReferenceException
from bs4 import BeautifulSoup
import re
from pathlib import Path

def setup_chrome_driver(headless=True):
    """
    设置Chrome WebDriver
    
    参数:
        headless: 是否使用无头模式
        
    返回:
        配置好的WebDriver实例
    """
    chrome_options = Options()
    
    # 基本设置 
    if headless:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument('--ignore-certificate-errors')
    
    # 性能优化设置
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-browser-side-navigation')
    chrome_options.add_argument('--disable-features=TranslateUI')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--blink-settings=imagesEnabled=false')  # 禁用图片加载
    
    # 明确指定ChromeDriver路径
    chromedriver_path = "/usr/local/bin/chromedriver"
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # 设置页面加载超时
    driver.set_page_load_timeout(30)
    
    return driver

def generate_filename_from_url(url):
    """
    从URL生成唯一的文件名
    
    参数:
        url: 文章URL
        
    返回:
        生成的文件名（不含扩展名）
    """
    # 移除URL末尾的斜杠
    url = url.rstrip('/')
    
    # 对于TechCrunch URL，使用完整路径的最后一部分
    if "techcrunch.com" in url:
        # 例如：https://techcrunch.com/2025/04/07/ibm-releases-a-new-mainframe-built-for-the-age-of-ai/
        # 返回：ibm-releases-a-new-mainframe-built-for-the-age-of-ai
        parts = url.split('/')
        if len(parts) > 4:
            return parts[-1]
        else:
            # 如果URL结构不符合预期，使用域名和时间戳
            import hashlib
            return f"techcrunch_{hashlib.md5(url.encode()).hexdigest()[:10]}"
    
    # 对于微信文章URL，提取s参数
    elif "mp.weixin.qq.com" in url:
        # 例如：https://mp.weixin.qq.com/s/FpisxJQ9AXHV26lHPwzy5A
        if "/s/" in url:
            return url.split('/s/')[-1]
        else:
            # 对于格式如 https://mp.weixin.qq.com/s?__biz=xxx&mid=xxx&idx=xxx
            import hashlib
            return f"wechat_{hashlib.md5(url.encode()).hexdigest()[:10]}"
    
    # 对于其他URL，使用MD5哈希的前10位字符
    else:
        import hashlib
        return f"article_{hashlib.md5(url.encode()).hexdigest()[:10]}"

def scrape_article(url, output_path, progress_callback=None):
    """
    使用Selenium抓取文章内容并保存为文本文件（包含重试和资源清理）
    
    参数:
        url: 要抓取的文章URL
        output_path: 保存文章内容的文件路径
        progress_callback: 进度回调函数
        
    返回:
        成功则返回True，失败则返回False
    """
    MAX_RETRIES = 3 # Use a loop with max retries instead of recursion
    retry_count = 0
    
    # 跳过已经存在的文件
    if os.path.exists(output_path):
        # 检查文件是否包含错误信息
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read(1000)  # 只读取前1000个字符
                if "环境异常" in content or "完成验证后即可继续访问" in content:
                    message = f"文件包含错误信息，将重新抓取: {output_path}"
                    print(message)
                    if progress_callback:
                        progress_callback(message)
                    # 不删除文件，继续处理
                else:
                    message = f"文件已存在且内容正常，跳过: {output_path}"
                    print(message)
                    if progress_callback:
                        progress_callback(message)
                    return True
        except Exception as e:
            message = f"检查文件时出错: {output_path}, 错误: {str(e)}"
            print(message)
            if progress_callback:
                progress_callback(message)
    
    while retry_count < MAX_RETRIES:
        driver = None # Initialize driver to None for the finally block
        try:
            # Create driver *inside* the loop for each attempt
            driver = setup_chrome_driver()
            
            # 根据网站类型设置不同的加载策略
            if "techcrunch.com" in url:
                # 对TechCrunch使用快速加载策略
                driver.execute_cdp_cmd('Network.setBlockedURLs', {"urls": [
                    "*google-analytics.com*", "*googletagmanager.com*", 
                    "*doubleclick.net*", "*facebook.net*", "*twitter.com*",
                    "*.jpg", "*.jpeg", "*.png", "*.gif", "*.svg"
                ]})
                driver.execute_cdp_cmd('Network.enable', {})
            
            # 访问网页
            driver.get(url)
            
            # 根据不同网站设置不同的等待时间
            if "weixin.qq.com" in url or "mp.weixin.qq.com" in url:
                # 使用 WebDriverWait 处理微信验证
                wait = WebDriverWait(driver, 10)  # 等待最多10秒
                verify_button_id = 'js_verify'
                verification_message_xpath = "//*[contains(text(), '完成验证后即可继续访问') or contains(text(), '环境异常')]"
                main_content_id = 'js_content' # Assuming this is the main content div ID after verification

                verification_needed = False
                try:
                    # Check if verification prompt is present within timeout
                    wait.until(EC.presence_of_element_located((By.XPATH, verification_message_xpath)))
                    verification_needed = True
                    message = f"检测到微信验证 (URL: {url})..."
                    print(message)
                    if progress_callback: progress_callback(message)
                except TimeoutException:
                    # No verification prompt found, assume page is loaded or doesn't need it
                    message = f"未在10秒内检测到微信验证提示 (URL: {url})"
                    print(message)
                    if progress_callback: progress_callback(message)
                    verification_needed = False

                if verification_needed:
                    try:
                        # Wait for the button to be clickable
                        verify_button = wait.until(EC.element_to_be_clickable((By.ID, verify_button_id)))

                        # Try standard click first
                        try:
                            verify_button.click()
                            message = f"点击了验证按钮 (URL: {url}), 等待文章加载..."
                            print(message)
                            if progress_callback: progress_callback(message)
                        except ElementClickInterceptedException:
                            message = f"常规点击被拦截 (URL: {url}), 尝试JavaScript点击..."
                            print(message)
                            if progress_callback: progress_callback(message)
                            driver.execute_script("arguments[0].click();", verify_button)
                            message = f"JavaScript点击了验证按钮 (URL: {url}), 等待文章加载..."
                            print(message)
                            if progress_callback: progress_callback(message)

                        # Wait for main content to appear after click
                        wait.until(EC.presence_of_element_located((By.ID, main_content_id)))
                        message = f"验证成功 (URL: {url}), 文章已加载。"
                        print(message)
                        if progress_callback: progress_callback(message)

                    except TimeoutException:
                        raise Exception(f"验证按钮未在10秒内可点击或点击后内容未加载 (URL: {url})") # Raise exception to trigger retry
                    except (NoSuchElementException, StaleElementReferenceException) as click_e:
                        raise Exception(f"查找或点击验证按钮时出错 (URL: {url}): {click_e}") # Raise exception
                    except Exception as general_click_e:
                        raise Exception(f"处理验证点击时发生未知错误 (URL: {url}): {general_click_e}") # Raise exception

                else: # No verification needed, check if content loaded anyway
                    try:
                        driver.find_element(By.ID, main_content_id)
                        message = f"检测到主要内容 (URL: {url}), 继续处理。"
                        print(message)
                        if progress_callback: progress_callback(message)
                    except NoSuchElementException:
                        # If no verification and no content, page might have failed silently
                        raise Exception(f"未检测到验证提示，也未检测到主要内容 (URL: {url}), 可能加载失败。")

            elif "techcrunch.com" in url:
                # TechCrunch只需要较短的加载时间，这里使用1秒
                time.sleep(1)
            else:
                # 其他网站使用默认等待时间
                time.sleep(2)
            
            # 获取页面内容
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # 根据不同网站抓取不同内容
            if "techcrunch.com" in url:
                # TechCrunch文章内容提取 - 使用更直接的方法
                article_text = ""
                
                # 获取文章标题 - 尝试更通用的选择器
                title_element = soup.select_one("h1")
                if title_element:
                    article_text += title_element.get_text().strip() + "\n\n"
                
                # 添加固定作者信息
                article_text += "作者：TechCrunch\n"
                
                # 从URL中提取日期
                try:
                    # 解析URL中的日期 - 例如: https://techcrunch.com/2023/04/07/some-article-title/
                    url_parts = url.split('.com/')
                    if len(url_parts) > 1:
                        path_parts = url_parts[1].strip('/').split('/')
                        # 通常日期格式是 yyyy/mm/dd
                        if len(path_parts) >= 3 and path_parts[0].isdigit() and path_parts[1].isdigit() and path_parts[2].isdigit():
                            year = path_parts[0]
                            month = path_parts[1]
                            day = path_parts[2]
                            date_str = f"{year}年{month}月{day}日"
                            article_text += f"日期：{date_str}\n\n"
                        else:
                            # 如果URL中没有日期，添加一个空行
                            article_text += "\n"
                    else:
                        article_text += "\n"
                except Exception as e:
                    # 如果解析日期出错，添加一个空行
                    article_text += "\n"
                
                # 直接提取所有段落，不使用复杂的选择器层次
                content_paragraphs = soup.select("article p")
                
                # 如果找不到段落，尝试使用更通用的选择器
                if not content_paragraphs:
                    content_paragraphs = soup.select(".article-content p, .entry-content p")
                
                # 添加段落内容
                for p in content_paragraphs:
                    p_text = p.get_text().strip()
                    if p_text and len(p_text) > 5:  # 避免空段落和太短的内容
                        article_text += p_text + "\n\n"
                
                text_content = article_text.strip()
            
            elif "mp.weixin.qq.com" in url or "weixin.qq.com" in url:
                # 微信文章内容提取
                article_text = ""
                
                # 获取文章标题 - 基于notepad结构
                title_element = soup.select_one("h1.rich_media_title, #activity-name")
                if title_element:
                    article_text += title_element.get_text().strip() + "\n\n"
                
                # 获取文章作者和日期
                author_element = soup.select_one(".rich_media_meta_nickname, #js_name")
                
                # 更新日期提取逻辑，优先使用publish_time
                date_element = soup.select_one("#publish_time")
                if not date_element or not date_element.get_text().strip():
                    # 尝试其他可能的日期选择器
                    date_element = soup.select_one(".rich_media_meta.rich_media_meta_text:not(.rich_media_meta_nickname)")
                
                if author_element:
                    article_text += f"作者: {author_element.get_text().strip()}\n"
                
                if date_element and date_element.get_text().strip():
                    article_text += f"日期: {date_element.get_text().strip()}\n\n"
                
                # 获取文章内容
                content_element = soup.select_one("#js_content, .rich_media_content")
                if content_element:
                    # 获取所有段落和节
                    paragraphs = content_element.select("p, section")
                    
                    # 用于存储已添加的段落内容，防止重复
                    added_content = set()
                    
                    for p in paragraphs:
                        # 忽略只包含图片的段落
                        if p.find('img') and len(p.get_text().strip()) < 5:
                            continue
                        
                        p_text = p.get_text().strip()
                        # 过滤掉短文本并且避免重复内容
                        if p_text and len(p_text) > 5 and p_text not in added_content:
                            article_text += p_text + "\n\n"
                            added_content.add(p_text)
                
                text_content = article_text.strip()
                
                # 如果内容太短，可能是提取失败，尝试使用正则表达式直接从源码提取
                if len(text_content) < 200:
                    try:
                        # 尝试直接获取内容区域的HTML
                        match = re.search(r'<div class="rich_media_content[^>]*>(.*?)</div>', page_source, re.DOTALL)
                        if match:
                            content_html = match.group(1)
                            content_soup = BeautifulSoup(content_html, 'html.parser')
                            # 移除所有脚本和样式
                            for script in content_soup(["script", "style"]):
                                script.decompose()
                            # 获取文本
                            backup_text = content_soup.get_text(separator='\n\n', strip=True)
                            if len(backup_text) > len(text_content):
                                text_content = backup_text
                    except Exception as e:
                        pass
            else:
                # 对于其他网站，使用通用方法
                # 提取文本内容
                text_content = soup.get_text()
                # 删除多余的空行
                text_content = re.sub(r'\n{3,}', '\n\n', text_content)
            
            # 检查是否仍然存在验证页面
            if "环境异常" in text_content and "完成验证后即可继续访问" in text_content:
                raise Exception(f"无法绕过验证页面，抓取失败 (URL: {url})") # Raise exception to trigger retry
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 添加URL到文章内容的最前面
            final_content = f"{url}\n\n{text_content}"
            
            # 保存内容到文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
            
            message = f"成功保存文章: {url} -> {output_path}"
            print(message)
            if progress_callback:
                progress_callback(message)
            
            return True # Success! Exit loop and function.

        except Exception as e:
            retry_count += 1
            error_message = f"抓取文章出错 {url} (尝试 {retry_count}/{MAX_RETRIES}): {str(e)}"
            print(error_message)
            if progress_callback:
                progress_callback(error_message)
            
            if retry_count >= MAX_RETRIES:
                final_error_message = f"已达到最大重试次数，放弃处理此URL: {url}"
                print(final_error_message)
                if progress_callback:
                    progress_callback(final_error_message)
                return False # Failed after retries
            else:
                # Wait a bit before the next attempt in the loop
                time.sleep(3 * retry_count) # Exponential backoff (3s, 6s)

        finally:
            # !!! Crucial: Ensure driver is always quit !!!
            if driver:
                try:
                    driver.quit()
                except Exception as quit_e:
                    print(f"尝试关闭WebDriver时出错 for {url} (尝试 {retry_count}/{MAX_RETRIES}): {quit_e}")
                    # Log error but continue, the main error is already captured

    # This part should ideally not be reached if logic is correct,
    # but acts as a final fallback return if the loop finishes unexpectedly.
    return False

def main(input_txt, output_dir=None, progress_callback=None):
    """
    从input_txt文件读取URL列表，使用Selenium抓取每个URL的文章内容
    
    参数:
        input_txt: 包含URL列表的输入文件
        output_dir: 保存抓取文章内容的目录
        progress_callback: 进度回调函数
    
    返回:
        包含成功抓取的文章路径列表的文件路径
    """
    # 如果未指定输出目录，则使用默认路径
    if output_dir is None:
        script_dir = Path(__file__).parent
        output_dir = script_dir / "article_content"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = output_dir / f"articles_{timestamp}"
    
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 读取包含URL的文件
    if not os.path.exists(input_txt):
        message = f"输入文件 {input_txt} 不存在！"
        print(message)
        if progress_callback:
            progress_callback(message)
        sys.exit(1)

    with open(input_txt, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]
    
    total_urls = len(urls)
    
    # 创建一个文件来记录成功抓取的文章路径
    success_file = os.path.join(output_dir, "successful_articles.txt")
    
    # 固定max_workers
    max_workers = 2  # 减少并发数量以避免被反爬 (Changed from 5)
    batch_size = max_workers
    total_batches = math.ceil(total_urls / batch_size)
    
    message = f"\n开始抓取文章，共{total_urls}个URL，分{total_batches}批进行（每批{batch_size}个）...\n"
    print(message)
    if progress_callback:
        progress_callback(message)
    
    successful_articles = []
    
    # 并行抓取文章
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for batch in range(total_batches):
            start_idx = batch * batch_size
            end_idx = min((batch + 1) * batch_size, total_urls)
            batch_urls = urls[start_idx:end_idx]
            current_batch_size = len(batch_urls)
            remaining_batches = total_batches - batch - 1
            
            message = f"正在处理第{batch+1}批，共{current_batch_size}个URL，还剩{remaining_batches}批"
            print(message)
            if progress_callback:
                progress_callback(message)
            
            future_to_url = {}
            for i, url in enumerate(batch_urls):
                # 从URL生成文件名
                url_id = generate_filename_from_url(url)
                article_path = os.path.join(output_dir, f"{url_id}.txt")
                
                future = executor.submit(
                    scrape_article,
                    url,
                    article_path,
                    progress_callback
                )
                future_to_url[future] = (url, article_path)
            
            for future in as_completed(future_to_url):
                url, article_path = future_to_url[future]
                try:
                    success = future.result()
                    if success:
                        successful_articles.append(article_path)
                except Exception as e:
                    error_message = f"处理URL时发生错误: {url}, 错误: {e}"
                    print(error_message)
                    if progress_callback:
                        progress_callback(error_message)
            
            # 每一批处理完后暂停一下，避免被反爬
            time.sleep(5)
            
            batch_complete_message = f"第{batch+1}批处理完成"
            print(batch_complete_message)
            if progress_callback:
                progress_callback(batch_complete_message)
    
    # 保存成功抓取的文章路径
    with open(success_file, "w", encoding="utf-8") as f:
        for article_path in successful_articles:
            f.write(f"{article_path}\n")
    
    completion_message = f"\n全部抓取完成，成功抓取 {len(successful_articles)}/{total_urls} 个文章\n"
    completion_message += f"成功抓取的文章列表已保存至: {success_file}"
    print(completion_message)
    if progress_callback:
        progress_callback(completion_message)
    
    return success_file

if __name__ == "__main__":
    """
    命令行用法示例:
        python 1a_url_to_article.py input_urls.txt [output_directory]
        
    如果不指定输出目录，则使用默认路径和文件名：./article_content/articles_yyyymmdd_hhmmss/
    """
    if len(sys.argv) < 2:
        print("用法示例: python 1a_url_to_article.py input_urls.txt [output_directory]")
        print("如果不指定输出目录，则使用默认路径和文件名：./article_content/articles_yyyymmdd_hhmmss/")
        sys.exit(1)

    input_txt_path = sys.argv[1]
    output_dir_path = sys.argv[2] if len(sys.argv) > 2 else None
    main(input_txt_path, output_dir_path) 