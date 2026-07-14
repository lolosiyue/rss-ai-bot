"""AI 總結模組 - DeepSeek 版"""

import os
import re
from typing import Optional

from openai import OpenAI


class AISummarizer:
    """AI 文章總結器（DeepSeek 版）"""

    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
            timeout=45.0,
            max_retries=1,
        )
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")

        self.success_count = 0
        self.fail_count = 0

    def summarize(self, title: str, content: str) -> Optional[str]:
        """總結文章"""
        content = self._clean_html(content)
        content = content[:6000]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是專業的新聞摘要助手。"
                            "請用繁體中文總結文章重點，要求："
                            "1. 不超過 140 字 "
                            "2. 保留重要技術細節、數字、產品名稱或事件結果 "
                            "3. 語氣客觀，不要加結論 "
                            "4. 翻譯成繁體中文，專有名詞保留原文。"
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"標題：{title}\n\n內容：{content}",
                    },
                ],
                temperature=0.3,
                max_tokens=400,
                stream=False,
                extra_body={"thinking": {"type": "disabled"}},
            )

            summary = (response.choices[0].message.content or "").strip()
            if summary:
                self.success_count += 1
                return summary

            raise ValueError("DeepSeek 回傳空摘要")

        except Exception as e:
            print(f"❌ DeepSeek API 錯誤: {e}")
            self.fail_count += 1
            return self._simple_summary(content)

    def _simple_summary(self, content: str) -> str:
        """簡單摘要（當 AI API 失敗時）"""
        summary = content[:180].strip()
        if len(content) > 180:
            summary += "..."
        return summary

    def _clean_html(self, text: str) -> str:
        """清理 HTML 標籤"""
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def print_stats(self):
        """印出統計資訊"""
        total = self.success_count + self.fail_count
        if total > 0:
            success_rate = (self.success_count / total) * 100
            print("\n📊 AI 總結統計：")
            print(f"   成功：{self.success_count}/{total} ({success_rate:.1f}%)")
            print(f"   失敗：{self.fail_count}/{total}")
