"""RSS 抓取模組"""

import feedparser
import hashlib
from typing import List, Dict
from datetime import datetime

class RSSFetcher:
    """RSS 源抓取器"""
    
    def __init__(self, feeds: List[Dict]):
        self.feeds = feeds
    
    def fetch_all(self) -> List[Dict]:
        """抓取所有 RSS 源的文章"""
        all_articles = []
        
        print(f"\n📡 開始抓取 {len(self.feeds)} 個 RSS 源...")
        print("-" * 50)
        
        for feed_config in self.feeds:
            try:
                articles = self._fetch_feed(feed_config)
                all_articles.extend(articles)
                print(f"✅ {feed_config['name']:<25} {len(articles):>3} 篇")
            except Exception as e:
                print(f"❌ {feed_config['name']:<25} 失敗: {e}")
        
        print("-" * 50)
        print(f"📊 總計抓取 {len(all_articles)} 篇文章\n")
        
        return all_articles
    
    def _fetch_feed(self, config: Dict) -> List[Dict]:
        """抓取單個 RSS 源"""
        feed = feedparser.parse(config['url'])
        articles = []
        
        # 取得最多 10 篇文章
        for entry in feed.entries[:10]:
            # 取得文章內容
            content = self._get_content(entry)
            
            # 取得發布時間
            published = self._get_published_date(entry)
            
            article = {
                'id': self._get_article_id(entry.link),
                'title': entry.title,
                'link': entry.link,
                'content': content,
                'published': published,
                'source': config['name'],
                'category': config.get('category', '未分類')
            }
            
            articles.append(article)
        
        return articles
    
    def _get_content(self, entry) -> str:
        """取得文章內容（嘗試多個欄位）"""
        # 嘗試不同的內容欄位
        for field in ['content', 'summary', 'description']:
            if hasattr(entry, field):
                content = getattr(entry, field)
                
                # 如果是 list，取第一個元素
                if isinstance(content, list) and len(content) > 0:
                    content = content[0].get('value', '')
                
                if content:
                    return content
        
        return ''
    
    def _get_published_date(self, entry) -> str:
        """取得發布時間"""
        for field in ['published', 'updated', 'created']:
            if hasattr(entry, field):
                return getattr(entry, field)
        
        return datetime.now().isoformat()
    
    def _get_article_id(self, url: str) -> str:
        """生成文章唯一 ID（使用 URL 的 MD5）"""
        return hashlib.md5(url.encode()).hexdigest()
