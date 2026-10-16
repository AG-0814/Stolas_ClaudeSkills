# Stolas Print：PDF 產出 skill

Stolas Print 把 Stolas 系列的 Markdown 檔整理成之後回顧用的 PDF。內容一律取自檔案本身，不依賴對話紀錄，所以可以在任何對話中重產。

| 來源 | 產出 |
|---|---|
| stolas-thread 教材 (已結案) | 第一頁為一頁重點，之後為含圖的印刷版學習筆記，學習紀錄壓縮到附錄 |
| stolas-web 主檔 | 第一頁封面放心智圖與一張比較表，之後是每個詞一句話與資料來源 |

## 使用方式

- stolas-thread 單元說「結案」後會自動接著產出。學習中途輸入 `/stolas-print` 不會產出，會先請你結案。
- stolas-web 隨時可以輸入 `/stolas-print`，或在工作階段中說「產出 PDF」，產出主檔當下的快照。
- 也可以在新對話中輸入 `/stolas-print <主題>` 或附上檔案重產。

## web 封面的比較表 (`--table`)

web 主檔通常有好幾張比較表，封面只放一張。Claude 會先讀完所有比較表，依 `references/web-print.md` 的規則挑出最能替封面輔助說明的那張 (比較整張網核心詞、能化解混淆的表優先)，再把表的標題傳給腳本：

```
python scripts/build_web_pdf.py <主檔.md> <輸出.pdf> --table "<比較表標題>"
```

- 標題就是主檔中「**比較表：」後面那段文字，照原樣傳入，空白差異不影響比對。
- 標題對不上任何一張表時，腳本會列出主檔裡所有比較表的標題，並以代碼 4 結束，改用列出的標題重跑即可。
- 主檔沒有比較表時省略這個參數。沒有傳 `--table` 時，腳本退回機械挑法：表頭與第一欄中恰好是關鍵字主名稱的格數最多者，平手取列數多的。

平常不需要自己下這個參數，說「產出 PDF」時 Claude 會自動判斷。想指定封面放哪張表，直接告訴 Claude 表的名稱就好。

## 檔案結構

```
stolas-print/
├── SKILL.md                     流程：找檔案、確認可產出、產出、檢查
├── README.md                    本說明
├── LICENSE                      授權條款
├── assets/
│   ├── onepage-a4.html          thread 一頁重點模板 (直式 A4)
│   ├── palette.json             學科分類配色 (兩支腳本共用)
│   └── web-print.css            web PDF 樣式
├── references/
│   ├── thread-print.md          thread 產出步驟、一頁重點的圖片、印刷版結構
│   ├── visual-toolkit.md        依繪圖規格重繪 SVG
│   └── web-print.md             web 版面規則與降級
└── scripts/
    ├── build_pdf.py             thread 印刷版 Markdown 轉 PDF (含一頁重點)
    └── build_web_pdf.py         web 主檔直接轉 PDF
```

## 環境需求

- 需要開啟程式執行 (Code Execution) 功能。
- 會使用 pandoc、Playwright (Chromium)、mermaid-cli 與 pypdf；缺少其中幾項時，腳本會自動降級 (例如沒有 mermaid-cli 時，web 封面改放文字版目錄樹)，全部失敗時交付 HTML。

## 授權

本專案以 MIT License 釋出，詳見 [LICENSE](LICENSE)。
