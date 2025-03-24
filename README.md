# AI 新闻摘要工具

这个工具用于自动从多个来源（包括微信公众号和TechCrunch）获取新闻URL，生成摘要，并创建Markdown和PDF文档。

## 功能概述

- 自动抓取微信公众号和TechCrunch文章URL
- 从URL中提取文章内容并生成摘要
- 合并不同来源的摘要内容
- 生成最终摘要文档（Markdown和PDF格式）
- 支持并行处理以提高效率

## 系统要求

- Python 3.7+
- 操作系统: Windows, macOS, 或 Linux
- 对于PDF生成功能，需要安装markdown库

## 安装

1. 克隆仓库
2. 创建虚拟环境并激活:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 
venv\Scripts\activate  # Windows
```
3. 安装依赖:
```bash
pip install -r requirements.txt
```

## 环境变量配置

项目使用`.env`文件管理API密钥和配置。

### 设置步骤:

1. 在项目根目录创建一个名为`.env`的文件
2. 添加以下内容，替换为您的实际值:
```
API_KEY=your_api_key_here
MODEL_ID=your_model_id_here
MODEL_ID_WECHAT=your_wechat_model_id_here  # 可选
MODEL_ID_TECHCRUNCH=your_techcrunch_model_id_here  # 可选
MODEL_ID_SUMMARY=your_summary_model_id_here
```

### 环境变量说明:

- `API_KEY`: OpenAI API密钥
- `MODEL_ID`: 默认使用的模型ID
- `MODEL_ID_WECHAT`: 处理微信文章时使用的模型ID（可选）
- `MODEL_ID_TECHCRUNCH`: 处理TechCrunch文章时使用的模型ID（可选）
- `MODEL_ID_SUMMARY`: 汇总处理所有摘要生成总结时使用的模型ID

## 项目结构

- `0_wechat_news_url.py` - 从SQLite数据库提取微信公众号文章URL
- `0_techcrunch_news_url.py` - 从TechCrunch网站抓取文章URL
- `1_url_to_abstract_md.py` - 处理URL列表并生成摘要Markdown文件
- `2_abstract_md_to_summary.py` - 合并摘要Markdown文件并生成最终摘要
- `3_md_to_pdf.py` - 将Markdown文件转换为PDF格式
- `run_ai_news_pipeline.sh` - 一键运行整个处理流程的脚本

## 使用方法

### 单独运行各组件

1. 提取微信公众号文章URL:
```bash
python 0_wechat_news_url.py
```

2. 抓取TechCrunch文章URL:
```bash
python 0_techcrunch_news_url.py
```

3. 处理URL列表生成摘要:
```bash
python 1_url_to_abstract_md.py url/news_urls.txt
```

4. 合并摘要并生成最终摘要:
```bash
python 2_abstract_md_to_summary.py abstract_md/file1.md abstract_md/file2.md
```

5. 将Markdown转换为PDF:
```bash
python 3_md_to_pdf.py deliverable/summary.md
```

### 一键运行整个流程

使用提供的shell脚本一键执行整个处理流程:

```bash
chmod +x run_ai_news_pipeline.sh  # 确保脚本有执行权限
./run_ai_news_pipeline.sh
```

## 目录说明

- `url/` - 存储URL文件的目录
- `abstract_md/` - 存储从URL生成的摘要Markdown文件
- `deliverable/` - 存储最终生成的摘要文件（Markdown和PDF）
- `system_prompt/` - 存储系统提示模板

## 注意事项

- 确保您有足够的API配额用于处理大量文章
- 处理大量URL时可能需要较长时间，请耐心等待
- 请遵守相关网站的使用条款和爬虫政策 