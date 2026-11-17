"""AI 總結模組 - DeepSeek 版"""

import os
import re
from datetime import datetime, timezone
from typing import Optional

from openai import OpenAI

from src.deepseek_pricing import is_deepseek_peak


class AISummarizer:
    """AI 文章總結器（DeepSeek 版）"""

    # 首次 + 1 次重試。SDK 重試設為 0，避免重試繞過尖峰檢查。
    _ATTEMPTS = 2

    def __init__(self, client=None, clock=None):
        if client is None:
            self.client = OpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com",
                timeout=45.0,
                max_retries=0,
            )
        else:
            self.client = client
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")

        self.success_count = 0
        self.fail_count = 0
        self.peak_skip_count = 0

    def summarize(self, title: str, content: str) -> Optional[str]:
        """總結文章。尖峰時段不呼叫 API，回傳 None（不標記已讀，留待下次離峰）。"""
        content = self._clean_html(content)
        content = content[:6000]

        for attempt in range(self._ATTEMPTS):
            # 每一次會計費的請求（含重試）當下重查，不只在作業開始時查一次。
            if is_deepseek_peak(self._clock()):
                self.peak_skip_count += 1
                print("⏸️ DeepSeek 尖峰計價，不呼叫 API，這篇留待下次離峰")
                return None

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
            except Exception as e:
                print(f"❌ DeepSeek API 錯誤: {e}")
                if attempt + 1 < self._ATTEMPTS:
                    continue
                self.fail_count += 1
                return self._simple_summary(content)

            summary = (response.choices[0].message.content or "").strip()
            if summary:
                self.success_count += 1
                return summary

            print("❌ DeepSeek 回傳空摘要")
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
        if total > 0 or self.peak_skip_count:
            print("\n📊 AI 總結統計：")
            if total > 0:
                success_rate = (self.success_count / total) * 100
                print(f"   成功：{self.success_count}/{total} ({success_rate:.1f}%)")
                print(f"   失敗：{self.fail_count}/{total}")
            if self.peak_skip_count:
                print(f"   尖峰略過：{self.peak_skip_count}（未呼叫 API，未標記已讀）")
