"""AI 總結模組 - DeepSeek 專用版"""

import os
import re
from typing import Optional
from openai import OpenAI  # [修改] 引入 OpenAI 庫兼容 DeepSeek

class AISummarizer:
    """AI 文章總結器（DeepSeek 版）"""
    
    def __init__(self):
        # [修改] 初始化 DeepSeek 客戶端
        self.client = OpenAI(
            api_key=os.getenv('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com"
        )
        self.model = "deepseek-chat"  # DeepSeek V3
        
        # 統計
        self.success_count = 0
        self.fail_count = 0
    
    def summarize(self, title: str, content: str) -> Optional[str]:
        """總結文章"""
        
        # 清理 HTML 標籤
        content = self._clean_html(content)
        
        # [修改] 截取內容 (DeepSeek 支援 64k context，這裡放寬到 5000 字以提升準確度)
        content = content[:5000]
        
        try:
            # [修改] 統一使用 OpenAI SDK 格式調用 DeepSeek
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "你是專業的新聞摘要助手。請用繁體中文總結文章重點，要求：1. 不超過 100 字 2. 保留關鍵技術參數或事件結果 3. 語氣客觀。"
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
            print(f"❌ DeepSeek API 錯誤: {e}")
            self.fail_count += 1
            # 失敗時返回簡單截斷
            return self._simple_summary(content)
    
    # ---------------------------------------------------------
    # 以下輔助函式保持不變
    # ---------------------------------------------------------

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