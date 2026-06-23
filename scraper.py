import requests
from bs4 import BeautifulSoup
import yfinance as yf
import json
import datetime
import os
import re
import time
from urllib.parse import urlparse, parse_qs, unquote
import csv

# 擴充版熱門美股/ETF資料庫 (150+ 檔，包含 Magnificant 7、半導體供應鏈、科技成長股與熱門 ETF)
US_STOCK_DATABASE = {
    # Magnificant 7
    "NVDA": {"name": "輝達", "aliases": ["Nvidia", "輝達", "NVDA"]},
    "AAPL": {"name": "蘋果", "aliases": ["Apple", "蘋果", "AAPL"]},
    "TSLA": {"name": "特斯拉", "aliases": ["Tesla", "特斯拉", "TSLA"]},
    "MSFT": {"name": "微軟", "aliases": ["Microsoft", "微軟", "MSFT"]},
    "GOOGL": {"name": "谷歌", "aliases": ["Google", "谷歌", "GOOGL", "GOOG"]},
    "GOOG": {"name": "谷歌", "aliases": ["Google", "谷歌", "GOOGL", "GOOG"]},
    "AMZN": {"name": "亞馬遜", "aliases": ["Amazon", "亞馬遜", "AMZN"]},
    "META": {"name": "Meta", "aliases": ["Meta", "臉書", "Facebook", "META"]},
    
    # 半導體、硬體與軟體巨人
    "AMD": {"name": "超微", "aliases": ["AMD", "超微"]},
    "AVGO": {"name": "博通", "aliases": ["Broadcom", "博通", "AVGO"]},
    "MRVL": {"name": "邁威爾", "aliases": ["Marvell", "邁威爾", "MRVL"]},
    "VSH": {"name": "威世", "aliases": ["Vishay", "威世", "VSH"]},
    "MU": {"name": "美光", "aliases": ["MU", "美光", "Micron"]},
    "ARM": {"name": "安謀", "aliases": ["ARM", "安謀"]},
    "SMCI": {"name": "超微電腦", "aliases": ["Supermicro", "超微電腦", "SMCI"]},
    "ASML": {"name": "艾司摩爾", "aliases": ["ASML", "艾司摩爾"]},
    "INTC": {"name": "英特爾", "aliases": ["Intel", "英特爾", "INTC"]},
    "QCOM": {"name": "高通", "aliases": ["Qualcomm", "高通", "QCOM"]},
    "TSM": {"name": "台積電ADR", "aliases": ["TSM", "台積電ADR"]},
    "TXN": {"name": "德州儀器", "aliases": ["TXN", "德儀", "德州儀器"]},
    "ADI": {"name": "亞德諾", "aliases": ["ADI", "亞德諾"]},
    "NXPI": {"name": "恩智浦", "aliases": ["NXPI", "恩智浦"]},
    "ON": {"name": "安森美", "aliases": ["ON Semi", "安森美", "ON"]},
    "MCHP": {"name": "微晶片科技", "aliases": ["MCHP", "微晶片科技", "Microchip"]},
    "COHR": {"name": "科休", "aliases": ["Coherent", "科休", "COHR"]},
    "LRCX": {"name": "科林研發", "aliases": ["Lam Research", "科林研發", "LRCX"]},
    "AMAT": {"name": "應用材料", "aliases": ["Applied Materials", "應用材料", "AMAT"]},
    "KLAC": {"name": "科磊", "aliases": ["KLA", "科磊", "KLAC"]},
    "SNPS": {"name": "新思科技", "aliases": ["Synopsys", "新思科技", "SNPS"]},
    "CDNS": {"name": "益華電腦", "aliases": ["Cadence", "益華電腦", "CDNS"]},
    "PLTR": {"name": "Palantir", "aliases": ["Palantir", "PLTR"]},
    "NFLX": {"name": "網飛", "aliases": ["Netflix", "網飛", "NFLX"]},
    "ORCL": {"name": "甲骨文", "aliases": ["Oracle", "甲骨文", "ORCL"]},
    "CRM": {"name": "賽富時", "aliases": ["Salesforce", "賽富時", "CRM"]},
    "NOW": {"name": "ServiceNow", "aliases": ["ServiceNow", "NOW"]},
    "PANW": {"name": "Palo Alto", "aliases": ["Palo Alto", "PANW"]},
    "CRWD": {"name": "CrowdStrike", "aliases": ["CrowdStrike", "CRWD"]},
    "DDOG": {"name": "Datadog", "aliases": ["Datadog", "DDOG"]},
    "NET": {"name": "Cloudflare", "aliases": ["Cloudflare", "NET"]},
    "SNOW": {"name": "Snowflake", "aliases": ["Snowflake", "SNOW"]},
    "MDB": {"name": "MongoDB", "aliases": ["MongoDB", "MDB"]},
    "U": {"name": "Unity", "aliases": ["Unity", "U"]},
    "COIN": {"name": "Coinbase", "aliases": ["Coinbase", "COIN"]},
    
    # 金融、醫療、零售、生技與其他
    "BRK.B": {"name": "波克夏", "aliases": ["Berkshire", "波克夏", "BRK.B", "BRK.A"]},
    "LLY": {"name": "禮來", "aliases": ["Eli Lilly", "禮來", "LLY"]},
    "NVO": {"name": "諾和諾德", "aliases": ["Novo Nordisk", "諾和諾德", "NVO"]},
    "V": {"name": "Visa", "aliases": ["Visa", "V"]},
    "MA": {"name": "萬事達卡", "aliases": ["Mastercard", "萬事達卡", "MA"]},
    "JPM": {"name": "摩根大通", "aliases": ["JPMorgan", "小摩", "摩根大通", "JPM"]},
    "MS": {"name": "摩根士丹利", "aliases": ["Morgan Stanley", "大摩", "摩根士丹利", "MS"]},
    "GS": {"name": "高盛", "aliases": ["Goldman Sachs", "高盛", "GS"]},
    "BAC": {"name": "美國銀行", "aliases": ["Bank of America", "美銀", "BAC"]},
    "WMT": {"name": "沃爾瑪", "aliases": ["Walmart", "沃爾瑪", "WMT"]},
    "PG": {"name": "寶僑", "aliases": ["P&G", "寶僑", "PG"]},
    "COST": {"name": "好市多", "aliases": ["Costco", "好市多", "COST"]},
    "HD": {"name": "家得寶", "aliases": ["Home Depot", "家得寶", "HD"]},
    "DIS": {"name": "迪士尼", "aliases": ["Disney", "迪士尼", "DIS"]},
    "NKE": {"name": "Nike", "aliases": ["Nike", "耐吉", "NKE"]},
    "SBUX": {"name": "星巴克", "aliases": ["Starbucks", "星巴克", "SBUX"]},
    "XOM": {"name": "埃克森美孚", "aliases": ["Exxon", "埃克森美孚", "XOM"]},
    "CVX": {"name": "雪佛龍", "aliases": ["Chevron", "雪佛龍", "CVX"]},
    
    # 熱門 ETF
    "SPY": {"name": "S&P 500 ETF", "aliases": ["SPY"]},
    "VOO": {"name": "Vanguard S&P 500", "aliases": ["VOO"]},
    "QQQ": {"name": "Nasdaq 100 ETF", "aliases": ["QQQ"]},
    "SOXX": {"name": "半導體 ETF", "aliases": ["SOXX", "費半 ETF"]},
    "SOXL": {"name": "三倍做多半導體", "aliases": ["SOXL", "費半三倍"]},
    "TLT": {"name": "美債 20年 ETF", "aliases": ["TLT", "美債20年"]}
}

def fetch_taiwan_stocks():
    """
    動態下載並快取台灣證交所 (TWSE) 與櫃買中心 (TPEx) 的最新上市櫃股票代碼與名稱清單
    """
    cache_path = os.path.join('docs', 'taiwan_stocks.json')
    if os.path.exists(cache_path):
        mtime = os.path.getmtime(cache_path)
        age_days = (time.time() - mtime) / (24 * 3600)
        if age_days < 7:
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    print("Loading Taiwan stocks from local cache...")
                    return json.load(f)
            except Exception as e:
                print(f"Error reading Taiwan stocks cache: {e}")

    print("Fetching latest Taiwan stocks from TWSE and TPEx...")
    stocks = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # 1. Listed (TWSE) -> 寫入 .TW 尾綴
    twse_url = 'https://isin.twse.com.tw/isin/C_public.jsp?strMode=2'
    try:
        res = requests.get(twse_url, headers=headers, timeout=10)
        res.encoding = 'big5'
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            rows = soup.select('table tr')
            for row in rows:
                tds = row.select('td')
                if len(tds) > 0:
                    text = tds[0].text.strip()
                    parts = text.split('\u3000')
                    if len(parts) == 2:
                        code, name = parts[0], parts[1]
                        if len(code) == 4 and code.isdigit():
                            stocks[code] = {
                                "name": name,
                                "ticker": f"{code}.TW"
                            }
    except Exception as e:
        print(f"Error fetching TWSE stocks: {e}")

    # 2. OTC (TPEx) -> 櫃買中心股票在 yfinance 必須使用 .TWO 尾綴
    tpex_url = 'https://isin.twse.com.tw/isin/C_public.jsp?strMode=4'
    try:
        res = requests.get(tpex_url, headers=headers, timeout=10)
        res.encoding = 'big5'
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            rows = soup.select('table tr')
            for row in rows:
                tds = row.select('td')
                if len(tds) > 0:
                    text = tds[0].text.strip()
                    parts = text.split('\u3000')
                    if len(parts) == 2:
                        code, name = parts[0], parts[1]
                        if len(code) == 4 and code.isdigit():
                            stocks[code] = {
                                "name": name,
                                "ticker": f"{code}.TWO"
                            }
    except Exception as e:
        print(f"Error fetching TPEx stocks: {e}")

    if stocks:
        try:
            os.makedirs('docs', exist_ok=True)
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(stocks, f, ensure_ascii=False, indent=4)
            print(f"Saved {len(stocks)} Taiwan stocks to cache.")
        except Exception as e:
            print(f"Error caching Taiwan stocks: {e}")
            
    return stocks

def get_source_name(url):
    """
    自訂出處網址之友善顯示名稱
    """
    parsed = urlparse(url)
    domain = parsed.hostname or ""
    domain = domain.replace("www.", "")
    if "ptt.cc" in domain:
        return "PTT 股板"
    elif "socialworkerdaily.com" in domain:
        return "股癌官方筆記"
    elif "gdinvestornotes.substack.com" in domain:
        return "Substack 股人筆記"
    elif "yasac.substack.com" in domain:
        return "Substack 呀沙係"
    elif "mugglestock.com" in domain:
        return "麻瓜投資"
    elif "jacksu.tw" in domain:
        return "蘇家禹筆記"
    elif "whatmkreallysaid.com" in domain:
        return "股癌逐字稿"
    elif "substack.com" in domain:
        parts = domain.split('.')
        if len(parts) >= 3:
            return f"Substack {parts[0]}"
        return "Substack"
    return domain

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
    搜尋 Yahoo Search 與 DuckDuckGo 以取得網友討論、分析筆記與 PTT 論壇文章
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    
    queries = [
        f"股癌 EP{ep_num} 筆記",
        f"股癌 EP{ep_num} PTT",
        f"股癌 EP{ep_num} 暗示",
        f"site:ptt.cc 股癌 EP{ep_num}"
    ]
    links = []
    
    # 1. Yahoo Search (第一順位，穩定性最高，不跳機器人挑戰)
    for q in queries:
        url = 'https://search.yahoo.com/search'
        try:
            res = requests.get(url, params={'p': q}, headers=headers, timeout=5)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                for a in soup.select('a'):
                    href = a.get('href', '')
                    if 'r.search.yahoo.com' in href:
                        match = re.search(r'/RU=([^/]+)', href)
                        if match:
                            real_url = unquote(match.group(1))
                            if real_url and real_url not in links:
                                links.append(real_url)
                    elif href.startswith('http') and not any(k in href for k in ['yahoo.com', 'yahoo.co', 'yimg.com']):
                        if href not in links:
                            links.append(href)
            time.sleep(0.3)
        except Exception as e:
            print(f"Yahoo Search error for '{q}': {e}")
            
    # 2. DuckDuckGo HTML 版 (備用，但若出現 202 挑戰則跳過)
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
            elif res.status_code == 202:
                print(f"DuckDuckGo returned challenge page for '{q}', skipping DDG backup.")
            time.sleep(0.3)
        except Exception as e:
            print(f"DuckDuckGo Search error for '{q}': {e}")
            
    # 過濾與整理連結
    filtered = []
    for l in links:
        l_lower = l.lower()
        if any(k in l_lower for k in [
            'youtube.com', 'spotify.com', 'apple.com', 'podcast', 'facebook.com', 
            'instagram.com', 'threads.net', 'twitter.com', 'x.com', 'duckduckgo.com',
            'google.com', 'soundon.fm', 'kkbox.com', 'wikipedia.org', 'bing.com',
            'yahoo.com', 'yahoo.co', 'yimg.com', 'uservoice.com', 'help.yahoo'
        ]):
            continue
        if not l.startswith('http'):
            continue
        filtered.append(l)
        
    return filtered

def extract_reason_and_filter(text, name, code=None):
    """
    將文本切分成句子，尋找提及 name 或 code 的句子。
    過濾掉顯著看空的句子。如果所有提及該標的之句子均為看空，則返回 None (表示不列出)。
    否則，返回第一條包含推薦/中性理由的句子（限制長度以維持 UI 美觀）。
    """
    # 負面/看空關鍵字
    neg_keywords = [
        "不要買", "別買", "不碰", "不建議", "避開", "看空", "做空", "空它", "空單", 
        "偏空", "高估", "有風險", "逢高出清", "賣出", "放空", "不要碰", "暫不推薦"
    ]
    
    # 使用常見中文及英文標點切分句子
    sentences = re.split(r'[。！？\n\r；;\t]+', text)
    
    matching_sentences = []
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        # 檢查是否提及該股（不區分大小寫）
        mentioned = False
        s_lower = s.lower()
        if name and name.lower() in s_lower:
            mentioned = True
        if code and code.lower() in s_lower:
            mentioned = True
            
        if mentioned:
            matching_sentences.append(s)
            
    if not matching_sentences:
        return None
        
    # 篩選非負面的句子
    valid_reasons = []
    for s in matching_sentences:
        has_neg = any(neg in s for neg in neg_keywords)
        if not has_neg:
            valid_reasons.append(s)
            
    # 如果所有提及的句子都含有看空字眼，則不推薦買入，回傳 None 予以過濾
    if not valid_reasons:
        return None
        
    # 取第一個有效的理由，並將其長度限制在 120 字以內，加上省略號
    best_reason = valid_reasons[0]
    if len(best_reason) > 120:
        best_reason = best_reason[:117] + "..."
        
    return best_reason

def extract_stocks_from_content(text, taiwan_stocks):
    """
    從文章內文中提取美股或台股提及標的，並套用防誤判防碰撞演算法，並篩選出有推薦理由且非看空的標的
    """
    found = []
    text_lower = text.lower()
    
    # 1. 識別美股
    for ticker, info in US_STOCK_DATABASE.items():
        matched = False
        for alias in info["aliases"]:
            if alias.lower() in text_lower:
                # 針對極短的縮寫 (如 ON, U, V)，只在它以大寫且有邊界時進行匹配，且需輔以美股常用關鍵字
                if len(alias) <= 2 and alias.isupper():
                    if re.search(r'\b' + re.escape(alias) + r'\b', text):
                        if alias == 'ON':
                            if '安森美' in text or any(k in text for k in ['美股', '晶片', '二極體', '半導體']):
                                reason = extract_reason_and_filter(text, alias, ticker)
                                if reason:
                                    found.append((info["name"], ticker, reason))
                                    matched = True
                                    break
                        elif alias == 'V':
                            if 'visa' in text_lower or '維薩' in text or any(k in text for k in ['美股', '支付', '信用卡']):
                                reason = extract_reason_and_filter(text, alias, ticker)
                                if reason:
                                    found.append((info["name"], ticker, reason))
                                    matched = True
                                    break
                        elif alias == 'U':
                            if 'unity' in text_lower or any(k in text for k in ['美股', '遊戲引擎', '軟體']):
                                reason = extract_reason_and_filter(text, alias, ticker)
                                if reason:
                                    found.append((info["name"], ticker, reason))
                                    matched = True
                                    break
                        else:
                            reason = extract_reason_and_filter(text, alias, ticker)
                            if reason:
                                found.append((info["name"], ticker, reason))
                                matched = True
                                break
                else:
                    reason = extract_reason_and_filter(text, alias, ticker)
                    if reason:
                        found.append((info["name"], ticker, reason))
                        matched = True
                        break
        if matched:
            continue
            
    # 2. 識別台股
    # 常用詞碰撞名單
    colliding_names = {
        '世界', '開發', '大成', '統一', '中信', '新光', '巨虹', '鉅虹', '高興', 
        '幸福', '大洋', '三商', '富邦', '國泰', '台泥', '亞泥', '味全', '泰山', 
        '大亞', '東元', '聲寶', '佳能', '大立', '喬山', '高林', '長興', '中鋼', 
        '第一', '華南', '合庫', '兆豐', '台企', '彰銀', '萬企', '國產', '欣欣', 
        '天然', '新海', '欣高', '前程'
    }
    
    # 提取文章中所有的4位數字，並過濾掉年份與集數等雜訊
    codes_in_text = set(re.findall(r'\b([1-9]\d{3})\b', text))
    for year in range(2018, 2029):
        codes_in_text.discard(str(year))
        
    for code, s_info in taiwan_stocks.items():
        name = s_info["name"]
        ticker = s_info["ticker"]
        
        # 清理名稱（例如: "世芯-KY" -> "世芯", "國泰金控" -> "國泰金"）
        clean_name = name.split('\u3000')[-1]
        clean_name = clean_name.replace('-KY', '').replace('金控', '金').strip()
        
        name_matched = False
        
        if clean_name in text:
            if clean_name in colliding_names:
                # 若是常用詞碰撞股票，則必須滿足：(1) 代碼同時出現；或 (2) 提及了更具體的公司全名/變體
                if code in codes_in_text:
                    name_matched = True
                elif clean_name == '世界' and '世界先進' in text:
                    name_matched = True
                elif clean_name == '國泰' and ('國泰金' in text or '國泰建設' in text):
                    name_matched = True
                elif clean_name == '富邦' and '富邦金' in text:
                    name_matched = True
                elif clean_name == '開發' and '開發金' in text:
                    name_matched = True
                elif clean_name == '中信' and '中信金' in text:
                    name_matched = True
                elif clean_name == '新光' and '新光金' in text:
                    name_matched = True
                elif clean_name == '大成' and '大成鋼' in text:
                    name_matched = True
            else:
                name_matched = True
                
        # 如果名字沒出現在內文，但有 4 碼代碼，則檢查是否以 (2330)、2330.TW 等帶有股票屬性的形式出現
        if not name_matched and code in codes_in_text:
            pattern = rf'(\({code}\)|\[{code}\]|{code}\.TW|{code}\.TWO|{code}\.tw|{code}\.two|股.*{code}|{code}.*股)'
            if re.search(pattern, text):
                name_matched = True
                
        if name_matched:
            reason = extract_reason_and_filter(text, clean_name, code)
            if reason:
                found.append((clean_name, ticker, reason))
            
    return found

def scrape_episodes():
    # 1. 爬取股癌筆記首頁以取得最新集數連結
    index_url = "https://socialworkerdaily.com/index/invest/notes-of-gooaye/ep-600-to-700/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    
    taiwan_stocks = fetch_taiwan_stocks()
    
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
    for el in episode_elements:
        title = el.text.strip()
        url = el.get('href', '')
        # 篩選真實單集，過濾掉總分類導覽目錄（如 ep-600-to-700）
        if 'notes-of-gooaye-ep-' in url or re.search(r'(?:EP|ep)?\s*\d+', title):
            if 'ep-' in url and '-to-' in url:
                continue
            episodes_to_scrape.append((title, url))
            
    # 只取前 10 個真正的最新單集，確保資料正確且覆蓋完整
    episodes_to_scrape = episodes_to_scrape[:10]
        
    results = []
    price_cache = {}
    
    for title, original_url in episodes_to_scrape:
        match = re.search(r'(?:EP|ep)?\s*(\d+)', title)
        ep_num = match.group(1) if match else None
        
        print(f"\n========== Processing Episode: {title} (EP {ep_num}) ==========")
        
        candidate_urls = [original_url]
        
        # 2. 如果有集數數字，搜尋網友討論與論壇
        if ep_num:
            print(f"Searching web for EP {ep_num} notes/PTT/hints...")
            search_links = search_netizen_links(ep_num)
            for link in search_links[:4]: # 取前 4 個相關連結，大幅擴大爬取範圍
                if link not in candidate_urls:
                    candidate_urls.append(link)
        
        # 3. 爬取候選網頁並記錄提及的股票及其具體出處
        stock_mentions_map = {}
        successful_sources = []
        
        print(f"Sources to crawl: {candidate_urls}")
        
        for url in candidate_urls:
            time.sleep(0.3) # 禮貌間隔
            print(f"Crawling source: {url}")
            try:
                res = requests.get(url, headers=headers, timeout=5)
                res.encoding = 'utf-8'
                if res.status_code != 200:
                    continue
                    
                ep_soup = BeautifulSoup(res.text, 'html.parser')
                
                # HTML 清理演算法：排除 header、footer、nav、aside 等 boilerplate 區塊，規避側欄熱門股票標籤干擾
                for el in ep_soup(['script', 'style', 'header', 'footer', 'nav', 'aside']):
                    el.decompose()
                    
                for el in list(ep_soup.find_all(True)):
                    # 避免在迭代過程中調用已 decomposed 的子節點屬性
                    if el.parent is None and el.name != 'html':
                        continue
                    classes = el.get('class', [])
                    el_class = ' '.join(classes) if isinstance(classes, list) else str(classes)
                    el_id = str(el.get('id', ''))
                    
                    el_class = el_class.lower()
                    el_id = el_id.lower()
                    
                    if any(k in el_class or k in el_id for k in [
                        'footer', 'header', 'nav', 'sidebar', 'aside', 'widget', 'menu', 
                        'comments', 'share', 'related', 'popular', 'recommend', 'banner'
                    ]):
                        el.decompose()

                # 優先抓取主要文章區塊
                main_el = ep_soup.find('article') or ep_soup.find('main') or ep_soup.find('div', class_='article-content') or ep_soup.find('div', class_='entry-content')
                page_text = main_el.get_text() if main_el else ep_soup.get_text()
                
                # 識別本頁出現的股票
                stocks_found = extract_stocks_from_content(page_text, taiwan_stocks)
                
                if stocks_found or url == original_url: # 即使原部落格沒配到股票，也將其列為成功來源
                    successful_sources.append(url)
                    
                source_name = get_source_name(url)
                
                for name, ticker, reason in stocks_found:
                    # 統一以 ticker 為 key 進行去重與歸納
                    if ticker not in stock_mentions_map:
                        stock_mentions_map[ticker] = {
                            "name": name,
                            "mentions": []
                        }
                    # 偏好使用更長的名字
                    if len(name) > len(stock_mentions_map[ticker]["name"]):
                        stock_mentions_map[ticker]["name"] = name
                        
                    # 記錄出處與理由
                    if not any(m["url"] == url for m in stock_mentions_map[ticker]["mentions"]):
                        stock_mentions_map[ticker]["mentions"].append({
                            "name": source_name,
                            "url": url,
                            "reason": reason
                        })
            except Exception as e:
                print(f"Error parsing source {url}: {e}")
                
        # 4. 對本集所有股票獲取即時價格
        final_stocks = []
        for ticker, s_info in stock_mentions_map.items():
            if ticker not in price_cache:
                info = get_stock_info(ticker)
                if info:
                    price_cache[ticker] = info
            
            if ticker in price_cache:
                final_stocks.append({
                    "name": s_info["name"],
                    "ticker": ticker,
                    "current_price": price_cache[ticker]["current_price"],
                    "change": price_cache[ticker]["change"],
                    "mentions": s_info["mentions"] # 傳遞給前端顯示出處
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
            "sources": successful_sources # 所有參與分析之有效來源
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
    
    os.makedirs('docs', exist_ok=True)
    with open('docs/portfolio_pnl.json', 'w', encoding='utf-8') as f:
        json.dump(portfolio_pnl, f, ensure_ascii=False, indent=4)
        
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
