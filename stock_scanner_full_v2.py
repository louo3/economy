import yfinance as yf
import pandas as pd
import twstock
from datetime import datetime, timedelta
from tqdm import tqdm
import os
import warnings
import time
import random
import sys
import os

# SSL 憑證路徑修正 (解決中文資料夾路徑問題)
os.environ['SSL_CERT_FILE'] = r'C:\Users\ASUS\cacert.pem'
os.environ['REQUESTS_CA_BUNDLE'] = r'C:\Users\ASUS\cacert.pem'

# 強制輸出為 UTF-8 以避免 Windows 終端亂碼
if sys.stdout.encoding != 'utf-8':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

warnings.filterwarnings('ignore')

def get_all_taiwan_stock_codes():
    """取得所有上市上櫃股票代號"""
    print("正在取得台股股票代號清單...")
    codes = twstock.codes
    tse_otc_codes = []
    for code, info in codes.items():
        if info.market in ['上市', '上櫃'] and len(code) == 4 and code.isdigit():
            suffix = ".TW" if info.market == '上市' else ".TWO"
            tse_otc_codes.append((f"{code}{suffix}", info.name))
    print(f"共找到 {len(tse_otc_codes)} 檔台股標的。")
    return tse_otc_codes

def process_dataframe(df, symbol, name):
    """處理單一股票的 DataFrame 並篩選條件"""
    try:
        # 確保必要的欄位存在且為單一層級
        required_cols = ['Open', 'High', 'Low', 'Close']
        if not all(col in df.columns for col in required_cols):
            return None
            
        df = df[required_cols].copy()
        df.dropna(subset=['Close'], inplace=True)
        
        if len(df) < 40:
            return None
            
        # 計算指標
        df['Prev_Close'] = df['Close'].shift(1)
        df['Price_Change'] = (df['Close'] - df['Prev_Close']) / df['Prev_Close']
        df['High_30_Prev'] = df['High'].shift(1).rolling(window=30).max()
        df['MA5'] = df['Close'].rolling(window=5).mean()
        
        # 篩選最近 6 個月的區間
        cutoff_date = (datetime.now() - timedelta(days=180)).date()
        df.dropna(subset=['MA5', 'High_30_Prev', 'Price_Change'], inplace=True)
        recent_df = df[df.index.date >= cutoff_date]
        
        results = []
        for i in range(len(recent_df)):
            current_row = recent_df.iloc[i]
            current_date = recent_df.index[i]
            
            # 條件 1: 創 30 日新高 且 漲停 (>= 9.8%)
            is_new_high = current_row['High'] >= current_row['High_30_Prev']
            is_limit_up = current_row['Price_Change'] >= 0.098 
            
            if is_new_high and is_limit_up:
                # 條件 2: 拉回 5 日線不破 (10天內)
                signal_idx = df.index.get_loc(current_date)
                post_df = df.iloc[signal_idx + 1 : signal_idx + 11]
                
                for j in range(len(post_df)):
                    after_row = post_df.iloc[j]
                    after_date = post_df.index[j]
                    
                    if pd.notna(after_row['MA5']):
                        touched_ma5 = after_row['Low'] <= (after_row['MA5'] * 1.005)
                        held_ma5 = after_row['Close'] >= after_row['MA5']
                        
                        if touched_ma5 and held_ma5:
                            results.append({
                                '代號': symbol.split('.')[0],
                                '名稱': name,
                                '突破日期': current_date.strftime('%Y-%m-%d'),
                                '突破價格': round(float(current_row['Close']), 2),
                                '拉回日期': after_date.strftime('%Y-%m-%d'),
                                '拉回價格': round(float(after_row['Close']), 2),
                                '當日MA5': round(float(after_row['MA5']), 2)
                            })
                            break 
        return results if results else None
    except Exception:
        return None

def main():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=300) 
    
    stocks = get_all_taiwan_stock_codes()
    batch_size = 50
    final_matches = []
    
    print(f"開始分批下載與篩選 (每批 {batch_size} 檔)...")
    
    # 將標的分組
    stock_batches = [stocks[i:i + batch_size] for i in range(0, len(stocks), batch_size)]
    
    for i, batch in enumerate(tqdm(stock_batches, desc="批次進度")):
        batch_symbols = [s[0] for s in batch]
        symbol_map = {s[0]: s[1] for s in batch}
        
        try:
            # 批次下載
            df_all = yf.download(batch_symbols, start=start_date.strftime('%Y-%m-%d'), 
                                 end=end_date.strftime('%Y-%m-%d'), progress=False, 
                                 auto_adjust=False, threads=True)
            
            if df_all.empty:
                continue
                
            # 遍歷批次中的每個標的，從 MultiIndex 中正確提取
            for symbol in batch_symbols:
                try:
                    # 只有一個標案時 yf 不會回傳 MultiIndex
                    if len(batch_symbols) == 1:
                        df_stock = df_all
                    else:
                        # 正確提取單一股票的所有價格欄位
                        if symbol in df_all.columns.get_level_values(1):
                            df_stock = df_all.xs(symbol, level=1, axis=1)
                        else:
                            continue
                            
                    res = process_dataframe(df_stock, symbol, symbol_map[symbol])
                    if res:
                        final_matches.extend(res)
                except Exception:
                    continue
            
            # 稍微間隔避免頻繁存取
            # time.sleep(random.uniform(0.5, 1.0))
            
        except Exception as e:
            print(f"\n批次 {i+1} 下載失敗: {e}")
            continue
                
    if final_matches:
        df_final = pd.DataFrame(final_matches)
        df_final = df_final.sort_values(by=['突破日期', '代號'], ascending=[False, True])
        
        output_file = f"taiwan_stock_screen_final_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        df_final.to_excel(output_file, index=False)
        
        print("\n" + "="*80)
        print(f"篩選完成！共找到 {len(df_final)} 次訊號。")
        # 顯示台積電 2330 若有的話，特別驗證其價格
        tsmc_res = df_final[df_final['代號'] == '2330']
        if not tsmc_res.empty:
            print("\n[驗證] 台積電 (2330) 篩選結果：")
            print(tsmc_res.to_string(index=False))
        
        print("\n最新前 20 筆結果：")
        print(df_final.head(20).to_string(index=False))
        print("="*80)
        print(f"成果已存至: {output_file}")
    else:
        print("\n沒找到符合條件的標的。")

if __name__ == "__main__":
    main()
