import yfinance as yf
import pandas as pd
import twstock
from datetime import datetime, timedelta
import os
import warnings
import time
import random
import sys

# SSL 憑證路徑修正 (Render 環境會自動處理，本地端如有需要請在此設定)
# if os.path.exists(r'C:\Users\ASUS\cacert.pem'):
#     os.environ['SSL_CERT_FILE'] = r'C:\Users\ASUS\cacert.pem'


warnings.filterwarnings('ignore')

class ScannerEngine:
    def __init__(self):
        self.stocks = []
        
    def get_taiwan_stock_codes(self):
        """取得所有上市上櫃股票代號"""
        codes = twstock.codes
        tse_otc_codes = []
        for code, info in codes.items():
            if info.market in ['上市', '上櫃'] and len(code) == 4 and code.isdigit():
                suffix = ".TW" if info.market == '上市' else ".TWO"
                tse_otc_codes.append((f"{code}{suffix}", info.name))
        return tse_otc_codes

    def process_dataframe(self, df, symbol, name):
        """處理單一股票的 DataFrame 並篩選條件"""
        try:
            required_cols = ['Open', 'High', 'Low', 'Close']
            if not all(col in df.columns for col in required_cols):
                return None
                
            df = df[required_cols].copy()
            df.dropna(subset=['Close'], inplace=True)
            
            if len(df) < 40:
                return None
                
            df['Prev_Close'] = df['Close'].shift(1)
            df['Price_Change'] = (df['Close'] - df['Prev_Close']) / df['Prev_Close']
            df['High_30_Prev'] = df['High'].shift(1).rolling(window=30).max()
            df['MA5'] = df['Close'].rolling(window=5).mean()
            
            cutoff_date = (datetime.now() - timedelta(days=180)).date()
            df.dropna(subset=['MA5', 'High_30_Prev', 'Price_Change'], inplace=True)
            recent_df = df[df.index.date >= cutoff_date]
            
            results = []
            for i in range(len(recent_df)):
                current_row = recent_df.iloc[i]
                current_date = recent_df.index[i]
                
                is_new_high = current_row['High'] >= current_row['High_30_Prev']
                is_limit_up = current_row['Price_Change'] >= 0.098 
                
                if is_new_high and is_limit_up:
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
                                    'symbol': symbol.split('.')[0],
                                    'name': name,
                                    'breakout_date': current_date.strftime('%Y-%m-%d'),
                                    'breakout_price': round(float(current_row['Close']), 2),
                                    'pullback_date': after_date.strftime('%Y-%m-%d'),
                                    'pullback_price': round(float(after_row['Close']), 2),
                                    'ma5_price': round(float(after_row['MA5']), 2)
                                })
                                break 
            return results
        except Exception:
            return None

    async def run_scan(self, progress_callback=None):
        """執行完整掃描"""
        stocks = self.get_taiwan_stock_codes()
        batch_size = 50
        final_matches = []
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=300)
        
        stock_batches = [stocks[i:i + batch_size] for i in range(0, len(stocks), batch_size)]
        
        for i, batch in enumerate(stock_batches):
            if progress_callback:
                await progress_callback(i + 1, len(stock_batches))
                
            batch_symbols = [s[0] for s in batch]
            symbol_map = {s[0]: s[1] for s in batch}
            
            try:
                df_all = yf.download(batch_symbols, start=start_date.strftime('%Y-%m-%d'), 
                                     end=end_date.strftime('%Y-%m-%d'), progress=False, 
                                     auto_adjust=False, threads=True)
                
                if df_all.empty:
                    continue
                    
                for symbol in batch_symbols:
                    try:
                        if len(batch_symbols) == 1:
                            df_stock = df_all
                        else:
                            if symbol in df_all.columns.get_level_values(1):
                                df_stock = df_all.xs(symbol, level=1, axis=1)
                            else:
                                continue
                                
                        res = self.process_dataframe(df_stock, symbol, symbol_map[symbol])
                        if res:
                            final_matches.extend(res)
                    except Exception:
                        continue
            except Exception:
                continue
                
        return final_matches
