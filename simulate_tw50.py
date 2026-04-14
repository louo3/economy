import yfinance as yf
import pandas as pd
import warnings
import math
from datetime import datetime
import os

# SSL 憑證路徑修正 (解決中文資料夾路徑問題)
os.environ['SSL_CERT_FILE'] = r'C:\Users\ASUS\cacert.pem'
os.environ['REQUESTS_CA_BUNDLE'] = r'C:\Users\ASUS\cacert.pem'

warnings.simplefilter(action='ignore', category=FutureWarning)

def get_taiwan_50_info():
    return {
        "2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科", "2308.TW": "台達電", "2382.TW": "廣達",
        "2881.TW": "富邦金", "2882.TW": "國泰金", "2891.TW": "中信金", "2412.TW": "中華電", "2886.TW": "兆豐金",
        "1216.TW": "統一", "2884.TW": "玉山金", "2002.TW": "中鋼", "2885.TW": "元大金", "2357.TW": "華碩",
        "2880.TW": "華南金", "3711.TW": "日月光投控", "2892.TW": "第一金", "2890.TW": "永豐金", "5871.TW": "中租-KY",
        "2345.TW": "智邦", "3231.TW": "緯創", "2883.TW": "開發金", "3008.TW": "大立光", "2887.TW": "台新金",
        "1101.TW": "台泥", "5880.TW": "合庫金", "2303.TW": "聯電", "2395.TW": "研華", "4938.TW": "和碩",
        "3045.TW": "台灣大", "2207.TW": "和泰車", "2379.TW": "瑞昱", "3661.TW": "世芯-KY", "1102.TW": "亞泥",
        "1301.TW": "台塑", "1303.TW": "南亞", "6669.TW": "緯穎", "2408.TW": "南亞科", "2324.TW": "仁寶",
        "3034.TW": "聯詠", "2603.TW": "長榮", "2618.TW": "長榮航", "2609.TW": "陽明", "1590.TW": "亞德客-KY",
        "2368.TW": "金像電", "7769.TW": "台灣虎航-創", "2449.TW": "京元電子", "3037.TW": "欣興", "2344.TW": "華邦電"
    }

end_date = datetime.strptime('2026-03-18', '%Y-%m-%d')
start_date = datetime.strptime('2020-11-01', '%Y-%m-%d')

tw50_info = get_taiwan_50_info()
symbols = list(tw50_info.keys())
all_results = []

budget_per_stock = 1000000

print(f"開始分析台灣50成分股...")

for symbol in symbols:
    df = yf.download(symbol, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), progress=False)

    if df.empty or len(df) < 60:
        continue

    if isinstance(df.columns, pd.MultiIndex):
        close_series = df[('Close', symbol)]
        open_series = df[('Open', symbol)]
        vol_series = df[('Volume', symbol)]
    else:
        close_series = df['Close']
        open_series = df['Open']
        vol_series = df['Volume']

    clean_df = pd.DataFrame({
        'Open': open_series,
        'Close': close_series,
        'Volume': vol_series
    })
    clean_df.dropna(inplace=True)
    if clean_df.empty:
        continue

    # 計算 60 日均線 (季線)
    clean_df['MA60'] = clean_df['Close'].rolling(window=60).mean()

    monthly_df = clean_df.resample('ME').agg({
        'Open': 'first',
        'Close': 'last',
        'Volume': 'sum',
        'MA60': 'last'
    })

    # 月度漲幅
    monthly_df['Monthly_Return'] = (monthly_df['Close'] - monthly_df['Open']) / monthly_df['Open']

    five_years_ago = pd.to_datetime('2021-03-01').tz_localize(monthly_df.index.tz)
    five_years_monthly = monthly_df[monthly_df.index >= five_years_ago].copy()

    avg_monthly_volume = five_years_monthly['Volume'].mean()

    matches = []
    for idx, row in five_years_monthly.iterrows():
        if pd.isna(row['MA60']):
            continue
        
        # 三大核心條件
        cond_return = row['Monthly_Return'] > 0.20
        cond_volume = row['Volume'] > avg_monthly_volume
        cond_ma = row['Close'] > row['MA60']
        
        if cond_return and cond_volume and cond_ma:
            matches.append({
                'Month': idx.strftime('%Y-%m'),
                'Return(%)': round(row['Monthly_Return'] * 100, 2),
                'Volume': int(row['Volume']),
                'Close': round(row['Close'], 2),
                'MA60': round(row['MA60'], 2)
            })
    
    if len(matches) > 0:
        latest_price = float(close_series.iloc[-1])
        latest_date = close_series.index[-1].strftime('%Y-%m-%d')
        
        buy_months = [r['Month'] for r in matches]
        buy_prices = [r['Close'] for r in matches]

        # 每次買進的預算即為：總預算 / 符合發生的次數
        budget_per_trade = budget_per_stock / len(matches)

        total_shares = 0
        total_spent = 0
        remaining_cash = 0

        for p in buy_prices:
            # 支援零股買進，直接無條件捨去取整數股
            shares = math.floor(budget_per_trade / p)
            cost = shares * p
            total_shares += shares
            total_spent += cost
            cash_left = budget_per_trade - cost
            remaining_cash += cash_left
            
        current_value = total_shares * latest_price
        total_asset = current_value + remaining_cash
        total_return = (total_asset - budget_per_stock) / budget_per_stock * 100
        
        stock_name = tw50_info.get(symbol, "")
        formatted_name = f"{symbol} ({stock_name})"

        all_results.append({
            '股票代號名稱': formatted_name,
            '符合條件次數': len(matches),
            '進場月份': ", ".join(buy_months),
            '最新收盤日期': latest_date,
            '最新收盤價': round(latest_price, 2),
            '累積買入股數': total_shares,
            '目前總資產價值': round(total_asset, 2),
            '累積總報酬率(%)': round(total_return, 2)
        })

print("\n" + "="*80)
print(f"{'台灣50成分股模擬測試結果 (每檔預算：1,000,000 台幣)':^80}")
print("="*80)

if not all_results:
    print("沒有股票符合條件。")
else:
    res_df = pd.DataFrame(all_results)
    # 依造投資報酬率由高到低排序
    res_df = res_df.sort_values('累積總報酬率(%)', ascending=False)
    print(res_df.to_string(index=False))

    # Output to Excel
    excel_filename = f"tw50_simulation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    res_df.to_excel(excel_filename, index=False)
    print(f"\n[Success] 成果已成功輸出至 Excel 檔案：{excel_filename}")
