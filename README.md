# Antigravity Stock Scanner - 台股智能掃描儀與網頁版 Dashboard

這是一個專門為台股設計的自動化掃描系統，結合了技術指標分析與現代化的網頁管理介面。系統會自動追蹤符合特定「突破後拉回」形態的股票，並透過 Telegram 與 Email 發送通知。

## 🌟 主要功能

- **技術形態掃描**：
  - 條件一：股價創 30 日新高且當日漲停（漲幅 >= 9.8%）。
  - 條件二：在 10 天內拉回至 5 日均線 (MA5) 且未破，作為潛在買點。
- **現代化網頁 Dashboard**：
  - 採用 Glassmorphism (毛玻璃) 與深色模式設計。
  - 即時查看篩選結果、管理通知設定。
- **自動化排程**：
  - 內建排程功能，可設定每天在收盤後自動掃描。
- **多管道通知**：
  - **Telegram**：即時發送美觀的選股摘要。
  - **Email**：發送詳細的 HTML 表格報告。

## 🛠️ 技術棧

- **Backend**: FastAPI (Python)
- **Frontend**: Vanilla JS, CSS (Premium Aesthetics)
- **Scheduler**: APScheduler
- **Database**: SQLite (SQLAlchemy)
- **Data Source**: yfinance, twstock

## 🚀 快速開始

### 1. 安裝環境
確保您的系統已安裝 Python 3.10+。

```bash
# 複製專案
git clone <your-repo-url>
cd 股票分析

# 建立並啟動虛擬環境 (Windows)
python -m venv venv
venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt
```

### 2. 啟動應用程式
```bash
python run_app.py
```

### 3. 設定與使用
- 開啟瀏覽器並訪問 `http://127.0.0.1:8000`。
- 點擊「**系統設定**」：
  - 輸入您的 Telegram Bot Token 與 Chat ID。
  - 輸入您的 Gmail 與應用程式密碼。
  - 設定您希望自動執行掃描的時間 (例如 15:30)。
- 點擊「**立即執行掃描**」來測試系統。

## 📁 專案結構

- `backend/`: 核心 API 與掃描邏輯。
- `static/`: 網頁靜態資源 (CSS/JS)。
- `templates/`: HTML 模板檔案。
- `run_app.py`: 專案入口啟動檔案。

## ⚠️ 注意事項

- 本系統僅供量化分析與研究參考，不構成任何投資建議。
- 請確保在使用 Email 通知功能時，已開啟 Gmail 的「應用程式密碼」功能。

## 📜 授權

MIT License.
