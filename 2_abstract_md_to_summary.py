#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
from datetime import datetime
import time
from dotenv import load_dotenv
from pathlib import Path
import shutil

# 如果你是用 volces-openai-sdk，请安装并导入它
try:
    from openai import OpenAI
except ImportError:
    print("请先安装相应的 SDK, 例如: pip install openai 或检查引用。")
    sys.exit(1)

def combine_markdown_files(file1_path, file2_path, output_dir=None):
    """
    合并两个 Markdown 文件到一个新文件中
    
    参数:
        file1_path: 第一个Markdown文件路径
        file2_path: 第二个Markdown文件路径
        output_dir: 输出目录，默认为None（使用输入文件所在目录）
    
    返回:
        combined_file_path: 合并后的文件路径
    """
    # 如果未指定输出目录，使用第一个文件所在的目录
    if output_dir is None:
        output_dir = os.path.dirname(file1_path)
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成带时间戳的文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    combined_filename = f"combined_abstract_md_{timestamp}.md"
    combined_file_path = os.path.join(output_dir, combined_filename)
    
    # 读取两个文件内容
    with open(file1_path, 'r', encoding='utf-8') as f1:
        content1 = f1.read()
    
    with open(file2_path, 'r', encoding='utf-8') as f2:
        content2 = f2.read()
    
    # 合并内容
    combined_content = content1 + "\n\n" + content2
    
    # 写入新文件
    with open(combined_file_path, 'w', encoding='utf-8') as f_out:
        f_out.write(combined_content)
    
    print(f"已将 {file1_path} 和 {file2_path} 合并到 {combined_file_path}")
    return combined_file_path

def generate_summary(client, model_id, markdown_content):
    """
    使用API生成Markdown文件内容的摘要
    
    参数:
        client: OpenAI客户端
        model_id: 使用的模型ID
        markdown_content: 要总结的Markdown内容
    
    返回:
        summary_text: 生成的摘要文本
    """
    MAX_RETRIES = 5
    retry_count = 0
    
    # 读取系统提示文件
    with open('./system_prompt/summary_prompt.md', 'r', encoding='utf-8') as f:
        prompt = f.read()

    while retry_count < MAX_RETRIES:
        try:
            # 调用API
            completion = client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": markdown_content}],
                temperature=0.5,
            )
            
            summary_text = completion.choices[0].message.content
            return summary_text
        
        except Exception as e:
            error_msg = str(e)
            retry_count += 1
            
            print(f"API调用出错: {error_msg}，正在重试 ({retry_count}/{MAX_RETRIES})...")
            
            if retry_count < MAX_RETRIES:
                time.sleep(1)  # 延迟一秒后重试
                continue
            else:
                print(f"已达到最大重试次数，无法生成摘要")
                raise

def create_deliverable_file(summary_text, combined_file_path):
    """
    创建最终的deliverable文件，包含标题和合并的内容
    
    参数:
        summary_text: 摘要文本内容
        combined_file_path: 合并的摘要源文件路径
    
    返回:
        deliverable_file_path: 最终文件路径
    """
    # 创建deliverable目录
    deliverable_dir = os.path.join(os.getcwd(), "deliverable")
    os.makedirs(deliverable_dir, exist_ok=True)
    
    # 生成带日期的文件名 (格式: AI News Update YYYY MM DD.md)
    today_date = datetime.now().strftime("%Y %m %d")
    display_date = datetime.now().strftime("%Y/%m/%d")
    deliverable_filename = f"AI News Update {today_date}.md"
    deliverable_file_path = os.path.join(deliverable_dir, deliverable_filename)
    
    # 读取合并的摘要源文件
    with open(combined_file_path, 'r', encoding='utf-8') as f_combined:
        combined_content = f_combined.read()
    
    # 创建标题
    title = f"# AI News Update - {display_date}\n\n"
    
    # 合并内容
    deliverable_content = title + "## Weekly Summary\n\n" + summary_text + "\n\n---\n\n" + "## News Abstracts\n\n" + combined_content
    
    # 写入最终文件
    with open(deliverable_file_path, 'w', encoding='utf-8') as f_out:
        f_out.write(deliverable_content)
    
    print(f"最终deliverable文件已保存到 {deliverable_file_path}")
    return deliverable_file_path

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='合并两个Markdown文件并生成摘要')
    parser.add_argument('file1', help='第一个Markdown文件路径')
    parser.add_argument('file2', help='第二个Markdown文件路径')
    args = parser.parse_args()
    
    # 检查文件是否存在
    for file_path in [args.file1, args.file2]:
        if not os.path.exists(file_path):
            print(f"错误: 文件 {file_path} 不存在")
            sys.exit(1)
    
    # 从.env文件加载环境变量
    load_dotenv()
    
    api_key = os.getenv("Google_API_KEY")
    model_id = os.getenv("Google_MODEL_ID")
    base_url = os.getenv("Google_BASE_URL")
    
    if not api_key or not model_id:
        print("未找到API_KEY或MODEL_ID_SUMMARY环境变量，请检查.env文件！")
        sys.exit(1)
    
    # 合并Markdown文件
    combined_file_path = combine_markdown_files(args.file1, args.file2)
    
    # 读取合并后的文件内容
    with open(combined_file_path, 'r', encoding='utf-8') as f:
        combined_content = f.read()
    
    # 初始化API客户端
    client = OpenAI(
        base_url=base_url,
        api_key=api_key,
    )
    
    try:
        # 生成摘要
        print("正在通过API生成摘要...")
        summary_text = generate_summary(client, model_id, combined_content)
        
        # 创建最终的deliverable文件
        create_deliverable_file(summary_text, combined_file_path)
        
    except Exception as e:
        print(f"生成摘要时出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 