import requests
from bs4 import BeautifulSoup
import yfinance as yf
import json
import datetime
import os
import re

# 強化版股票名稱與代碼對照表 (這部分你可以持續手動增加)
STOCK_DATABASE = {
    "台積電": "2330.TW", "聯電": "2303.TW", "鴻海": "2317.TW", "長榮": "2603.TW",
    "Nvidia": "NVDA", "輝達": "NVDA", "Apple": "AAPL", "蘋果": "AAPL",
    "Tesla": "TSLA", "特斯拉": "TSLA", "Marvell": "MRVL", "AMD": "AMD"
}

def get_stock_info(name):
    ticker = STOCK_DATABASE.get(name)
    if not ticker: return None
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        if hist.empty: return None
        return {
            "ticker": ticker,
            "current_price": round(hist['Close'].iloc[-1], 2),
            "change": f"{round(((hist['Close'].iloc[-1] - hist['Close'].iloc[-2])/hist['Close'].iloc[-2])*100, 2)}%"
        }
    except: return None

def scrape():
    # 爬取股癌筆記
    url = "https://socialworkerdaily.com/index/invest/notes-of-gooaye/ep-600-to-700/"
    res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    
    data = []
    # 根據網站結構抓取集數內容
    entries = soup.select('div.entry-content p')
    current_ep = "最新集數"
    
    # 簡易關鍵字匹配邏輯
    for p in entries[:50]: # 掃描前 50 段文字
        text = p.get_text()
        found_stocks = []
        for name in STOCK_DATABASE.keys():
            if name in text:
                info = get_stock_info(name)
                if info:
                    found_stocks.append({"name": name, **info})
        
        if found_stocks:
            data.append({
                "episode": current_ep,
                "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "stocks": found_stocks
            })
            break # 範例僅抓取最新一集提及的
            
    return data

if __name__ == "__main__":
    results = scrape()
    os.makedirs('docs', exist_ok=True)
    with open('docs/data.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
