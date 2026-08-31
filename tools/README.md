# tools — 產生器

`23-條號索引.html` 與 `search-index.json` **不是手寫的**，由這裡的三支腳本產生。
改過任何一份圖解或題庫之後，要重跑才會同步。三支都不需要安裝套件，Python 3 直接執行即可。

```bash
python tools/gen_index.py    # 1. 產生 tools/index_data.json（條文 × 段落 × 題數）
python tools/gen_page.py     # 2. 用 index_data.json + index_tpl.html 產生 23-條號索引.html
python tools/gen_search.py   # 3. 掃過所有圖解頁，產生 search-index.json（內文搜尋用）
```

順序不能顛倒——`gen_page.py` 吃 `gen_index.py` 的輸出。

## 各檔用途

| 檔案 | 用途 |
|---|---|
| `arts.json` | 全法 266 條的條號、所屬編章節與條文全文，由全國法規資料庫 pcode D0120029 解析而來。**法規修正時要重新擷取這一份。** |
| `gen_index.py` | 把 `arts.json` 的每一條對應到「一句話主旨（人工撰寫的 `OV` 表）＋ 圖解頁段落（`RULES`）＋ 題庫題數（掃 `05-互動題庫.html`）」 |
| `gen_page.py` | 把上一步的結果填進 `index_tpl.html`，輸出 `23-條號索引.html` |
| `gen_search.py` | 依 `<h2 id>` 把每份圖解切段、抽純文字，輸出 `search-index.json`（約 190,000 字／423 KB，網頁端在第一次輸入關鍵字時才抓） |
| `index_tpl.html` | 條號索引的版型與搜尋邏輯；**改版面要改這裡，不要直接改 `23-條號索引.html`**（會被覆蓋） |

## 三個對應關係要保持同步

1. **段落 id**：`gen_index.py` 的 `RULES` 與題庫 `05-互動題庫.html` 的 `DGRULES` 是同一套規則的兩份實作。
   新增圖解段落或調整條號分段時，兩邊都要改。
2. **段落標題**：`gen_page.py` 與 `gen_search.py` 都直接讀題庫的 `DOCS` 常數取得檔名與段落標題，
   所以**題庫的 `DOCS` 是單一事實來源**，改章節編號時只要改那裡。
3. **`FILES`**：在 `gen_index.py`。章節代碼 → 圖解檔名。潔淨區（`M`）沒有任何設置標準條文對應，
   列在裡面只是為了讓內文搜尋能把潔淨區段落列進「另有 N 個圖解段落提到…」。

## 法規修正時

1. 重新從全國法規資料庫擷取條文，更新 `arts.json`
2. 檢查 `gen_index.py` 的 `OV`（主旨）有沒有需要跟著改的條文
3. 依序重跑三支腳本
4. 人工核對受影響的圖解頁與題庫題目
