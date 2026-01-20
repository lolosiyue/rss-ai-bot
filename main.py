#!/usr/bin/env python3
"""
RSS AI Bot - 主程式
自動抓取 RSS、AI 總結、推送到 Discord
"""

import json
import os
import sys
from datetime import datetime
from src.rss_fetcher import RSSFetcher
from src.ai_summarizer import AISummarizer
from src.discord_notifier import DiscordNotifier
from src.storage import Storage

def print_header():
    """印出標題"""
    print("\n" + "=" * 60)
    print("🤖 RSS AI Bot")
    print(f"⏰ 執行時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

def print_footer(start_time):
    """印出結尾"""
    duration = (datetime.now() - start_time).total_seconds()
    print("\n" + "=" * 60)
    print(f"✅ 執行完成")
    print(f"⏱️  耗時：{duration:.1f} 秒")
    print("=" * 60 + "\n")

def load_config():
    """載入設定檔"""
    try:
        with open('config/feeds.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ 錯誤：找不到 config/feeds.json")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ 錯誤：feeds.json 格式錯誤 - {e}")
        sys.exit(1)

def check_env_vars():
    """檢查必要的環境變數"""
    required_vars = {
        'DISCORD_WEBHOOK_URL': 'Discord Webhook URL',
        'GEMINI_API_KEY': 'Google Gemini API Key',
        'GIST_TOKEN': 'GitHub Personal Access Token',
        'GIST_ID': 'GitHub Gist ID'
    }
    
    missing = []
    for var, name in required_vars.items():
        if not os.getenv(var):
            missing.append(f"  - {var} ({name})")
    
    if missing:
        print("❌ 錯誤：缺少必要的環境變數：")
        print("\n".join(missing))
        print("\n請在 GitHub Repository Settings → Secrets 中設定")
        sys.exit(1)

def main():
    """主程式"""
    start_time = datetime.now()
    print_header()
    
    # 檢查環境變數
    check_env_vars()
    
    # 載入設定
    config = load_config()
    print(f"📋 載入 {len(config['feeds'])} 個 RSS 源")
    
    # 初始化模組
    storage = Storage()
    fetcher = RSSFetcher(config['feeds'])
    summarizer = AISummarizer()
    notifier = DiscordNotifier(os.getenv('DISCORD_WEBHOOK_URL'))
    
    try:
        # 1. 載入已讀文章列表
        print(f"\n{'─' * 60}")
        print("📚 載入已讀文章列表...")
        read_articles = storage.load_read_articles()
        print(f"   目前已讀：{len(read_articles)} 篇")
        
        # 2. 抓取 RSS
        print(f"\n{'─' * 60}")
        all_articles = fetcher.fetch_all()
        
        if not all_articles:
            print("⚠️ 沒有抓取到任何文章")
            print_footer(start_time)
            return
        
        # 3. 過濾新文章
        print(f"\n{'─' * 60}")
        print("🔍 過濾新文章...")
        new_articles = [
            article for article in all_articles
            if article['id'] not in read_articles
        ]
        print(f"   新文章：{len(new_articles)} 篇")
        
        if not new_articles:
            print("✅ 沒有新文章")
            print_footer(start_time)
            return
        
        # 4. AI 總結
        print(f"\n{'─' * 60}")
        print(f"🤖 開始 AI 總結（最多處理 20 篇）...")
        print(f"{'─' * 60}")
        
        summarized_articles = []
        max_articles = min(len(new_articles), 20)
        
        for i, article in enumerate(new_articles[:max_articles], 1):
            print(f"\n[{i}/{max_articles}] {article['title'][:60]}...")
            print(f"   來源：{article['source']}")
            
            summary = summarizer.summarize(article['title'], article['content'])
            
            if summary:
                article['summary'] = summary
                summarized_articles.append(article)
                read_articles.append(article['id'])
                print(f"   ✅ 總結：{summary[:80]}...")
            else:
                print(f"   ⚠️ 總結失敗")
        
        # 印出統計
        summarizer.print_stats()
        
        # 5. 發送到 Discord
        if summarized_articles:
            print(f"\n{'─' * 60}")
            notifier.send_articles(summarized_articles)
        
        # 6. 儲存已讀列表
        print(f"\n{'─' * 60}")
        print("💾 儲存已讀列表...")
        storage.save_read_articles(read_articles)
        
        print_footer(start_time)
        
    except Exception as e:
        print(f"\n❌ 執行錯誤：{e}")
        import traceback
        traceback.print_exc()
        
        # 發送錯誤通知
        notifier.send_error(str(e))
        
        sys.exit(1)

if __name__ == '__main__':
    main()
