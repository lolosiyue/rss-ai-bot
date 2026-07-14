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
                            """# 角色與任務
                            你是一位專業的新聞摘要助手。請閱讀以下文章，將重點摘要並翻譯為繁體中文。

                            # 嚴格約束條件
                            1. 總字數嚴格控制在 140 字以內。
                            2. 只輸出一段摘要，不要標題、條列、前言或結語。
                            3. 必須保留事件主體、重要技術細節、數字、產品名稱、時間、地點與結果。
                            4. 語氣必須客觀中立，只陳述文章內容，不得推測、評論或延伸。
                            5. 全文使用繁體中文；專有名詞優先保留原文，若有常見中文譯名，可用「中文譯名（原文）」表示。
                            6. 若內容過長，優先刪除背景、形容詞與重複資訊，保留最重要事實。


                            # 待摘要文章"""
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
