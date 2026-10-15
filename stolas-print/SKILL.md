---
name: "stolas-print"
description: Stolas 系列的 PDF 產出技能，把 stolas-thread 的教材檔整理成含一頁重點與圖片的 PDF 學習筆記，或把 stolas-web 的主檔整理成「心智圖封面加名詞速查」的 PDF。使用者訊息以 /stolas-print 或全形 ／stolas-print 開頭時使用 (大小寫不拘)，後面可接教材檔名或主題，例如「/stolas-print」「/stolas-print 外匯交易」。stolas-thread 結案時也會直接載入本技能。在已使用過 stolas-web 的對話中，使用者說「產出 PDF」「輸出 PDF」也使用本技能。stolas-thread 單元仍在學習中 (教材學習狀態不是「已完成」) 時，本技能不產出，請使用者先在 stolas-thread 說「結案」。沒有 Stolas 教材或主檔、只是一般地要求產生或轉換 PDF 時不觸發；訊息以 /stolas-thread、/stolas-web、/stolas-exam 開頭時屬於其他技能。
---

# Stolas Print：PDF 產出

## 這個技能在做什麼

stolas-thread 與 stolas-web 的檔案是 Markdown 工作底稿，本技能把它們整理成之後回顧用的 PDF。內容一律取自檔案本身，不依賴對話紀錄，所以可以在任何對話中重產；也因此不補寫檔案中沒有的內容。

| 來源 | 產出 | 做法 |
|---|---|---|
| stolas-thread 教材 | 一頁重點 + 含圖的印刷版學習筆記 | `references/thread-print.md` |
| stolas-web 主檔 | 心智圖封面 + 每個詞一句話 + 資料來源 | `references/web-print.md` |

## 步驟 1：找到要產出的檔案

依序判斷，找到就停：

1. 使用者在訊息中指定了檔名、附上檔案，或指定了主題名稱：用那一份。
2. 由 stolas-thread 結案直接載入：用該單元的教材。
3. 本對話中 stolas-thread 或 stolas-web 建立或更新過的檔案：用最近更新的那一份。本對話同時有兩份以上時，請使用者選。
4. 使用者連接的資料夾或工作目錄中，檔名以 `stolas-thread-`、`stolas-web-` 開頭 (舊版為 `stolas-`、`stolas-lite-`) 的 Markdown 檔：列出最近更新的 3 到 5 份，請使用者選。
5. 都找不到：請使用者附上教材或主檔。

**判斷來源**：讀 frontmatter 的 `type`。

- `stolas-thread`，或沒有 `type` 但 `tags` 含 `stolas` 的舊版教材：thread 模式。
- `stolas-web`，或舊版的 `stolas-lite`：web 模式。frontmatter 損壞 (例如被編輯器改成 `***` 開頭) 時，看標題是否為「<主題>：名詞速查」並有「目錄樹」章節，符合就當作 web 主檔。
- 兩者都不是：說明本技能只處理 Stolas 系列的檔案。

## 步驟 2：確認可以產出

**thread 模式**：讀教材標頭下方的版本行。

- 學習狀態為「已完成」：繼續。
- 學習狀態不是「已完成」(例如「講解中」)：**不產出**。用一句話說明單元還在學習中，請使用者回到 stolas-thread 說「結案」，結案時會寫入一頁重點並自動接著產出 PDF。使用者堅持要先看一份草稿時，同樣請他先結案；結案後仍可以繼續追問，教材更新後再重產。
- 教材缺「一頁重點」章節 (例如舊版教材在結案前就中斷)：說明缺少的章節，請使用者回到 stolas-thread 結案補上。

**web 模式**：主檔隨時都可以產出，不需要結案。已建立條目的關鍵字為 0 時，說明主檔還沒有內容可以產出。

## 步驟 3：產出

依模式讀 `references/thread-print.md` 或 `references/web-print.md`，照其中的步驟執行。

**輸出位置**：與來源檔案同一個資料夾。來源在使用者連接的本機資料夾時，透過裝置橋接寫回該資料夾 (能在該電腦上執行指令時直接在原處產出；只能搬運檔案時，先在工作區產出再寫回)。

**檔名**：`stolas-thread-<slug>-<YYYY-MM-DD>.pdf` 或 `stolas-web-<slug>-<YYYY-MM-DD>.pdf`，slug 取來源檔名，日期取產出當天。同一天重產時覆蓋同名檔案。

## 步驟 4：檢查與交付

1. 把 PDF 的第 1 頁與任一張含圖或含表的頁面轉成預覽圖看一眼，確認中文字型、圖片、表格正常，沒有被切斷的條目。
2. 呈現或傳送 PDF。寫在使用者本機資料夾時，告知檔案位置即可。
3. 用一兩句話說明這份 PDF 收了什麼 (例如「封面收心智圖與『止損、強制平倉、爆倉』比較表，共 3 頁」)，有降級處理時一併說明。

## 語言與格式

- 使用繁體中文。中文使用全形逗號與句號，括號一律半形，括號與前後中文各留一個空格。
- 不使用 emoji。
- 直接陳述 (避開「不是……而是……」句式)，段落以陳述句收尾。

## 備援規則

- **工具缺失**：腳本會自動降級 (細節見各模式的參考檔)；仍然失敗時，交付 HTML 版本，並告知使用者可用瀏覽器的「列印 → 另存為 PDF」自行轉檔。
- **工具呼叫失敗**：改用下一個替代方案，避免反覆重試同一個失敗的呼叫。

## 參考檔案

- `references/thread-print.md`：thread 教材的產出步驟、一頁重點的圖片判斷、印刷版結構。thread 模式讀取。
- `references/visual-toolkit.md`：依繪圖規格重繪 SVG 的規範。thread 模式重繪圖片前讀取。
- `references/web-print.md`：web 主檔的版面規則與執行方式。web 模式讀取。
- `assets/onepage-a4.html`：thread 一頁重點模板 (直式 A4)，填寫規則寫在檔內註解。
- `assets/palette.json`：學科分類對應的配色，兩支腳本共用，不需要手動編輯。
- `assets/web-print.css`：web PDF 的樣式，由 `build_web_pdf.py` 讀取。
- `scripts/build_pdf.py`：thread 印刷版 Markdown 轉 PDF，可加 `--onepage` 把一頁重點放在第一頁。
- `scripts/build_web_pdf.py`：web 主檔直接轉 PDF，版面與挑選規則都在腳本內。
