#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import httpx
import math
import configparser
from datetime import datetime
from dotenv import load_dotenv
import time
from threading import Lock

# 如果你是用 volces-openai-sdk，请安装并导入它
# from openai import OpenAI
# 这里仅作示例:
try:
    from openai import OpenAI
except ImportError:
    print("请先安装相应的 SDK, 例如: pip install openai 或检查引用。")
    sys.exit(1)

# 速率限制器实现
class RateLimiter:
    def __init__(self, max_per_second=1, max_per_minute=60):
        self.max_per_second = max_per_second
        self.max_per_minute = max_per_minute
        self.second_count = 0
        self.minute_count = 0
        self.last_reset_second = time.time()
        self.last_reset_minute = time.time()
        self.lock = Lock()
        
    def acquire(self):
        with self.lock:
            current_time = time.time()
            
            # 检查是否需要重置秒计数器
            if current_time - self.last_reset_second >= 1:
                self.second_count = 0
                self.last_reset_second = current_time
                
            # 检查是否需要重置分钟计数器
            if current_time - self.last_reset_minute >= 60:
                self.minute_count = 0
                self.last_reset_minute = current_time
            
            # 检查是否超过限制
            if self.second_count >= self.max_per_second:
                sleep_time = 1 - (current_time - self.last_reset_second)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                self.second_count = 0
                self.last_reset_second = time.time()
                
            if self.minute_count >= self.max_per_minute:
                sleep_time = 60 - (current_time - self.last_reset_minute)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                self.minute_count = 0
                self.last_reset_minute = time.time()
            
            # 增加计数器
            self.second_count += 1
            self.minute_count += 1

# 创建全局限流器
rate_limiter = RateLimiter()

def get_model_id_for_url(url, default_model_id, model_id_wechat, model_id_techcrunch):
    """
    根据URL选择合适的模型ID
    
    参数:
        url: 要处理的URL
        default_model_id: 默认模型ID
        model_id_wechat: 微信文章专用模型ID
        model_id_techcrunch: TechCrunch文章专用模型ID
    
    返回:
        适用于该URL的模型ID
    """
    if "weixin.qq.com" in url:
        return model_id_wechat
    elif "techcrunch.com" in url:
        return model_id_techcrunch
    else:
        return default_model_id

def fetch_markdown(client, model_id, url, batch_idx, model_id_wechat=None, model_id_techcrunch=None, progress_callback=None):
    """
    用于并行调用 API 的辅助函数：
    给定 client, model_id, url, 调用接口获取对应 Markdown。
    
    包含重试逻辑：如果返回结果包含特定文本（如"微信，是一个生活方式"）或发生错误，
    会自动重试最多10次。超过重试次数后，对错误情况返回None，对特定文本情况则使用最后一次结果。
    
    返回值： (idx, md_text 或 None, 错误信息或 None)
    """
    MAX_RETRIES = 10
    UNWANTED_TEXT = ["微信，是一个生活方式", "环境异常"]
    retry_count = 0
    
    # 根据URL选择模型ID
    specific_model_id = model_id
    if model_id_wechat is not None and model_id_techcrunch is not None:
        specific_model_id = get_model_id_for_url(url, model_id, model_id_wechat, model_id_techcrunch)
    
    while retry_count < MAX_RETRIES:
        try:
            # 获取速率限制许可
            rate_limiter.acquire()
            
            completion = client.chat.completions.create(
                model=specific_model_id,
                messages=[{"role": "user", "content": url}],
            )
            md_text = completion.choices[0].message.content
            
            # 检查是否包含不需要的文本
            unwanted_found = False
            for text in UNWANTED_TEXT:
                if text in md_text:
                    unwanted_found = True
                    break
                    
            if unwanted_found:
                retry_count += 1
                retry_message = f"URL#{batch_idx}: 返回结果包含不需要的文本，正在重试 ({retry_count}/{MAX_RETRIES})..."
                print(retry_message)
                if progress_callback:
                    progress_callback(retry_message)
                
                if retry_count < MAX_RETRIES:
                    continue
                else:
                    final_message = f"URL#{batch_idx}: 已达到最大重试次数，放弃处理此URL..."
                    print(final_message)
                    if progress_callback:
                        progress_callback(final_message)
                    return (batch_idx, None, "包含不需要的文本并达到最大重试次数")
            
            # 如果返回文本不是以 # 开头，则截去 # 之前的部分
            if not md_text.startswith('#'):
                start_hash = md_text.find('#')
                if start_hash != -1:
                    md_text = md_text[start_hash:]  # 去除所有 # 之前的冗余文本
            
            return (batch_idx, md_text, None)
        
        except Exception as e:
            error_msg = str(e)
            retry_count += 1
            
            retry_error_message = f"URL#{batch_idx}: API调用出错: {error_msg}，正在重试 ({retry_count}/{MAX_RETRIES})..."
            print(retry_error_message)
            if progress_callback:
                progress_callback(retry_error_message)
            
            if retry_count < MAX_RETRIES:
                time.sleep(1)  # 延迟一秒后重试
                continue
            else:
                final_error_message = f"URL#{batch_idx}: 已达到最大重试次数，放弃处理此URL..."
                print(final_error_message)
                if progress_callback:
                    progress_callback(final_error_message)
                return (batch_idx, None, error_msg)


def main(input_txt, output_md=None, progress_callback=None):
    """
    从 input_txt 文件读取每行 URL，利用多线程并行调用 LLM Bot 接口获取 Markdown 文本并合并，
    最终输出为一个 output_md 文件（纯 Markdown）。
    从环境变量或.env文件读取 API Key、model ID 和处理参数。
    
    如果未指定 output_md，则使用默认路径和文件名：./abstract_md/abstract_md_yyyymmdd_hhmmss.md
    
    参数:
        input_txt: 输入文件路径，包含URL列表
        output_md: 输出Markdown文件路径
        progress_callback: 进度回调函数，用于实时更新进度信息
    """
    # 如果未指定输出文件，则使用默认路径和文件名
    if output_md is None:
        # 确保输出目录存在
        output_dir = os.path.join(".", "abstract_md")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_md = os.path.join(output_dir, f"abstract_md_{timestamp}.md")

    # 1. 从.env文件加载环境变量
    load_dotenv()
    
    api_key = os.getenv("API_KEY")
    model_id = os.getenv("MODEL_ID")
    model_id_wechat = os.getenv("MODEL_ID_WECHAT")
    model_id_techcrunch = os.getenv("MODEL_ID_TECHCRUNCH")
    
    # 固定max_workers为10，不再从.env读取batch_size
    max_workers = 10
    batch_size = max_workers
    
    if not api_key or not model_id:
        message = "未找到API_KEY或MODEL_ID环境变量，请检查.env文件！"
        print(message)
        if progress_callback:
            progress_callback(message)
        sys.exit(1)
        
    if not model_id_wechat:
        model_id_wechat = model_id
        warning_message = "未找到MODEL_ID_WECHAT环境变量，将使用MODEL_ID作为微信文章的处理模型"
        print(warning_message)
        if progress_callback:
            progress_callback(warning_message)
            
    if not model_id_techcrunch:
        model_id_techcrunch = model_id
        warning_message = "未找到MODEL_ID_TECHCRUNCH环境变量，将使用MODEL_ID作为TechCrunch文章的处理模型"
        print(warning_message)
        if progress_callback:
            progress_callback(warning_message)

    # 2. 初始化客户端
    client = OpenAI(
        base_url="https://ark.cn-beijing.volces.com/api/v3/bots",
        api_key=api_key,
    )

    # 3. 读取包含 URL 的文件
    if not os.path.exists(input_txt):
        message = f"输入文件 {input_txt} 不存在！"
        print(message)
        if progress_callback:
            progress_callback(message)
        sys.exit(1)

    with open(input_txt, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    total_urls = len(urls)
    total_batches = math.ceil(total_urls / batch_size)
    message = f"\n开始处理，共{total_urls}个URL，分{total_batches}批进行（每批{batch_size}个）...\n"
    print(message)
    if progress_callback:
        progress_callback(message)

    # 4. 并行调用 API
    results = []  # 用于存放 (idx, md_text) 的结果
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
            
            future_to_idx = {}
            for i, url in enumerate(batch_urls):
                future = executor.submit(
                    fetch_markdown, 
                    client, 
                    model_id, 
                    url, 
                    start_idx+i, 
                    model_id_wechat, 
                    model_id_techcrunch, 
                    progress_callback
                )
                future_to_idx[future] = start_idx+i

            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    (ret_idx, md_text, err_msg) = future.result()
                    if err_msg:
                        error_message = f"错误: {err_msg}"
                        print(error_message)
                        if progress_callback:
                            progress_callback(error_message)
                        continue
                    results.append((ret_idx, md_text))
                except Exception as e:
                    error_message = f"错误: {e}"
                    print(error_message)
                    if progress_callback:
                        progress_callback(error_message)

            batch_complete_message = f"第{batch+1}批处理完成"
            print(batch_complete_message)
            if progress_callback:
                progress_callback(batch_complete_message)

    completion_message = f"\n全部处理完成，成功处理 {len(results)}/{total_urls} 个URL\n"
    print(completion_message)
    if progress_callback:
        progress_callback(completion_message)

    # 5. 按照原先顺序 (idx) 排序并合并所有 Markdown
    results.sort(key=lambda x: x[0])
    merged_md = "\n\n".join(r[1] for r in results if r[1])

    if not merged_md.strip():
        empty_message = "未获取到任何有效内容，程序结束。"
        print(empty_message)
        if progress_callback:
            progress_callback(empty_message)
        return

    # 6. 将合并后的 Markdown 内容写入 .md 文件
    try:
        # 确保输出目录存在
        output_dir = os.path.dirname(output_md)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        with open(output_md, "w", encoding="utf-8") as f:
            f.write(merged_md)
        file_message = f"已生成Markdown文件：{output_md}"
        print(file_message)
        if progress_callback:
            progress_callback(file_message)
        return output_md
    except Exception as e:
        error_message = f"写入文件失败: {e}"
        print(error_message)
        if progress_callback:
            progress_callback(error_message)

if __name__ == "__main__":
    """
    命令行用法示例:
        python 1_url_to_abstract_md.py input_urls.txt [output.md]
        
    如果不指定输出文件，则使用默认路径和文件名：./abstract_md/abstract_md_yyyymmdd_hhmmss.md
    """
    if len(sys.argv) < 2:
        print("用法示例: python 1_url_to_abstract_md.py input.txt [output.md]")
        print("如果不指定输出文件，则使用默认路径和文件名：./abstract_md/abstract_md_yyyymmdd_hhmmss.md")
        sys.exit(1)

    input_txt_path = sys.argv[1]
    output_md_path = sys.argv[2] if len(sys.argv) > 2 else None
    main(input_txt_path, output_md_path)
