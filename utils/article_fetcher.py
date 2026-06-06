import requests
import re
import html
import time
from datetime import datetime
from utils.logger import get_logger

logger = get_logger('article_fetcher')

class ArticleFetcher:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0'
        }
        self.cookies = {
            'Hm_lvt_0f7c5559638e1f2b5f9b2b6d8d3d0d9e': '1705457362',
            'Hm_lpvt_0f7c5559638e1f2b5f9b2b6d8d3d0d9e': '1705457362'
        }

    @staticmethod
    def _retry_with_backoff(func, max_retries=3, initial_delay=1):
        """使用退避策略的重试装饰器"""
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"操作失败，{delay}秒后重试: {str(e)}")
                    time.sleep(delay)
                    delay *= 2
        return wrapper

    def get_BruceFeIix_articles(self):
        '''获取今日url'''
        current_date = datetime.now().strftime("%Y-%m-%d")
        base_url = f'https://raw.githubusercontent.com/BruceFeIix/picker/refs/heads/master/archive/daily/{current_date[:4]}/{current_date}.md'
        
        logger.info(f"开始获取BruceFeIix文章，日期: {current_date}")
        logger.info(f"请求URL: {base_url}")
        
        @self._retry_with_backoff
        def fetch_articles():
            response = requests.get(base_url, headers=self.headers)
            response.raise_for_status()
            matches = re.findall(
                r'(?:[\d]+\.\s*)?(?P<title>.*?)(?:\]\(|\s+)?(https://mp\.weixin\.qq\.com/[^\s\)]+)(?:\)|$)', 
                response.text
            )
            logger.info(f"找到 {len(matches)} 篇文章")
            return [(self._clean_title(title), url.rstrip(')')) for title, url in matches]
        
        try:
            articles = fetch_articles()
            logger.info(f"成功获取BruceFeIix文章，共 {len(articles)} 篇")
            return articles
        except Exception as e:
            logger.error(f"获取BruceFeIix文章失败: {str(e)}")
            return []

    def get_doonsec_articles(self):
        '''获取洞见文章url'''
        logger.info("开始获取洞见文章")
        
        @self._retry_with_backoff
        def fetch_articles():
            response = requests.get(
                'https://wechat.doonsec.com/rss.xml',
                headers=self.headers,
                cookies=self.cookies
            )
            response.encoding = 'utf-8'
            decoded_string = html.unescape(response.text)
            logger.debug(f"响应编码: {response.encoding}")
            logger.debug(f"响应内容前100字符: {response.text[:100]}")
            matches = re.findall(
                r'<item><title>(.*?)</title><link>(https://mp\.weixin\.qq\.com/.*?)</link>', 
                decoded_string
            )
            logger.info(f"找到 {len(matches)} 篇文章")
            return [(self._clean_title(title), url) for title, url in matches]
        
        try:
            articles = fetch_articles()
            logger.info(f"成功获取洞见文章，共 {len(articles)} 篇")
            return articles
        except Exception as e:
            logger.error(f"获取洞见文章失败: {str(e)}")
            return []

    @staticmethod
    def _clean_title(title):
        """清理和标准化文章标题"""
        # 移除多余的标记和格式
        title = re.sub(r'[\[\]【】\(\)]', '', title)
        # 移除HTML标签
        title = re.sub(r'<[^>]+>', '', title)
        # 移除多余的空白字符
        title = ' '.join(title.split())
        # 移除标题中的链接
        title = re.sub(r'https?://\S+', '', title)
        return title.strip() 