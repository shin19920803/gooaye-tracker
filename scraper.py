import requests
from bs4 import BeautifulSoup
import yfinance as yf
import json
import datetime
import os
import re
import time
from urllib.parse import urlparse, parse_qs

# 擴充版股票資料庫 (涵蓋主要美股/台股科技股與半導體股)
STOCK_DATABASE = {
    "台積電": "2330.TW", "台積": "2330.TW", "TSMC": "2330.TW",
    "聯電": "2303.TW", "鴻海": "2317.TW", "長榮": "2603.TW",
    "聯發科": "2454.TW", "廣達": "2382.TW", "緯創": "3231.TW", "技嘉": "2376.TW",
    "世界先進": "5347.TW", "大中": "6435.TW", "國巨": "2327.TW", "欣興": "3037.TW",
    "世芯": "3661.TW", "創意": "3443.TW", "智原": "3035.TW", "台達電": "2308.TW",
    "信驊": "5274.TW", "智邦": "2345.TW", "健策": "3653.TW", "川湖": "2059.TW",
    "奇鋐": "3017.TW", "雙鴻": "3324.TW", "神達": "2370.TW", "英業達": "2356.TW",
    "金像電": "2368.TW", 
    "Nvidia": "NVDA", "輝達": "NVDA", "NVDA": "NVDA",
    "Apple": "AAPL", "蘋果": "AAPL", "AAPL": "AAPL",
    "Tesla": "TSLA", "特斯拉": "TSLA", "TSLA": "TSLA",
    "Marvell": "MRVL", "MRVL": "MRVL",
    "AMD": "AMD", "Microsoft": "MSFT", "微軟": "MSFT", 
    "Google": "GOOGL", "谷歌": "GOOGL", "GOOGL": "GOOGL",
    "Amazon": "AMZN", "亞馬遜": "AMZN", "Meta": "META", 
    "美光": "MU", "MU": "MU", "Vishay": "VSH", "VSH": "VSH",
    "Broadcom": "AVGO", "博通": "AVGO", "AVGO": "AVGO",
    "Supermicro": "SMCI", "SMCI": "SMCI", "ASML": "ASML",
    "Intel": "INTC", "英特爾": "INTC"
}

def get_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        if hist.empty:
            return None
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

def search_netizen_links(ep_num):
    """
    使用 DuckDuckGo HTML 版搜尋有關該集股癌筆記的網頁、部落格或論壇文章
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    
    # 建構多個搜尋關鍵字，提高涵蓋度
    queries = [f"股癌 EP{ep_num}", f"股癌 {ep_num} 筆記"]
    links = []
    
    for q in queries:
        url = f"https://html.duckduckgo.com/html/?q={q}"
        try:
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                for a in soup.select('a.result__url'):
                    href = a.get('href', '')
                    if 'uddg=' in href:
                        real_url = parse_qs(urlparse(href).query).get('uddg', [None])[0]
                        if real_url and real_url not in links:
                            links.append(real_url)
            time.sleep(0.3)
        except Exception as e:
            print(f"Error searching DuckDuckGo for '{q}': {e}")
            
    # 過濾連結，排除聲音平台與無關網站
    filtered = []
    for l in links:
        l_lower = l.lower()
        if any(k in l_lower for k in [
            'youtube.com', 'spotify.com', 'apple.com', 'podcast', 'facebook.com', 
            'instagram.com', 'threads.net', 'twitter.com', 'x.com', 'duckduckgo.com',
            'google.com', 'soundon.fm', 'kkbox.com', 'wikipedia.org', 'bing.com'
        ]):
            continue
        filtered.append(l)
        
    return filtered

def extract_stocks_from_url(url, headers):
    """
    爬取特定 URL 的內文並分析提及的股票
    """
    try:
        # 設定較短的 timeout 避免卡死
        res = requests.get(url, headers=headers, timeout=5)
        res.encoding = 'utf-8'
        if res.status_code != 200:
            return []
            
        soup = BeautifulSoup(res.text, 'html.parser')
        # 移除 scripts 跟 styles
        for s in soup(["script", "style"]):
            s.decompose()
            
        text = soup.get_text()
        
        found = []
        # 掃描比對資料庫
        for name, ticker in STOCK_DATABASE.items():
            # 使用簡單的比對，如果出現就記錄
            if name in text:
                found.append((name, ticker))
        return found
    except Exception as e:
        print(f"Error parsing content from {url}: {e}")
        return []

def scrape_episodes():
    # 1. 爬取股癌筆記首頁以取得最新集數連結
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
    episode_elements = soup.select('h2.wp-block-post-title a')
    
    episodes_to_scrape = []
    for el in episode_elements[:10]: # 預設抓取前 10 集
        title = el.text.strip()
        url = el.get('href')
        episodes_to_scrape.append((title, url))
        
    results = []
    price_cache = {}
    
    for title, original_url in episodes_to_scrape:
        # 解析集數數字 (例如 "股癌筆記EP672" -> "672")
        match = re.search(r'(?:EP|ep)?\s*(\d+)', title)
        ep_num = match.group(1) if match else None
        
        print(f"\n========== Processing Episode: {title} (EP {ep_num}) ==========")
        
        # 收集來源網頁清單
        candidate_urls = [original_url]
        
        # 2. 如果有集數數字，則上網搜尋其他網友/筆記來源
        if ep_num:
            print(f"Searching web for additional notes on EP {ep_num}...")
            search_links = search_netizen_links(ep_num)
            for link in search_links[:3]: # 取前 3 個外部搜尋連結，避免過度爬取
                if link not in candidate_urls:
                    candidate_urls.append(link)
        
        # 3. 爬取所有來源並聚合股票
        found_stocks_map = {}
        successful_sources = []
        
        print(f"Sources to crawl for EP {ep_num}: {candidate_urls}")
        
        for url in candidate_urls:
            time.sleep(0.3) # 禮貌延遲
            print(f"Crawling source: {url}")
            stocks_found = extract_stocks_from_url(url, headers)
            if stocks_found:
                successful_sources.append(url)
                for name, ticker in stocks_found:
                    # 避免同個股票因不同名稱重複出現在同一集（例如「台積電」與「TSMC」）
                    # 統一以 ticker 代碼為 key
                    if ticker not in found_stocks_map:
                        found_stocks_map[ticker] = {
                            "name": name,
                            "ticker": ticker
                        }
                    # 偏好使用中文或較長的名字作為顯示名稱
                    elif len(name) > len(found_stocks_map[ticker]["name"]):
                        found_stocks_map[ticker]["name"] = name

        # 4. 對本集所有提及的股票抓取即時價格
        final_stocks = []
        for ticker, s_info in found_stocks_map.items():
            if ticker not in price_cache:
                info = get_stock_info(ticker)
                if info:
                    price_cache[ticker] = info
            
            if ticker in price_cache:
                final_stocks.append({
                    "name": s_info["name"],
                    "ticker": ticker,
                    "current_price": price_cache[ticker]["current_price"],
                    "change": price_cache[ticker]["change"]
                })
        
        # 5. 解析發布日期 (從原部落格頁面)
        pub_date = datetime.datetime.now().strftime("%Y-%m-%d")
        try:
            ep_res = requests.get(original_url, headers=headers, timeout=5)
            if ep_res.status_code == 200:
                ep_soup = BeautifulSoup(ep_res.text, 'html.parser')
                date_meta = ep_soup.find('meta', property='article:published_time')
                if date_meta:
                    pub_date = date_meta.get('content')[:10]
        except Exception as e:
            print(f"Error fetching date from original post: {e}")
            
        results.append({
            "episode": title,
            "url": original_url,
            "date": pub_date,
            "stocks": final_stocks,
            "sources": successful_sources # 記錄成功的分析來源提供前端顯示
        })
        print(f"Finished EP {ep_num}. Found stocks: {[s['name'] for s in final_stocks]}")
            
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
        
    # 寫入 CSV 檔案
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
    print("Starting Gooaye Multi-Source Search Scraper...")
    results = scrape_episodes()
    os.makedirs('docs', exist_ok=True)
    with open('docs/data.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print("Episode search scraping completed.")
    
    print("Starting Portfolio PnL Calculation...")
    calculate_portfolio()
    print("All tasks completed.")
