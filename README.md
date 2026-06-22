# 股癌筆記追蹤器 & 模擬倉儀表板 (Gooaye Tracker & Mock Portfolio Dashboard)

本專案是一個無伺服器 (Serverless) 的個人投資儀表板與股癌筆記股票提及追蹤器。透過 GitHub Actions 每天自動執行爬蟲，比對股癌最新的 Podcast 筆記中提及的股票，並自動更新您的模擬倉 (Mock Portfolio) 損益表現。

## 功能特色
1. **股癌筆記股票追蹤**：每天自動爬取「社工日常」股癌筆記最新集數，標記出節目中討論的股票，並顯示其最新股價與單日漲跌幅。
2. **模擬倉自動損益計算**：讀取根目錄下的 `portfolio.json` 配置，自動拉取 Yahoo Finance 股價，計算並輸出**今日損益**與**累計回報**。
3. **高質感網頁儀表板**：提供精美的毛玻璃風 (Glassmorphism) 深色模式前端網頁，直觀顯示股票提及歷史與模擬倉市值分配比例。
4. **雲端硬碟 & Excel 同步**：自動生成 `portfolio_pnl.csv` 檔案，方便您直接同步至 Google 雲端硬碟，在手機或試算表中打開。
5. **瀏覽器本地模擬器**：網頁版提供臨時編輯沙盒，可直接在瀏覽器新增持股即時計算損益。

---

## 目錄結構
* `scraper.py`：核心爬蟲與損益計算 Python 腳本
* `portfolio.json`：您的模擬倉持股交易記錄檔案 (可手動修改)
* `requirements.txt`：Python 依賴套件清單
* `docs/`：網頁與資料庫發行資料夾 (用於託管網頁)
  * `index.html`：網頁儀表板前端
  * `style.css`：網頁樣式表
  * `data.json`：爬蟲生成的股癌提及股票數據
  * `portfolio_pnl.json`：模擬倉損益計算 JSON
  * `portfolio_pnl.csv`：損益試算表報告 (UTF-8 BOM 編碼，支援 Excel)

---

## 使用教學

### 1. 本機安裝與執行
如果您想在本機執行，請依照以下步驟設定：

```bash
# 建立虛擬環境
python3 -m venv .venv
source .venv/bin/activate

# 安裝依賴庫
pip install -r requirements.txt

# 執行爬蟲與損益計算
python scraper.py
```
執行完畢後，您可以直接用瀏覽器打開 `docs/index.html` 查看最新的網頁儀表板！

### 2. 設定您的模擬倉交易紀錄
編輯專案根目錄底下的 `portfolio.json`，依照以下格式填入您的買入歷史：

```json
[
  {
    "symbol": "2330.TW",
    "name": "台積電",
    "buy_price": 950.0,
    "shares": 1000,
    "buy_date": "2026-06-10"
  },
  {
    "symbol": "NVDA",
    "name": "輝達",
    "buy_price": 120.0,
    "shares": 100,
    "buy_date": "2026-06-15"
  }
]
```
> **注意**：
> * 台股代碼後面必須加上 `.TW`（例如台積電為 `2330.TW`、聯發科為 `2454.TW`）。
> * 美股代碼直接填寫（例如 `NVDA`、`AAPL`）。

### 3. 如何啟用線上網頁 (GitHub Pages 託管)
若您已將此專案推送到您的 GitHub 儲存庫，可以開啟免費的線上儀表板：
1. 進入您 GitHub 儲存庫的 **Settings** > **Pages**。
2. 在 **Build and deployment** 下方的 Source 選擇 `Deploy from a branch`。
3. 將 Branch 設為 `main`，資料夾設為 `/docs`。
4. 點擊 **Save**。約 1-2 分鐘後，您就可以在專案提供的網址上看到您的專屬儀表板！

---

## Google 雲端與試算表同步方案

如果您希望在 Google 雲端隨時隨地查看，我們提供以下兩種極佳方案：

### 方案 A：自動生成 CSV 檔案同步 (透過電腦版 Google Drive)
1. 在您的 Mac 上安裝 **Google 雲端硬碟電腦版** (Google Drive for Desktop)。
2. 將本專案目錄放置於您的 Google Drive 同步資料夾中（例如：`/Users/shin1992/Google Drive/我的雲端硬碟/projects/gooaye-tracker`）。
3. 當您在本機執行 `python scraper.py` 後，生成的 `docs/portfolio_pnl.csv` 會自動同步上雲。在手機上打開 Google Drive App 即可隨時檢視最新損益。

### 方案 B：純 Google Sheets 試算表（極力推薦，無需執行程式）
如果您不希望設定定時排程或執行 Python 腳本，我們建議您直接在 Google Sheets（試算表）中建立損益表。它具有 100% 的即時性且運作於雲端：

在儲存格中輸入以下公式：
* **獲取台股股價 (以台積電為例)**：
  ```excel
  =GOOGLEFINANCE("TPE:2330", "price")
  ```
* **獲取美股股價 (以輝達為例)**：
  ```excel
  =GOOGLEFINANCE("NASDAQ:NVDA", "price")
  ```
* **獲取昨日收盤價 (以計算今日損益)**：
  ```excel
  =GOOGLEFINANCE("TPE:2330", "closeyest")
  ```
* **累積損益公式**：
  ```excel
  =(現價 - 買入均價) * 股數
  ```

本專案的網頁版 **「雲端與試算表同步」** 分頁中，也提供了詳細的公式說明與複製功能。
