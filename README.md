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

项目使用`.env`文件管理API密钥和配置。**请参考 `.env.example` 文件获取最新的变量列表和格式。**

### 设置步骤:

1. **复制 `.env.example` 为 `.env`**:
   ```bash
   cp .env.example .env
   ```
2. **编辑 `.env` 文件**, 替换占位符为您的实际值:
```dotenv
# Example for Volcengine service used in abstract generation
Volcengine_API_KEY="YOUR_VOLCENGINE_API_KEY"
Volcengine_MODEL_ID="YOUR_VOLCENGINE_MODEL_ID" # e.g., doubao-pro-32k
Volcengine_BASE_URL="https://ark.cn-beijing.volces.com/api/v3" # Or your region's endpoint

# Example for Google service used in final summarization
Google_API_KEY="YOUR_GOOGLE_API_KEY"
Google_MODEL_ID="YOUR_GOOGLE_MODEL_ID" # e.g., gemini-1.5-flash-latest
Google_BASE_URL="YOUR_GOOGLE_BASE_URL" # e.g., https://generativelanguage.googleapis.com/v1beta/models/
```
   *注意: 根据您在 `1b_article_to_abstract_md.py` 和 `2_abstract_md_to_summary.py` 中配置的客户端，填写对应的 API Key, Model ID, 和 Base URL。*

### 环境变量说明:

- `*_API_KEY`: 您使用的 LLM 服务商提供的 API 密钥。
- `*_MODEL_ID`: 用于生成摘要或总结的模型 ID。
- `*_BASE_URL`: LLM 服务商的 API 端点 URL。

## 项目结构

- `0_wechat_news_url.py` - 从SQLite数据库提取微信公众号文章URL
- `0_techcrunch_news_url.py` - 从TechCrunch网站抓取文章URL
- `1a_url_to_article.py` - 从URL提取文章内容并保存
- `1b_article_to_abstract_md.py` - 读取文章内容并生成摘要Markdown文件
- `1_url_to_abstract_md_wrapper.py` - 协调`1a`和`1b`处理URL列表
- `2_abstract_md_to_summary.py` - 合并摘要Markdown文件并生成最终摘要
- `3_md_to_pdf.py` - 将Markdown文件转换为PDF格式
- `run_ai_news_pipeline.sh` - 一键运行整个处理流程的脚本

## 使用方法

### 单独运行各组件

1. 提取微信公众号文章URL (生成 `url/wechat_news_urls_*.txt`):
```bash
python 0_wechat_news_url.py
```

2. 抓取TechCrunch文章URL (生成 `url/techcrunch_news_urls_*.txt`):
```bash
python 0_techcrunch_news_url.py
```

3. 处理URL列表生成摘要 (需要提供URL文件路径, 生成 `abstract_md/abstract_md_*.md`):
```bash
# 处理微信URL
python 1_url_to_abstract_md_wrapper.py url/wechat_news_urls_YYYYMMDD_HHMMSS.txt
# 处理TechCrunch URL
python 1_url_to_abstract_md_wrapper.py url/techcrunch_news_urls_YYYYMMDD_HHMMSS.txt
```
   *注意：请将 `YYYYMMDD_HHMMSS` 替换为实际生成的文件名中的时间戳。脚本 `1a` 会将文章内容存入 `article_content/`。*

4. 合并摘要并生成最终摘要 (需要提供摘要文件路径, 生成 `deliverable/summary_*.md`):
```bash
# 合并微信和TechCrunch的摘要
python 2_abstract_md_to_summary.py abstract_md/abstract_md_wechat_*.md abstract_md/abstract_md_techcrunch_*.md
```
   *注意：请将 `*` 替换为实际生成的文件名中的标识符或时间戳。*

5. 将Markdown转换为PDF (需要提供Markdown文件路径, 生成同名 `.pdf` 文件):
```bash
python 3_md_to_pdf.py deliverable/summary_YYYYMMDD_HHMMSS.md
```
   *注意：请将 `YYYYMMDD_HHMMSS` 替换为实际生成的文件名中的时间戳。*

### 一键运行整个流程

使用提供的shell脚本一键执行整个处理流程。该脚本会自动处理文件查找和传递:

```bash
chmod +x run_ai_news_pipeline.sh  # 确保脚本有执行权限 (仅首次需要)
./run_ai_news_pipeline.sh
```
*该脚本会按顺序执行步骤1到5，自动查找最新生成的URL和摘要文件作为后续步骤的输入。*

## 目录说明

- `url/` - 存储URL文件的目录
- `article_content/` - 存储从URL提取的原始文章内容
- `abstract_md/` - 存储从文章内容生成的摘要Markdown文件
- `deliverable/` - 存储最终生成的摘要文件（Markdown和PDF）
- `system_prompt/` - 存储系统提示模板

## 注意事项

- 确保您有足够的API配额用于处理大量文章
- 处理大量URL时可能需要较长时间，请耐心等待
- 请遵守相关网站的使用条款和爬虫政策 