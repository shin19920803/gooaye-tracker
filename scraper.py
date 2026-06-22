import requests
from bs4 import BeautifulSoup
import yfinance as yf
import json
import datetime
import os
import re

# 強化版股票名稱與代碼對照表 (這部分您可以持續手動增加)
STOCK_DATABASE = {
    "台積電": "2330.TW", "聯電": "2303.TW", "鴻海": "2317.TW", "長榮": "2603.TW",
    "聯發科": "2454.TW", "廣達": "2382.TW", "緯創": "3231.TW", "技嘉": "2376.TW",
    "Nvidia": "NVDA", "輝達": "NVDA", "Apple": "AAPL", "蘋果": "AAPL",
    "Tesla": "TSLA", "特斯拉": "TSLA", "Marvell": "MRVL", "AMD": "AMD",
    "Microsoft": "MSFT", "微軟": "MSFT", "Google": "GOOGL", "谷歌": "GOOGL",
    "Amazon": "AMZN", "亞馬遜": "AMZN", "Meta": "META", "美光": "MU"
}

def get_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        if hist.empty:
            return None
        # 確保數值為原生 Python float，避免 JSON 序列化錯誤
        curr_price = float(hist['Close'].iloc[-1])
        prev_price = float(hist['Close'].iloc[-2])
        change_pct = ((curr_price - prev_price) / prev_price) * 100
        return {
            "current_price": round(curr_price, 2),
            "change": f"{round(change_pct, 2)}%",
            "change_val": round(curr_price - prev_price, 2),
            "previous_close": round(prev_price, 2)
        }
    except Exception as e:
        print(f"Error fetching stock info for {ticker}: {e}")
        return None

def scrape_episodes():
    # 爬取股癌筆記首頁以取得最新集數連結
    index_url = "https://socialworkerdaily.com/index/invest/notes-of-gooaye/ep-600-to-700/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    
    try:
        res = requests.get(index_url, headers=headers)
        res.encoding = 'utf-8'
        if res.status_code != 200:
            print(f"Failed to fetch index page: {res.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching index page: {e}")
        return []
        
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # 獲取最新 5 個單集連結與標題
    episode_elements = soup.select('h2.wp-block-post-title a')
    episodes_to_scrape = []
    for el in episode_elements[:5]:
        title = el.text.strip()
        url = el.get('href')
        episodes_to_scrape.append((title, url))
        
    results = []
    price_cache = {}
    
    for title, url in episodes_to_scrape:
        print(f"Scraping episode: {title} ({url})")
        try:
            ep_res = requests.get(url, headers=headers)
            ep_res.encoding = 'utf-8'
            if ep_res.status_code != 200:
                print(f"Failed to fetch episode page {title}: {ep_res.status_code}")
                continue
        except Exception as e:
            print(f"Error fetching episode page {title}: {e}")
            continue
            
        ep_soup = BeautifulSoup(ep_res.text, 'html.parser')
        paragraphs = [p.get_text().strip() for p in ep_soup.select('div.entry-content p, div.kv-page-content p') if p.get_text().strip()]
        
        found_stocks = {}
        for p in paragraphs:
            for name, ticker in STOCK_DATABASE.items():
                if name in p:
                    if name not in found_stocks:
                        if ticker not in price_cache:
                            info = get_stock_info(ticker)
                            if info:
                                price_cache[ticker] = info
                        
                        if ticker in price_cache:
                            found_stocks[name] = {
                                "name": name,
                                "ticker": ticker,
                                "current_price": price_cache[ticker]["current_price"],
                                "change": price_cache[ticker]["change"]
                            }
                            
        if found_stocks:
            results.append({
                "episode": title,
                "url": url,
                "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "stocks": list(found_stocks.values())
            })
            
    return results

def calculate_portfolio():
    portfolio_file = "portfolio.json"
    if not os.path.exists(portfolio_file):
        print("portfolio.json not found, skipping portfolio calculation.")
        return
        
    try:
        with open(portfolio_file, "r", encoding="utf-8") as f:
            portfolio = json.load(f)
    except Exception as e:
        print(f"Error loading portfolio.json: {e}")
        return
        
    assets = []
    total_cost = 0.0
    total_value = 0.0
    total_daily_pnl = 0.0
    
    print("Calculating portfolio PnL...")
    price_cache = {}
    
    for item in portfolio:
        symbol = item.get("symbol")
        buy_price = float(item.get("buy_price", 0.0))
        shares = float(item.get("shares", 0.0))
        name = item.get("name", symbol)
        
        if symbol not in price_cache:
            info = get_stock_info(symbol)
            if info:
                price_cache[symbol] = info
                
        if symbol not in price_cache:
            print(f"Could not get price data for portfolio item: {symbol}")
            continue
            
        info = price_cache[symbol]
        current_price = info["current_price"]
        prev_close = info["previous_close"]
        
        cost = buy_price * shares
        value = current_price * shares
        pnl = value - cost
        pnl_pct = (pnl / cost * 100) if cost > 0 else 0.0
        
        daily_pnl = (current_price - prev_close) * shares
        daily_change_pct = float(info["change"].replace("%", ""))
        
        total_cost += cost
        total_value += value
        total_daily_pnl += daily_pnl
        
        assets.append({
            "symbol": symbol,
            "name": name,
            "buy_price": round(buy_price, 2),
            "shares": round(shares, 2),
            "current_price": round(current_price, 2),
            "previous_close": round(prev_close, 2),
            "cost": round(cost, 2),
            "value": round(value, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": f"{round(pnl_pct, 2)}%",
            "daily_pnl": round(daily_pnl, 2),
            "daily_change_pct": f"{round(daily_change_pct, 2)}%"
        })
        
    total_pnl = total_value - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0.0
    total_daily_change_pct = (total_daily_pnl / total_cost * 100) if total_cost > 0 else 0.0
    
    portfolio_pnl = {
        "summary": {
            "total_cost": round(total_cost, 2),
            "total_value": round(total_value, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": f"{round(total_pnl_pct, 2)}%",
            "total_daily_pnl": round(total_daily_pnl, 2),
            "total_daily_change_pct": f"{round(total_daily_change_pct, 2)}%",
            "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "assets": assets
    }
    
    # 寫入 JSON 檔案
    os.makedirs('docs', exist_ok=True)
    with open('docs/portfolio_pnl.json', 'w', encoding='utf-8') as f:
        json.dump(portfolio_pnl, f, ensure_ascii=False, indent=4)
        
    # 寫入 CSV 檔案 (可直接拉入 Google Drive)
    import csv
    with open('docs/portfolio_pnl.csv', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["類別", "數值"])
        writer.writerow(["總持股成本", round(total_cost, 2)])
        writer.writerow(["目前總市值", round(total_value, 2)])
        writer.writerow(["累積損益額", round(total_pnl, 2)])
        writer.writerow(["累積回報率", f"{round(total_pnl_pct, 2)}%"])
        writer.writerow(["今日損益額", round(total_daily_pnl, 2)])
        writer.writerow(["今日回報率", f"{round(total_daily_change_pct, 2)}%"])
        writer.writerow(["更新時間", portfolio_pnl["summary"]["update_time"]])
        writer.writerow([])
        
        writer.writerow(["股票代碼", "股票名稱", "買入均價", "持有股數", "當前股價", "昨日收盤價", "投資成本", "目前市值", "累積損益", "累積回報率", "今日損益", "今日回報率"])
        for asset in assets:
            writer.writerow([
                asset["symbol"],
                asset["name"],
                asset["buy_price"],
                asset["shares"],
                asset["current_price"],
                asset["previous_close"],
                asset["cost"],
                asset["value"],
                asset["pnl"],
                asset["pnl_pct"],
                asset["daily_pnl"],
                asset["daily_change_pct"]
            ])
            
    print("Portfolio PnL reports generated successfully!")

if __name__ == "__main__":
    print("Starting Gooaye Scraper...")
    results = scrape_episodes()
    os.makedirs('docs', exist_ok=True)
    with open('docs/data.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print("Episode scraping completed.")
    
    print("Starting Portfolio PnL Calculation...")
    calculate_portfolio()
    print("All tasks completed.")
