# Stolas：系統化教學 skill

Stolas 是一個 Claude skill，把一個專有名詞、縮寫或外文術語，或一篇國文課文、古典詩詞、文言文，展開成完整的學習單元。它先診斷學習者對該領域的基本認識，再用脈絡地圖同時安排「它怎麼運作」與「它從哪來、往哪去、跟誰是同一類」，概念淺的主題多往外拉脈絡，概念深的主題專注自身拆解。所有討論持續整併成一份教材，透過期中與最終驗收確認理解，結案時產出附一頁重點的 PDF 學習筆記，教材附 Obsidian 可讀取的學科標籤。

## 使用方式

訊息以 `/stolas` (或全形 `／stolas`) 開頭才會啟動，例如：

- `/stolas Semaglutide`
- `/stolas 杜甫〈登高〉`
- `/stolas 我感覺台灣飲料店小品牌很多，為什麼沒有寡占`
- `/stolas` 附上一張圖片，詢問「這是什麼」

單元開始後可以直接追問，或使用以下指令：

| 指令 | 作用 |
|---|---|
| 繼續教學 | 講解下一個節點 |
| 沒聽懂 | 換一種方式重講 (先畫圖，再拆步驟定位卡住的地方) |
| 生成全教材 | 把剩餘節點一次寫進教材後停下等待 |
| 驗收 | 進行期中或最終驗收 |
| 跳至結尾驗收 | 直接進行涵蓋全部節點的最終驗收 |

## 檔案結構

```
stolas/
├── SKILL.md                     主流程與教學規則
├── README.md                    本說明
├── LICENSE                      授權條款
├── assets/
│   ├── onepage-a4.html          直式 A4 一頁重點模板
│   └── palette.json             學科分類配色
├── references/
│   ├── intake.md                多義詞、婉拒、觀察查核、圖片辨識
│   ├── context-map.md           脈絡地圖：深淺判定、欄位、權重
│   ├── classical-text.md        經典文本單元
│   ├── doc-template.md          教材模板、學科分類與印刷版結構
│   ├── visual-toolkit.md        圖解的表徵選擇與繪圖規格
│   └── assessment.md            選擇題設計、驗收與評分
└── scripts/
    └── build_pdf.py             教材 Markdown 轉 PDF (含一頁重點)
```

## 環境需求

- 需要開啟程式執行 (Code Execution) 功能，教材檔與 PDF 才能產生。
- PDF 轉檔會使用 pandoc、Playwright (Chromium)、mermaid-cli 與 pypdf；缺少其中幾項時，腳本會自動降級處理。
- 有網路搜尋工具時，涉及數據、法規、時效資訊的內容會先查證再寫入。

## 致謝

Stolas 自第三版起的部分設計概念，參考自 Matt Pocock 的 [mattpocock/skills](https://github.com/mattpocock/skills) 倉庫 (MIT License)，主要是 `skills/productivity/` 中的 teach、wait-what、to-questionnaire 與 writing-for-agents。參考的範圍包括：以術語表作為已定義清單並統一用語、以作答證據判定掌握、誤解只收錄被更正過的錯誤、課程與參考資料分離、沒聽懂時換方式重講，以及撰寫 skill 時的正向描述、漸進揭露與單一規則來源等原則。

以上皆為概念參考，Stolas 的所有文字與程式均為重新撰寫，未複製原倉庫的內容。感謝原作者公開分享。

## 貢獻者

- [AG-0814](https://github.com/AG-0814)：作者
- [Claude](https://claude.com/claude-code) (Anthropic)：協作撰寫與維護

## 授權

本專案以 MIT License 釋出，詳見 [LICENSE](LICENSE)。
