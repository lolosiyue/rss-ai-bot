"""AI 總結模組 - NVIDIA 專用版"""

import os
import re
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
        
        # 截取內容保持在 5000 字以內
        content = content[:5000]
        
        try:
            # 呼叫 NVIDIA API
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
            print(f"❌ NVIDIA API 錯誤: {e}")
            self.fail_count += 1
            # 失敗時返回簡單截斷
            return self._simple_summary(content)