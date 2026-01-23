import requests
import time
import json

class DiscordNotifier:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_articles(self, articles):
        """
        分批發送文章到 Discord (每 5 篇一批)
        """
        if not articles:
            return

        BATCH_SIZE = 5
        total_articles = len(articles)

        print(f"📡 準備發送 {total_articles} 篇文章至 Discord...")

        for i in range(0, total_articles, BATCH_SIZE):
            batch = articles[i : i + BATCH_SIZE]
            current_batch_num = (i // BATCH_SIZE) + 1
            
            self._send_batch(batch)
            
            # 休息 1 秒，避免 Rate Limit
            time.sleep(1)

    def _send_batch(self, batch_articles):
        """發送單批文章"""
        embeds = []
        for article in batch_articles:
            title = article.get('title', '無標題')
            summary = article.get('summary', '無摘要')
            
            # [修復] 這裡調用顏色判斷函式
            color = self._get_color(title + summary)

            embed = {
                "title": title,
                "url": article.get('link', ''),
                "description": summary,
                "color": color,  # 使用動態顏色
                "footer": {
                    "text": f"來源: {article.get('source', 'RSS')} | AI: DeepSeek-V3"
                },
                "timestamp": article.get('published', '')
            }
            embeds.append(embed)

        payload = {
            "username": "RSS AI Bot",
            "embeds": embeds
        }

        try:
            response = requests.post(
                self.webhook_url, 
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            if response.status_code not in [200, 204]:
                print(f"❌ Discord 發送失敗 ({response.status_code}): {response.text}")
        except Exception as e:
            print(f"❌ Discord 連線錯誤: {e}")

    def _get_color(self, text):
        """
        [新增] 根據關鍵字決定 Embed 顏色
        """
        text = text.lower()
        
        # 🚨 緊急/安全 (紅色)
        if any(x in text for x in ['漏洞', '駭客', '攻擊', '警告', 'cve']):
            return 0xFF0000 
            
        # 🤖 AI/模型 (綠色)
        if any(x in text for x in ['ai', 'gpt', 'llm', 'model', 'deepseek', 'gemini']):
            return 0x00FF00
            
        # 🍎 Apple (灰色)
        if any(x in text for x in ['apple', 'ios', 'mac', 'iphone']):
            return 0x999999
            
        # ☁️ 雲端/技術 (藍色 - 預設)
        return 3447003

    def send_error(self, error_msg):
        """發送錯誤通知"""
        payload = {
            "username": "RSS Bot Alert",
            "content": f"⚠️ **系統執行錯誤**\n```{error_msg}```"
        }
        requests.post(self.webhook_url, json=payload)