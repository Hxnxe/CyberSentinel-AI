import json
import os
from datetime import datetime
from utils.logger import get_logger
from utils.blog_manager import BlogManager
import re

logger = get_logger('article_manager')

class ArticleManager:
    def __init__(self, analyzer, blog_manager=None):
        self.analyzer = analyzer
        self.blog_manager = blog_manager or BlogManager()
        self.categories = {
            "漏洞分析": "🔍",
            "安全研究": "🔬",
            "威胁情报": "🎯",
            "安全工具": "🛠️",
            "最佳实践": "📚",
            "吃瓜新闻": "🍉",
            "其他": "📌"
        }
        
        # 分类别名映射
        self.category_aliases = {
            " 漏洞分析": "漏洞分析",  # 处理前导空格
            "漏洞利用": "漏洞分析",   # 将漏洞利用归类到漏洞分析
        }
        
        # 创建必要的目录
        self.data_dir = "data/articles"
        self.results_dir = "results/daily_articles"
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)
        
        # 加载已处理的URL和分类文章
        self.processed_urls_file = os.path.join(self.data_dir, "processed_urls.json")
        self.categorized_articles_file = os.path.join(self.data_dir, "categorized_articles.json")
        self.processed_urls = self._load_processed_urls()
        self.categorized_articles = self._load_categorized_articles()

    def _load_processed_urls(self):
        """加载已处理的URL列表"""
        if os.path.exists(self.processed_urls_file):
            try:
                with open(self.processed_urls_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载已处理URL文件失败: {str(e)}")
                return []
        return []

    def _load_categorized_articles(self):
        """加载已分类的文章"""
        if os.path.exists(self.categorized_articles_file):
            try:
                with open(self.categorized_articles_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载分类文章文件失败: {str(e)}")
                return {category: [] for category in self.categories.keys()}
        return {category: [] for category in self.categories.keys()}

    def _save_processed_urls(self):
        """保存已处理的URL列表"""
        try:
            with open(self.processed_urls_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_urls, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存已处理URL文件失败: {str(e)}")

    def _save_categorized_articles(self):
        """保存分类文章"""
        try:
            with open(self.categorized_articles_file, 'w', encoding='utf-8') as f:
                json.dump(self.categorized_articles, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存分类文章文件失败: {str(e)}")

    def filter_new_articles(self, articles):
        """过滤出新文章"""
        new_articles = []
        for title, url in articles:
            if url not in self.processed_urls:
                new_articles.append((title, url))
        return new_articles

    def process_articles(self, articles):
        """处理新文章"""
        if not articles:
            return None

        # 分析文章
        analysis_result = self.analyzer.analyze_article_titles(articles)
        if not analysis_result or not analysis_result['filtered_articles']:
            return None

        # 更新已处理的URL和分类文章
        today = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # 首先加载现有的分类文章数据
            today_articles = {category: [] for category in self.categories.keys()}
            
            # 保留今天已有的文章
            for category, articles_list in self.categorized_articles.items():
                today_articles[category] = [
                    article for article in articles_list 
                    if isinstance(article, dict) and article.get('date') == today
                ]
            
            # 创建URL集合用于去重（包含所有已存在的URL）
            existing_urls = set(self.processed_urls)
            for category_articles in today_articles.values():
                for article in category_articles:
                    if isinstance(article, dict) and 'url' in article:
                        existing_urls.add(article['url'])
            
            # 处理新文章
            new_articles_added = False
            for article in analysis_result['filtered_articles']:
                if 'url' not in article:
                    logger.warning(f"跳过缺少URL的文章: {article.get('title', 'Unknown')}")
                    continue
                    
                # 检查URL是否已经存在
                if article['url'] in existing_urls:
                    logger.info(f"跳过已存在的文章: {article.get('title', article['url'])}")
                    continue
                
                # 添加到已处理URL集合
                existing_urls.add(article['url'])
                if article['url'] not in self.processed_urls:
                    self.processed_urls.append(article['url'])
                
                # 处理分类
                category = article.get('category', '其他')
                category = self.category_aliases.get(category, category)
                if category not in self.categories:
                    logger.warning(f"未知分类: {category}，将归类为'其他'")
                    category = '其他'
                
                # 创建文章数据
                article_data = {
                    'title': article.get('title', 'Unknown'),
                    'url': article['url'],
                    'date': today
                }
                
                # 添加新文章到对应分类
                today_articles[category].append(article_data)
                logger.info(f"添加新文章到{category}分类: {article_data['title']}")
                new_articles_added = True
            
            # 更新分类文章数据
            # 保留非今天的文章，并添加今天的文章
            for category in self.categories.keys():
                old_articles = [
                    article for article in self.categorized_articles.get(category, [])
                    if isinstance(article, dict) and article.get('date') != today
                ]
                self.categorized_articles[category] = old_articles + today_articles[category]
            
            # 只有在添加了新文章时才保存数据
            if new_articles_added:
                self._save_processed_urls()
                self._save_categorized_articles()
                logger.info("保存更新后的文章数据")
            else:
                logger.info("没有新文章需要添加，跳过保存")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"处理文章时发生错误: {str(e)}", exc_info=True)
            return None

    def generate_daily_report(self, analysis_result, daily_report_path):
        """生成每日安全资讯报告并发布到博客

        Args:
            analysis_result (dict): 包含过滤后文章信息的字典
            daily_report_path (str): 报告文件的完整路径
        """
        # 检查 analysis_result 是否有效
        if not analysis_result or not analysis_result.get('filtered_articles'):
            logger.warning("没有有效的分析结果，无法生成每日报告")
            return

        today = datetime.now()
        date_str = today.strftime('%Y-%m-%d')
        # 使用传入的路径，不再自行构造
        # filename = os.path.join(self.results_dir, f"{date_str}.md")
        filename = daily_report_path # 使用传入的路径
        logger.info(f"准备生成每日报告: {filename}")

        # 用于去重的集合
        processed_urls = set()
        processed_titles = set()

        # 读取已有的文章（如果存在）
        existing_categorized_articles = {cat: [] for cat in self.categories.keys()}
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 解析已有内容中的文章
                    for category in self.categories.keys():
                        pattern = f"### {self.categories[category]} {category}\n\n([^#]*?)(?=\n###|\n## |$)"
                        matches = re.findall(pattern, content, re.DOTALL)
                        if matches:
                            articles_text = matches[0]
                            article_matches = re.findall(r'\* \[(.*?)\]\((.*?)\)', articles_text)
                            for title, url in article_matches:
                                processed_urls.add(url)
                                processed_titles.add(title)
                                existing_categorized_articles[category].append({
                                    'title': title,
                                    'url': url,
                                    'date': date_str
                                })
            except Exception as e:
                logger.error(f"读取已有文件失败: {str(e)}")

        # 按分类整理新文章
        for article in analysis_result['filtered_articles']:
            # 获取文章信息
            title = article.get('title', '无标题')
            url = article.get('url', '#')
            
            # 检查URL和标题是否已处理过
            if url in processed_urls or title in processed_titles:
                logger.info(f"跳过重复文章: {title}")
                continue
                
            # 添加到已处理集合
            processed_urls.add(url)
            processed_titles.add(title)
            
            # 处理分类
            category = article.get('category', '其他')
            # 处理分类别名
            category = self.category_aliases.get(category, category)
            # 如果分类不在预定义分类中，归类到"其他"
            if category not in self.categories:
                logger.warning(f"未知分类: {category}，将归类为'其他'")
                category = '其他'
            
            # 添加文章到对应分类
            existing_categorized_articles[category].append({
                'title': title,
                'url': url,
                'date': date_str
            })

        # 生成markdown内容
        content = f"""
# 安全资讯日报 {date_str}

> 本文由AI自动生成，基于对安全相关仓库、CVE和最新安全研究成果的自动化分析。
> 
> 更新时间：{today.strftime('%Y-%m-%d %H:%M:%S')}

<!-- more -->

## 今日资讯
"""
        # 添加分类文章
        for category, emoji in self.categories.items():
            articles = existing_categorized_articles[category]
            if articles:
                content += f"\n### {emoji} {category}\n\n"
                
                # 按日期倒序排序，处理空值情况
                articles.sort(
                    key=lambda x: x.get('date') or '0000-00-00',  # 使用默认值处理空值
                    reverse=True
                )
                
                # 添加文章
                for article in articles:
                    title = article.get('title', '无标题').strip()  # 去除标题前后空格
                    url = article.get('url', '#')
                    content += f"* [{title}]({url})\n"

        # 添加AI分析结果
        content += "\n## 安全分析\n"
        
        # 从AI分析目录读取今日的分析结果
        ai_analysis_file = os.path.join("results/ai_analysis", f"Ai_{date_str.replace('-', '_')}.md")
        if os.path.exists(ai_analysis_file):
            try:
                with open(ai_analysis_file, 'r', encoding='utf-8') as f:
                    ai_content = f.read()
                    # 移除原始文件的标题（如果有）
                    ai_content = ai_content.replace("# AI 安全分析日报", "").strip()
                    content += ai_content
            except Exception as e:
                logger.error(f"读取AI分析文件失败: {str(e)}")
                content += "\n> 暂无AI分析结果\n"
        else:
            content += "\n> 暂无AI分析结果\n"

        # 添加页脚
        content += """


## 免责声明
本文内容由 AI 自动生成，仅供参考和学习交流。文章中的观点和建议不代表作者立场，使用本文信息需自行承担风险和责任。
"""

        # 保存文件
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"已生成每日安全资讯报告: {filename}")

            # 发布到博客
            if self.blog_manager.publish_daily_report(date_str, content):
                logger.info(f"已成功发布到博客: {date_str}")
            else:
                logger.error(f"发布到博客失败: {date_str}")

        except Exception as e:
            logger.error(f"保存每日报告失败: {str(e)}")

    def set_blog_token(self, token):
        """设置博客认证token"""
        self.blog_manager.set_token(token) 
