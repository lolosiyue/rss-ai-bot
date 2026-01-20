"""AI 總結模組 - 支援多個 AI API"""

import os
import requests
from typing import Optional
import re

class AISummarizer:
    """AI 文章總結器（支援多個 API 備援）"""
    
    def __init__(self):
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        self.groq_key = os.getenv('GROQ_API_KEY')
        self.openai_key = os.getenv('OPENAI_API_KEY')
        
        # 統計
        self.success_count = 0
        self.fail_count = 0
    
    def summarize(self, title: str, content: str) -> Optional[str]:
        """總結文章（自動嘗試多個 API）"""
        
        # 清理 HTML 標籤
        content = self._clean_html(content)
        
        # 截取內容（避免 token 過多）
        content = content[:2000]
        
        # 1. 優先使用 Gemini（免費額度最大）
        if self.gemini_key:
            summary = self._summarize_gemini(title, content)
            if summary:
                self.success_count += 1
                return summary
        
        # 2. 備援：Groq（超快但額度較小）
        if self.groq_key:
            summary = self._summarize_groq(title, content)
            if summary:
                self.success_count += 1
                return summary
        
        # 3. 備援：OpenAI（付費但便宜）
        if self.openai_key:
            summary = self._summarize_openai(title, content)
            if summary:
                self.success_count += 1
                return summary
        
        # 4. 都失敗：返回簡單摘要
        self.fail_count += 1
        return self._simple_summary(content)
    
    def _summarize_gemini(self, title: str, content: str) -> Optional[str]:
        """使用 Google Gemini API"""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.gemini_key}"
            
            prompt = f"""請用繁體中文總結以下文章的重點，要求：
1. 不超過 100 字
2. 保留關鍵資訊
3. 語氣客觀
4. 不要加入個人評論

標題：{title}

內容：
{content}

總結："""
            
            data = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "maxOutputTokens": 200,
                    "temperature": 0.3,
                    "topP": 0.8,
                    "topK": 40
                }
            }
            
            response = requests.post(url, json=data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                
                # 檢查是否有回應
                if 'candidates' in result and len(result['candidates']) > 0:
                    summary = result['candidates'][0]['content']['parts'][0]['text']
                    summary = summary.strip()
                    
                    # 移除可能的前綴
                    summary = re.sub(r'^(總結：|摘要：)', '', summary)
                    
                    return summary
                else:
                    print(f"⚠️ Gemini 無回應內容")
                    return None
            else:
                print(f"⚠️ Gemini API 錯誤 ({response.status_code})")
                return None
                
        except Exception as e:
            print(f"❌ Gemini 錯誤: {e}")
            return None
    
    def _summarize_groq(self, title: str, content: str) -> Optional[str]:
        """使用 Groq API"""
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.groq_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "mixtral-8x7b-32768",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是專業的新聞摘要助手。請用繁體中文總結文章重點，不超過 100 字，語氣客觀。"
                    },
                    {
                        "role": "user",
                        "content": f"標題：{title}\n\n內容：{content}"
                    }
                ],
                "max_tokens": 200,
                "temperature": 0.3
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                summary = result['choices'][0]['message']['content']
                return summary.strip()
            else:
                print(f"⚠️ Groq API 錯誤 ({response.status_code})")
                return None
                
        except Exception as e:
            print(f"❌ Groq 錯誤: {e}")
            return None
    
    def _summarize_openai(self, title: str, content: str) -> Optional[str]:
        """使用 OpenAI API"""
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是專業的新聞摘要助手。請用繁體中文總結文章重點，不超過 100 字，語氣客觀。"
                    },
                    {
                        "role": "user",
                        "content": f"標題：{title}\n\n內容：{content}"
                    }
                ],
                "max_tokens": 200,
                "temperature": 0.3
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                summary = result['choices'][0]['message']['content']
                return summary.strip()
            else:
                print(f"⚠️ OpenAI API 錯誤 ({response.status_code})")
                return None
                
        except Exception as e:
            print(f"❌ OpenAI 錯誤: {e}")
            return None
    
    def _simple_summary(self, content: str) -> str:
        """簡單摘要（當所有 AI API 都失敗時）"""
        # 取前 150 字元
        summary = content[:150].strip()
        if len(content) > 150:
            summary += "..."
        return summary
    
    def _clean_html(self, text: str) -> str:
        """清理 HTML 標籤"""
        # 移除 HTML 標籤
        text = re.sub(r'<[^>]+>', '', text)
        # 移除多餘空白
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
