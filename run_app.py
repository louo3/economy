import uvicorn
import os
import sys

# 將當前路徑加入 PYTHONPATH 以便 backend 模組能被正確導入
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # 雲端部署通常會提供 PORT 環境變數，本機預設使用 8000
    port = int(os.environ.get("PORT", 8000))
    # 雲端部署需要監聽 0.0.0.0 以接受外部請求
    host = "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1"
    
    print(f"正在啟動 Antigravity 股票分析網頁版 (連接埠: {port})...")
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)
