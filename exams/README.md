# 歷屆試題資料（exams/）

考選部「考畢試題查詢平臺」<https://wwwq.moex.gov.tw/exam/wFrmExamQandASearch.aspx> 公布的
**消防設備師／消防設備士**試題、答案、更正答案，轉成網頁 `25-歷屆試題.html`、`26-考試策略分析.html` 使用的資料。
依著作權法第 9 條，依法令舉行之考試試題不受著作權保護。

| 路徑 | 內容 |
|---|---|
| `meta/exam_codes.json` | 82～115 年名稱含「消防」「警察人員」的考試場次代碼 |
| `meta/catalog.json` | 各場次中「消防」類科的試題／答案／更正答案下載連結 |
| `raw/` | 下載的 PDF（**不進版控**，`.gitignore`）與 `manifest.json` |
| `data/papers.json` | 解析結果：每份試卷的申論題、選擇題、官方答案、更正答案、備註 |
| `data/exam.json` | 網頁用資料：再加上主題分類與「可能相關條文」（自動比對） |
| `data/parse_warnings.txt` | 解析警告（題號不連續、缺答案、選項不足四個）；目前 0 則 |

## 更新流程（每年新考試公布後）

需要 Python 3 與 PyMuPDF（`pip install pymupdf`）。在專案根目錄執行：

```bash
python exams/tools/list_exams.py 115 116          # 1. 補抓新年度場次代碼
python exams/tools/crawl_index.py                 # 2. 各場次的消防類科檔案清單
python exams/tools/download.py exams/raw 消防設備師 消防設備士   # 3. 下載 PDF（已下載的會跳過）
python exams/tools/parse_papers.py                # 4. PDF → papers.json（看警告數是否為 0）
python exams/tools/build_exam_data.py             # 5. papers.json → exam.json
```

爬蟲每次請求間隔 1 秒。考選部憑證缺 Subject Key Identifier，Python 3.13+ 預設的嚴格檢查會擋，
`moex.py` 只關掉 `VERIFY_X509_STRICT`，**仍驗證憑證**。

## 解析重點（parse_papers.py）

- 選項符號 (A)～(D)、㈠～㈩、⑴～⑸ 是私用區字元（E18C–E18F、E129–E132、E0C6–E0CA），已逐年核對 100～115 年一致。
- 題號和題幹在同一列，題幹又可能以數字開頭（「9」＋「119 火災通報…」），所以用「預期的下一個題號」切，不抓行首所有數字。
- 答案 PDF 是表格，用座標配對（答案在題號正下方）。100～102 年是「題號 01 02…／答案」兩列的舊格式，另外處理。
- 跨頁黏進題目的「代號：」「頁次：」會被清掉。表格與附圖**沒有**轉成文字，網頁會提示看原卷 PDF。

## 主題分類與相關條文（build_exam_data.py）

- 主題：依關鍵字命中數歸到設備／法規／火災學主題，並連到站內圖解頁。約 6% 題目無法歸類。
- 相關條文：題目與設置標準各條（`tools/arts.json`）做字元雙連詞 TF-IDF 相似度，取前 3 條且分數 ≥ 0.22，火災學不比對。
  **這是延伸閱讀線索，不是官方解答依據。**
