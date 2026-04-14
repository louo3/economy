import uvicorn
import os
import sys

# 將當前路徑加入 PYTHONPATH 以便 backend 模組能被正確導入
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("正在啟動 Antigravity 股票分析網頁版...")
    print("請開啟瀏覽器並訪問: http://127.0.0.1:8000")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
