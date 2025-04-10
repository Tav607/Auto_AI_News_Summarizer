#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
import importlib.util

def load_module(module_path, module_name):
    """
    动态加载模块
    
    参数:
        module_path: 模块文件路径
        module_name: 模块名称
    
    返回:
        加载的模块
    """
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    """
    组合URL到文章抓取和文章到摘要生成的两个步骤
    """
    parser = argparse.ArgumentParser(description="将URL转换为文章摘要Markdown文件")
    parser.add_argument("input_urls", help="包含URL列表的输入文件路径")
    parser.add_argument("--output_dir", "-d", help="文章内容输出目录")
    parser.add_argument("--output_md", "-o", help="摘要Markdown输出文件路径")
    
    args = parser.parse_args()
    
    # 获取脚本所在目录
    script_dir = Path(__file__).parent
    
    # 如果未指定文章输出目录，则使用默认路径
    if not args.output_dir:
        articles_dir = script_dir / "article_content"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output_dir = str(articles_dir / f"articles_{timestamp}")
    
    # 如果未指定摘要输出文件，则使用默认路径
    if not args.output_md:
        abstract_dir = script_dir / "abstract_md"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output_md = str(abstract_dir / f"abstract_md_{timestamp}.md")
    
    print("\n" + "="*80)
    print(f"步骤 1: 抓取文章内容 - 开始")
    print("="*80)
    
    # 动态导入模块
    url_to_article = load_module(str(script_dir / "1a_url_to_article.py"), "url_to_article")
    
    # 调用第一步：抓取文章内容
    successful_articles_file = url_to_article.main(args.input_urls, args.output_dir)
    
    if not successful_articles_file or not os.path.exists(successful_articles_file):
        print("文章抓取失败或没有成功抓取的文章，程序终止")
        sys.exit(1)
    
    print("\n" + "="*80)
    print(f"步骤 2: 生成文章摘要 - 开始")
    print("="*80)
    
    # 动态导入模块
    article_to_abstract = load_module(str(script_dir / "1b_article_to_abstract_md.py"), "article_to_abstract")
    
    # 调用第二步：生成文章摘要
    output_md_file = article_to_abstract.main(successful_articles_file, args.output_md)
    
    if not output_md_file:
        print("摘要生成失败，程序终止")
        sys.exit(1)
    
    print("\n" + "="*80)
    print(f"全部处理完成！")
    print(f"文章内容保存在: {args.output_dir}")
    print(f"摘要Markdown文件: {args.output_md}")
    print("="*80 + "\n")

if __name__ == "__main__":
    main() 