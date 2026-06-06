import json
import os
import requests
from datetime import datetime
from utils.logger import get_logger

logger = get_logger('blog_manager')


class BlogManager:
    def __init__(self, base_url="http://127.0.0.1", token="", data_dir="data/blog"):
        self.base_url = base_url.rstrip("/")
        self.token = token.strip() if isinstance(token, str) else ""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Content-Type': 'application/json;charset=UTF-8',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Charset': 'utf-8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'token': token
        }
        # 创建必要的目录
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 加载文章ID映射
        self.article_map_file = os.path.join(self.data_dir, "article_map.json")
        self.article_map = self._load_article_map()

    def _has_token(self):
        """Return whether blog publishing is configured."""
        return bool(self.token)

    def _headers_for_log(self):
        """Return request headers with sensitive values redacted for debug logs."""
        safe_headers = self.headers.copy()
        if safe_headers.get("token"):
            safe_headers["token"] = "<redacted>"
        return safe_headers

    def _load_article_map(self):
        """加载文章ID映射"""
        if os.path.exists(self.article_map_file):
            try:
                with open(self.article_map_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载文章映射文件失败: {str(e)}")
                return {}
        return {}

    def _save_article_map(self):
        """保存文章ID映射"""
        try:
            with open(self.article_map_file, 'w', encoding='utf-8') as f:
                json.dump(self.article_map, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存文章映射文件失败: {str(e)}")

    def set_token(self, token):
        """设置认证token"""
        self.token = token.strip() if isinstance(token, str) else ""
        self.headers['token'] = self.token

    def create_article(self, date_str):
        """创建新文章
        
        Args:
            date_str: 文章日期，格式为 YYYY-MM-DD
            
        Returns:
            int: 文章ID，如果创建失败返回None
        """
        try:
            if not self._has_token():
                logger.info("BLOG_TOKEN 未配置，跳过博客文章创建")
                return None

            # 检查是否已经存在该日期的文章
            if date_str in self.article_map:
                logger.info(f"日期 {date_str} 的文章已存在，ID: {self.article_map[date_str]}")
                return self.article_map[date_str]

            # 准备创建文章的数据
            data = {
                "title": f"日报[{date_str}]",
                "top": 0,
                "tags": [],
                "category": "安全资讯",
                "createdAt": datetime.now().isoformat(),
                "private": False,
                "hidden": False,
                "content": ""
            }

            # 发送创建请求
            response = requests.post(
                f"{self.base_url}/api/admin/article",
                headers=self.headers,
                json=data
            )

            if response.status_code == 201:
                result = response.json()
                if result['statusCode'] == 200 and 'data' in result:
                    article_id = result['data']['id']
                    # 保存文章ID映射
                    self.article_map[date_str] = article_id
                    self._save_article_map()
                    logger.info(f"成功创建文章，日期: {date_str}, ID: {article_id}")
                    return article_id
            
            logger.error(f"创建文章失败，状态码: {response.status_code}")
            return None

        except Exception as e:
            logger.error(f"创建文章时出错: {str(e)}")
            return None

    def update_article(self, article_id, content):
        """更新文章内容
        
        Args:
            article_id: 文章ID
            content: 文章内容
            
        Returns:
            bool: 更新是否成功
        """
        try:
            if not self._has_token():
                logger.info("BLOG_TOKEN 未配置，跳过博客文章更新")
                return False

            # 添加编码检查日志
            logger.debug(f"更新文章内容前100字符: {content[:100]}")
            
            # 记录请求信息
            logger.debug(f"准备更新文章，ID: {article_id}")
            logger.debug(f"请求头: {self._headers_for_log()}")
            logger.debug(f"内容长度: {len(content)}")
            
            try:
                # 发送更新请求，移除 Accept-Encoding 头，让服务器返回未压缩的响应
                headers = self.headers.copy()
                headers.pop('Accept-Encoding', None)
                
                response = requests.put(
                    f"{self.base_url}/api/admin/article/{article_id}",
                    headers=headers,
                    json={"content": content},
                    timeout=30
                )
                
                # 详细记录响应信息
                logger.debug(f"更新文章响应状态码: {response.status_code}")
                logger.debug(f"响应头: {dict(response.headers)}")
                
                # 检查响应内容类型
                content_type = response.headers.get('content-type', '')
                logger.debug(f"响应Content-Type: {content_type}")
                
                # 记录响应内容（前200个字符）
                response_text = response.text[:200]
                logger.debug(f"更新文章响应内容: {response_text}")
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                        if result.get('statusCode') == 200 and result.get('data', {}).get('modifiedCount', 0) > 0:
                            logger.info(f"成功更新文章，ID: {article_id}")
                            return True
                        else:
                            logger.error(f"更新文章失败，响应数据异常: {result}")
                    except json.JSONDecodeError as je:
                        logger.error(f"解析响应JSON失败: {str(je)}，响应内容: {response_text}")
                        return False
                
                logger.error(f"更新文章失败，状态码: {response.status_code}，响应: {response_text}")
                return False
                
            except requests.RequestException as e:
                logger.error(f"发送更新请求时出错: {str(e)}")
                return False

        except Exception as e:
            logger.error(f"更新文章时出错: {str(e)}")
            return False

    def get_article_id(self, date_str):
        """获取指定日期的文章ID
        
        Args:
            date_str: 文章日期，格式为 YYYY-MM-DD
            
        Returns:
            int: 文章ID，如果不存在返回None
        """
        return self.article_map.get(date_str)

    def publish_daily_report(self, date_str, content):
        """发布每日报告
        
        Args:
            date_str: 文章日期，格式为 YYYY-MM-DD
            content: 文章内容
            
        Returns:
            bool: 发布是否成功
        """
        try:
            # 首先获取或创建文章
            article_id = self.get_article_id(date_str)
            if article_id is None:
                article_id = self.create_article(date_str)
                if article_id is None:
                    return False

            # 更新文章内容
            return self.update_article(article_id, content)

        except Exception as e:
            logger.error(f"发布每日报告时出错: {str(e)}")
            return False

    def update_html_content(self, html_content):
        """更新博客的 HTML 内容"""
        try:
            if not self._has_token():
                logger.info("BLOG_TOKEN 未配置，跳过博客 HTML 更新")
                return False

            # 准备更新的数据
            data = {
                "_id": "67b72d183cd136c9b24ab4ea",  # 这里需要替换为实际的 ID
                "name": "每日资讯",
                "path": "/today",
                "type": "file",
                "html": html_content
            }

            logger.info("准备发送更新请求到博客")
            # 发送更新请求
            response = requests.put(
                f"{self.base_url}/api/admin/customPage",
                headers=self.headers,
                json=data
            )

            logger.info(f"更新请求发送，状态码: {response.status_code}")
            if response.status_code == 200:
                logger.info("成功更新博客的 HTML 内容")
                return True
            else:
                logger.error(f"更新博客 HTML 内容失败，状态码: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"更新博客 HTML 内容时出错: {str(e)}")
            return False 
