import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def search_stock(query):
    """
    簡單的股票搜尋模擬。
    在實際應用中，可以對接 twstock 或 FinMind 的 API。
    這裡先提供幾個熱門台灣股票作為範例。
    """
    stocks = {
        "2330": "台積電 (TSMC)",
        "2317": "鴻海 (Foxconn)",
        "2454": "聯發科 (MediaTek)",
        "2308": "台達電 (Delta Electronics)",
        "2382": "廣達 (Quanta)",
        "2881": "富邦金 (Fubon Financial)",
        "2882": "國泰金 (Cathay Financial)",
        "2891": "中信金 (CTBC Financial)",
        "2412": "中華電 (Chunghwa Telecom)",
        "2886": "兆豐金 (Mega Financial)",
        "2303": "聯電 (UMC)",
        "2603": "長榮 (Evergreen Marine)",
        "2618": "長榮航 (EVA Air)",
        "2609": "陽明 (Yang Ming)",
        "3008": "大立光 (Largan Precision)",
    }
    
    results = []
    for code, name in stocks.items():
        if query in code or query in name:
            results.append((code, name))
    
    return results

def get_stock_data(ticker):
    """
    獲取指定股票的最近 5 天數據
    """
    if not ticker.endswith(".TW") and not ticker.endswith(".TWO"):
        ticker += ".TW"
        
    print(f"\n正在獲取 {ticker} 的資料...")
    stock = yf.Ticker(ticker)
    
    # 獲取最近 5 天的歷史數據
    end_date = datetime.now()
    start_date = end_date - timedelta(days=10) # 抓稍多一點確保有 5 天交易日
    
    df = stock.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
    
    if df.empty:
        print("找不到該股票的資料，請檢查代號是否正確。")
        return None
        
    return df.tail(5)

def main():
    print("="*40)
    print("      台灣股票搜尋與資料獲取程式      ")
    print("="*40)
    
    while True:
        user_input = input("\n請輸入股票名稱或代號 (輸入 'exit' 退出): ").strip()
        
        if user_input.lower() == 'exit':
            break
            
        if not user_input:
            continue
            
        search_results = search_stock(user_input)
        
        if not search_results:
            # 如果範例字典沒找到，嘗試直接用輸入值作為代號搜尋
            ticker_to_fetch = user_input
            if not (ticker_to_fetch.isdigit() or ticker_to_fetch.endswith(".TW")):
                print(f"找不到與 '{user_input}' 相關的預設股票。請嘗試輸入完整的股票代號（例如 2330）。")
                continue
        else:
            print(f"\n找到以下相關股票:")
            for i, (code, name) in enumerate(search_results):
                print(f"{i+1}. {code} - {name}")
                
            choice = input(f"\n請選擇股票編號 (1-{len(search_results)}) 或直接按 Enter 取消: ").strip()
            if not choice or not choice.isdigit() or int(choice) < 1 or int(choice) > len(search_results):
                continue
            
            ticker_to_fetch = search_results[int(choice)-1][0]
            
        data = get_stock_data(ticker_to_fetch)
        
        if data is not None:
            print(f"\n{ticker_to_fetch} 最近 5 天的交易資料:")
            # 格式化輸出
            print(data[['Open', 'High', 'Low', 'Close', 'Volume']].to_string())
            print("\n" + "-"*40)

if __name__ == "__main__":
    main()
