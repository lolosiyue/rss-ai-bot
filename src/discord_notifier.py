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
        """發送單批文章（含錯誤防護）"""
        embeds = []
        for article in batch_articles:
            # 1. 確保基本欄位有值，且強制轉為字串
            title = str(article.get('title', '無標題'))
            if not title: title = "無標題"
            
            summary = str(article.get('summary', '無摘要'))
            if not summary: summary = "無摘要"
            
            # 強制截斷以符合 Discord 限制 (Description max 4096)
            summary = summary[:4000]

            # 2. 獲取連結 (如果為空則不加入)
            link = article.get('link', '')
            
            # 3. 獲取顏色
            color = self._get_color(title + summary)

            # 建構 Embed 物件
            embed = {
                "title": title,
                "description": summary,
                "color": color,
                "footer": {
                    "text": f"來源: {article.get('source', 'RSS')} | AI: DeepSeek-V3"
                }
            }
            
            # 只有當連結存在且以 http 開頭時才加入，避免 400 錯誤
            if link and link.startswith('http'):
                embed["url"] = link

            # 注意：這裡刻意移除了 "timestamp" 欄位
            # 因為 RSS 的時間格式混亂，容易導致 Discord 拒收整個請求 (400 Error)
            
            embeds.append(embed)

        payload = {
            "username": "RSS AI Bot",
            "embeds": embeds,
            "avatar_url": "https://cdn-icons-png.flaticon.com/512/2111/2111463.png"
        }

        try:
            # 加入 print 以便除錯，如果再次失敗可以看到發送了什麼
            print(f"DEBUG Payload: {json.dumps(payload, ensure_ascii=False)}") 
            
            response = requests.post(
                self.webhook_url, 
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code not in [200, 204]:
                print(f"❌ Discord 發送失敗 ({response.status_code}): {response.text}")
            else:
                print(f"✅ 成功發送一批 ({len(embeds)} 則)")
                
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