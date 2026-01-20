"""資料儲存模組 - 使用 GitHub Gist"""

import json
import os
import requests
from typing import List, Optional

class Storage:
    """管理已讀文章列表的儲存"""
    
    def __init__(self):
        self.gist_token = os.getenv('GIST_TOKEN')
        self.gist_id = os.getenv('GIST_ID')
        
        if not self.gist_token or not self.gist_id:
            print("⚠️ 警告：未設定 GIST_TOKEN 或 GIST_ID")
    
    def load_read_articles(self) -> List[str]:
        """載入已讀文章 ID 列表"""
        try:
            url = f"https://api.github.com/gists/{self.gist_id}"
            headers = {
                "Authorization": f"token {self.gist_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                gist_data = response.json()
                content = gist_data['files']['read_articles.json']['content']
                articles = json.loads(content)
                print(f"✅ 從 Gist 載入 {len(articles)} 筆記錄")
                return articles
            else:
                print(f"⚠️ Gist 載入失敗 ({response.status_code})，使用空列表")
                return []
                
        except Exception as e:
            print(f"❌ 載入錯誤: {e}")
            return []
    
    def save_read_articles(self, articles: List[str]) -> bool:
        """儲存已讀文章 ID 列表"""
        try:
            url = f"https://api.github.com/gists/{self.gist_id}"
            headers = {
                "Authorization": f"token {self.gist_token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json"
            }
            
            # 只保留最近 1000 筆（避免檔案過大）
            if len(articles) > 1000:
                articles = articles[-1000:]
                print(f"🧹 清理舊記錄，保留最近 1000 筆")
            
            data = {
                "files": {
                    "read_articles.json": {
                        "content": json.dumps(articles, indent=2, ensure_ascii=False)
                    }
                }
            }
            
            response = requests.patch(url, headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ 儲存 {len(articles)} 筆記錄到 Gist")
                return True
            else:
                print(f"❌ Gist 儲存失敗 ({response.status_code})")
                return False
                
        except Exception as e:
            print(f"❌ 儲存錯誤: {e}")
            return False
