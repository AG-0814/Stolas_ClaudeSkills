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
