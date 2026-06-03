# 🤖 RSS AI Bot

自動抓取 RSS 訂閱源、使用 AI 總結文章、推送到 Discord。

## ✨ 特色

- 🤖 AI 自動總結文章重點
- 📰 支援多個 RSS 源
- 🔔 自動推送到 Discord
- 💰 完全免費（使用 GitHub Actions）
- 🔄 自動去重（不會重複推送）

## 🚀 快速開始

### 1. Fork 這個專案

點擊右上角的 Fork 按鈕

### 2. 設定 Secrets

前往 Settings → Secrets and variables → Actions → New repository secret

新增以下 Secrets：

- `DISCORD_WEBHOOK_URL`: Discord Webhook URL
- `DEEPSEEK_API_KEY`: Deepseek API Key
- `GEMINI_API_KEY`: Google Gemini API Key
- `GIST_TOKEN`: GitHub Personal Access Token
- `GIST_ID`: GitHub Gist ID
- `NVIDIA_API_KEY`: NVIDIA API Key

### 3. 啟用 Actions

前往 Actions 標籤，點擊 "I understand my workflows, go ahead and enable them"

### 4. 測試執行

Actions → RSS AI Bot → Run workflow

## 📝 自訂 RSS 源

編輯 `config/feeds.json`：

\`\`\`json
{
  "feeds": [
    {
      "name": "你的網站",
      "url": "https://example.com/feed",
      "category": "分類"
    }
  ]
}
\`\`\`

## 📅 執行頻率

預設每小時執行一次，可在 `.github/workflows/rss-bot.yml` 修改：

\`\`\`yaml
schedule:
  - cron: '0 */2 * * *'  # 改為每 2 小時
\`\`\`

## 📊 使用量

- GitHub Actions: 約 1,440 分鐘/月（免費額度 2,000 分鐘）
- Gemini API: 約 750K tokens/月（免費額度 1M tokens）

## 📄 授權

MIT License
