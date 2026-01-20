"""Discord 通知模組"""

import requests
from typing import List, Dict
from datetime import datetime

class DiscordNotifier:
    """Discord Webhook 通知器"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        
        if not webhook_url:
            print("⚠️ 警告：未設定 DISCORD_WEBHOOK_URL")
    
    def send_articles(self, articles: List[Dict]):
        """發送文章摘要到 Discord"""
        if not articles:
            print("📭 沒有新文章需要發送")
            return
        
        print(f"\n📤 準備發送 {len(articles)} 篇文章到 Discord...")
        
        # 按分類分組
        by_category = self._group_by_category(articles)
        
        # 建立 embeds
        embeds = self._create_embeds(by_category, articles)
        
        # 發送
        self._send_webhook(embeds, len(articles))
    
    def _group_by_category(self, articles: List[Dict]) -> Dict[str, List[Dict]]:
        """按分類分組文章"""
        by_category = {}
        
        for article in articles:
            category = article['category']
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(article)
        
        return by_category
    
    def _create_embeds(self, by_category: Dict[str, List[Dict]], all_articles: List[Dict]) -> List[Dict]:
        """建立 Discord Embeds"""
        embeds = []
        
        # 每個分類建立一個 embed
        for category, items in by_category.items():
            embed = {
                "title": f"📰 {category}",
                "description": f"共 {len(items)} 篇新文章",
                "color": self._get_color(category),
                "fields": [],
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "RSS AI 摘要機器人"
                }
            }
            
            # 每個分類最多顯示 5 篇
            for article in items[:5]:
                # 標題最多 100 字元
                title = article['title']
                if len(title) > 100:
                    title = title[:97] + "..."
                
                # 摘要最多 200 字元
                summary = article['summary']
                if len(summary) > 200:
                    summary = summary[:197] + "..."
                
                field = {
                    "name": f"🔗 {title}",
                    "value": (
                        f"{summary}\n"
                        f"[閱讀全文]({article['link']}) • "
                        f"來源：{article['source']}"
                    ),
                    "inline": False
                }
                
                embed['fields'].append(field)
            
            # 如果該分類超過 5 篇，顯示提示
            if len(items) > 5:
                embed['fields'].append({
                    "name": "📚 更多文章",
                    "value": f"還有 {len(items) - 5} 篇文章未顯示",
                    "inline": False
                })
            
            embeds.append(embed)
        
        # Discord 限制最多 10 個 embeds
        if len(embeds) > 10:
            embeds = embeds[:10]
            print(f"⚠️ 分類過多，只顯示前 10 個分類")
        
        return embeds
    
    def _send_webhook(self, embeds: List[Dict], total: int):
        """發送到 Discord Webhook"""
        try:
            # 建立訊息內容
            content = f"🌅 **今日新聞摘要** - 共 {total} 篇新文章"
            
            data = {
                "content": content,
                "embeds": embeds,
                "username": "RSS Bot",
                "avatar_url": "https://cdn-icons-png.flaticon.com/512/2111/2111463.png"
            }
            
            response = requests.post(
                self.webhook_url,
                json=data,
                timeout=10
            )
            
            if response.status_code == 204:
                print(f"✅ 成功發送到 Discord")
            elif response.status_code == 429:
                print(f"⚠️ Discord 速率限制，請稍後再試")
            else:
                print(f"❌ Discord 發送失敗 ({response.status_code})")
                print(f"   回應：{response.text}")
                
        except Exception as e:
            print(f"❌ Discord 發送錯誤: {e}")
    
    def send_error(self, error_message: str):
        """發送錯誤通知"""
        try:
            data = {
                "content": f"⚠️ **RSS Bot 執行錯誤**\n```\n{error_message}\n```",
                "username": "RSS Bot"
            }
            
            requests.post(self.webhook_url, json=data, timeout=10)
            
        except Exception as e:
            print(f"❌ 錯誤通知發送失敗: {e}")
    
    def _get_color(self, category: str) -> int:
        """根據分類返回顏色"""
        colors = {
            '科技': 0x3498db,    # 藍色
            '新聞': 0xe74c3c,    # 紅色
            '財經': 0x2ecc71,    # 綠色
            '娛樂': 0x9b59b6,    # 紫色
            '運動': 0xf39c12,    # 橘色
            '生活': 0x1abc9c,    # 青色
        }
        return colors.get(category, 0x95a5a6)  # 預設灰色
