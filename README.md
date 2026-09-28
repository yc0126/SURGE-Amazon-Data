# 📦 SURGE 模型 — Amazon 多類別資料清洗與訓練交接

本專案存放已清洗完成的 Amazon 各類別資料集與自動化轉換腳本。每個商品類別皆整理於獨立的資料夾中（例如 `All_Beauty/`），請點選上方對應的類別資料夾下載檔案。

## 1. 專案目錄與檔案說明

| 資料夾 / 檔案路徑 | 檔案大小 | 檔案內容與用途說明 | 給組員的交接建議 |
| :--- | :--- | :--- | :--- |
| **`All_Beauty/reviews_All_Beauty.json`** | 254K | **【核心訓練檔】** 清洗後的 Amazon 美妝互動紀錄（共 2,627 筆、262 人）。已完成 5-core 過濾、去重、毫秒轉秒（`unixReviewTime`），並對齊官方欄位格式。 | **★ 必下載**<br>放進官方專案的 `tests/resources/deeprec/sequential/amazon/` |
| **`All_Beauty/meta_All_Beauty.json`** | 20K | **【核心對照檔】** 自動生成的商品類別對照表（共 368 件商品），用來滿足官方 `_meta_preprocessing` 強制讀取 `asin` 與 `categories` 的規定。 | **★ 必下載**<br>與上方 `reviews` 檔放在同一個 `amazon/` 資料夾內 |
| **`All_Beauty/amazon_beauty_surge.txt`** | 13K | **【純數字序列檔】** 由 `clean_amazon.py` 產出的空白分隔序列檔（如 `1 7 6 5 4`）。 | **備用檔**<br>官方 TF 1.x 版用不到；若改用 PyTorch / RecBole 可直接餵入 |
| **`convert_for_surge.py`** | 2.1K | **【全自動分類轉換腳本】** 讀取原始 `.jsonl` 並執行去重與 5-core 過濾，自動建立類別資料夾並產出 `reviews_*.json` 與 `meta_*.json`。 | **供團隊重用**<br>用法：`python3 convert_for_surge.py <類別名稱>` |
| **`clean_amazon.py`** | 3.5K | **【通用序列清洗腳本】** 將字串 ID 轉為純數字（1-based index）並依時間排序聚合，產出 `.txt` 檔。 | **報告素材**<br>展示資料前處理與 ID 映射邏輯 |

*(註：各類別原始未清洗大數據 `*.jsonl` 因單檔高達數百 MB 且訓練用不到，僅留存本機不上傳。)*

---

## 2. 🚀 模型執行步驟（給負責訓練的組員）

### Step 1: 放置資料檔
請點選上方欲測試的類別資料夾（以 `All_Beauty` 為例），下載裡面的 **`reviews_All_Beauty.json`** 與 **`meta_All_Beauty.json`**，並直接放進 `SIGIR21-SURGE/tests/resources/deeprec/sequential/amazon/` 資料夾底下（**不需要**連同外層的 `All_Beauty` 資料夾一起放進去）。

### Step 2: 修改 `examples/00_quick_start/sequential.py` 兩處設定

**(1) 第 714～715 行（改為要跑的類別檔名）：**
```python
if flags_obj.dataset == 'amazon':
    reviews_name = 'reviews_All_Beauty.json'
    meta_name = 'meta_All_Beauty.json'
```

**(2) 第 760 行附近（補上 `else` 分支，修正官方漏寫 `amazon` 切分長度的 Bug）：**
```python
if not os.path.exists(test_file+'_group1'):
    if flags_obj.dataset == 'kuaishou':
        split_length = [50, 100, 150, 200]
    elif flags_obj.dataset == 'taobao_global':
        split_length = [10, 20, 30, 40]
    else:
        split_length = [10, 20, 30, 40]
    group_sequence(test_file=test_file, split_length=split_length)
```

### Step 3: 啟動訓練指令
```bash
cd examples/00_quick_start
python sequential.py --dataset=amazon --name=amazon-SURGE --gpu_id=0 --batch_size=128
```
