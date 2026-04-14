import yfinance as yf
import pandas as pd
import warnings
import math
from datetime import datetime

warnings.simplefilter(action='ignore', category=FutureWarning)

def get_taiwan_midcap_100_info():
    # 台灣中型100成分股 (包含股票代號與名稱，此處以2025/2026年常見的主要成分股做範例代表)
    return {
        "2344.TW": "華邦電", "2353.TW": "宏碁", "2377.TW": "微星", "2606.TW": "裕民", "2834.TW": "臺企銀",
        "2889.TW": "國票金", "2890.TW": "永豐金", "2892.TW": "第一金", "2912.TW": "統一超", "3005.TW": "神基",
        "3044.TW": "健鼎", "3443.TW": "創意", "3702.TW": "大聯大", "4958.TW": "臻鼎-KY", "5347.TW": "世界",
        "5876.TW": "上海商銀", "6176.TW": "瑞儀", "6239.TW": "力成", "8046.TW": "南電", "8069.TW": "元太",
        "8299.TW": "群聯", "8454.TW": "富邦媒", "9904.TW": "寶成", "9910.TW": "豐泰", "9921.TW": "巨大",
        "1476.TW": "儒鴻", "1504.TW": "東元", "1590.TW": "亞德客-KY", "1605.TW": "華新", "2006.TW": "東和鋼鐵",
        "2049.TW": "上銀", "2204.TW": "中華", "2206.TW": "三陽工業", "2301.TW": "光寶科", "2313.TW": "華通",
        "2324.TW": "仁寶", "2337.TW": "旺宏", "2352.TW": "佳世達", "2376.TW": "技嘉", "2383.TW": "台光電",
        "2385.TW": "群光", "2395.TW": "研華", "2404.TW": "漢唐", "2408.TW": "南亞科", "2409.TW": "友達",
        "2449.TW": "京元電子", "2451.TW": "創見", "2542.TW": "興富發", "2609.TW": "陽明", "2610.TW": "華航",
        "2615.TW": "萬海", "2809.TW": "京城銀", "2812.TW": "台中銀", "2888.TW": "新光金", "2903.TW": "遠百",
        "2915.TW": "潤泰全", "3008.TW": "大立光", "3017.TW": "奇鋐", "3034.TW": "聯詠", "3037.TW": "欣興",
        "3189.TW": "景碩", "3231.TW": "緯創", "3406.TW": "玉晶光", "3481.TW": "群創", "3532.TW": "台勝科",
        "3533.TW": "嘉澤", "3583.TW": "辛耘", "3653.TW": "健策", "3665.TW": "貿聯-KY", "4739.TW": "康普",
        "4766.TW": "南寶", "4915.TW": "致伸", "4938.TW": "和碩", "4968.TW": "立積", "5269.TW": "祥碩",
        "5483.TW": "中美晶", "5522.TW": "遠雄", "5871.TW": "中租-KY", "5880.TW": "合庫金", "6121.TW": "新普",
        "6147.TW": "頎邦", "6213.TW": "聯茂", "6269.TW": "台郡", "6271.TW": "同欣電", "6278.TW": "台表科",
        "6409.TW": "旭隼", "6415.TW": "矽力*-KY", "6446.TW": "藥華藥", "6488.TW": "環球晶", "6505.TW": "台塑化",
        "6531.TW": "愛普*", "6669.TW": "緯穎", "6770.TW": "力積電", "8016.TW": "矽創", "8150.TW": "南茂",
        "8422.TW": "可寧衛", "8464.TW": "億豐", "8996.TW": "高力", "9914.TW": "美利達", "9941.TW": "裕融"
    }

end_date = datetime.strptime('2026-03-18', '%Y-%m-%d')
start_date = datetime.strptime('2020-11-01', '%Y-%m-%d')

midcap_info = get_taiwan_midcap_100_info()
symbols = list(midcap_info.keys())
all_results = []

budget_per_stock = 1000000

print(f"開始分析台灣中型100成分股，共 {len(symbols)} 檔...")

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
        
        stock_name = midcap_info.get(symbol, "")
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
print(f"{'台灣中型100成分股模擬測試結果 (每檔預算：1,000,000 台幣)':^80}")
print("="*80)

if not all_results:
    print("沒有中型100成分股符合條件。")
else:
    res_df = pd.DataFrame(all_results)
    # 依造投資報酬率由高到低排序
    res_df = res_df.sort_values('累積總報酬率(%)', ascending=False)
    print(res_df.to_string(index=False))

    # Output to Excel
    excel_filename = f"midcap100_simulation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    res_df.to_excel(excel_filename, index=False)
    print(f"\n[Success] 成果已成功輸出至 Excel 檔案：{excel_filename}")
