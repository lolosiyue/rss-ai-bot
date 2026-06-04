"""AI 總結模組 - NVIDIA 專用版"""

import os
import re
import time
from typing import Optional
from openai import OpenAI  # NVIDIA NIM 支援並相容 OpenAI SDK

class AISummarizer:
    """AI 文章總結器（NVIDIA 版）"""
    
    def __init__(self):
        # [修改] 初始化 NVIDIA 客戶端與端點
        self.client = OpenAI(
            api_key=os.getenv('NVIDIA_API_KEY'),
            base_url="https://integrate.api.nvidia.com/v1"
        )
        # 選用 NVIDIA 平台提供的免費標準優質模型
        self.model = "meta/llama-3.3-70b-instruct" 
        
        # 統計
        self.success_count = 0
        self.fail_count = 0
    
    def summarize(self, title: str, content: str) -> Optional[str]:
        """總結文章"""
        
        # 清理 HTML 標籤
        content = self._clean_html(content)
        
        # 🔥 【優化 1】將截取字數從 5000 降到 3500！

        content = content[:3500]
        
        # 🔥 【優化 2】智慧重試機制設定
        max_retries = 3      # 最多重試 3 次
        base_delay = 10       # 基礎等待 10 秒
        
        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system", 
                            "content": "你是專業的新聞摘要助手。請用繁體中文總結文章重點，要求：1. 不超過 100 字 2. 保留關鍵技術參數或事件結果 3. 語氣客觀。 4. 翻譯成繁體中文，專有名詞保留原文"
                        },
                        {
                            "role": "user", 
                            "content": f"標題：{title}\n\n內容：{content}"
                        }
                    ],
                    temperature=0.3,
                    max_tokens=300,
                    stream=False
                )
                
                summary = response.choices[0].message.content.strip()
                self.success_count += 1
                return summary

            except Exception as e:
                # 檢查是不是觸發了 429 Too Many Requests
                if "429" in str(e) and attempt < max_retries:
                    # 指數退避計算：第一次睡 10 秒，第二次睡 20 秒，第三次睡 40 秒
                    sleep_time = base_delay * (2 ** attempt)
                    print(f"⚠️ 觸發 NVIDIA 429 限制，伺服器太擠了！將在 {sleep_time} 秒後進行第 {attempt + 1} 次重試...")
                    time.sleep(sleep_time)
                    continue  # 進入下一次迴圈重試
                
                # 如果不是 429，或者重試了 3 次都沒救，才宣告失敗並走向低保方案
                print(f"❌ NVIDIA API 真正錯誤: {e}")
                self.fail_count += 1
                return self._simple_summary(content)
        
    def _simple_summary(self, content: str) -> str:
        """簡單摘要（當 AI API 失敗時）"""
        summary = content[:150].strip()
        if len(content) > 150:
            summary += "..."
        return summary
    
    def _clean_html(self, text: str) -> str:
        """清理 HTML 標籤"""
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def print_stats(self):
        """印出統計資訊"""
        total = self.success_count + self.fail_count
        if total > 0:
            success_rate = (self.success_count / total) * 100
            print(f"\n📊 AI 總結統計：")
            print(f"   成功：{self.success_count}/{total} ({success_rate:.1f}%)")
            print(f"   失敗：{self.fail_count}/{total}")
