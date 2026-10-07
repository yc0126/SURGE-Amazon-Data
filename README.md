# SURGE — Amazon 資料清洗與訓練交接

本專案提供 Amazon 各商品類別的資料轉換腳本與整理後的資料，供官方 [SIGIR21-SURGE](https://github.com/tsinghua-fib-lab/SIGIR21-SURGE) 的 Amazon 預處理流程使用。

**`reviews_*.json` 與 `meta_*.json` 是官方預處理的來源檔。** 官方程式還需產生訓練、驗證、測試序列與 ID 字典，模型才會讀取這些產物。

目前已更新的 `All_Beauty` 互動資料保留原始毫秒時間戳。其他類別須先重新執行新版轉換腳本，才能統一使用本文的毫秒設定。本專案目前提供資料與操作交接；不代表已完成官方環境的端到端訓練驗證。

## 1. 專案檔案

| 資料夾／檔案 | 內容與用途 | 給組員的交接建議 |
| :--- | :--- | :--- |
| `All_Beauty/reviews_All_Beauty.json` | **互動來源檔**：2,627 筆互動、262 位使用者、368 件商品。已完成重複紀錄移除與反覆 5-core 過濾，保留原始毫秒時間戳。 | **必下載**，交給官方 Amazon 預處理流程。 |
| `All_Beauty/meta_All_Beauty.json` | **商品類別對照檔**：368 件商品。各商品的 `categories` 皆設為 `[["All_Beauty"]]`，供官方 `_meta_preprocessing` 讀取。 | **必下載**，與 `reviews` 放在同一資料夾。這是自動生成的類別標記，並非 Amazon 原始商品中繼資料。 |
| `All_Beauty/amazon_beauty_surge.txt` | **數字序列備用檔**：由 `clean_amazon.py` 產生，以空白分隔使用者與商品序列。 | 官方 SURGE 的本文流程不使用此檔。改用 PyTorch 或 RecBole 時，仍須依目標框架的資料規格轉換。 |
| `convert_for_surge.py` | **來源格式轉換腳本**：讀取原始 `.jsonl`，去重、執行 5-core 過濾，產出官方預處理所需的兩個 JSON Lines 檔案。新版保留毫秒。 | 用法：`python3 convert_for_surge.py <類別名稱>`。 |
| `clean_amazon.py` | **數字序列整理腳本**：進行數字 ID 映射、時間排序與序列聚合。 | 供檢查序列與展示前處理邏輯；不取代官方 SURGE 預處理。 |
| `Amazon_Fashion/`、`Sports_and_Outdoors/` | 其他類別的整理結果。 | 使用毫秒設定前，先以新版 `convert_for_surge.py` 重新產生來源檔；各類別分開處理與訓練。 |

原始 `*.jsonl` 留存本機，不納入 GitHub。檔案大小會隨重新產生結果改變，因此此表不固定標示大小。

## 2. 來源欄位與清洗規則

### 互動檔：`reviews_All_Beauty.json`

雖然副檔名是 `.json`，實際格式是 **JSON Lines**：每行一筆 JSON 物件，沒有包在外層陣列中。

```json
{"reviewerID": "AE23ZBUF2YVBQPH2NN6F5XSA3QYQ", "asin": "B089R7S73D", "unixReviewTime": 1598559204579}
```

| 輸出欄位 | Amazon Reviews 2023 來源 | 意義 |
| :--- | :--- | :--- |
| `reviewerID` | `user_id` | 使用者 ID。 |
| `asin` | 優先採用 `parent_asin`，缺少時採用 `asin` | 本專案使用的商品 ID；優先將變體歸到父商品。 |
| `unixReviewTime` | `timestamp` | 原始評論時間戳，單位為**毫秒**。欄位名稱沿用官方讀取介面。 |

新版轉換腳本的處理方式：

1. 讀取 `<類別名稱>.jsonl` 中可用的使用者、商品與時間欄位。
2. 以「使用者、商品、原始毫秒時間戳」三者組合作為去重依據。
3. 反覆移除互動少於 5 筆的使用者或商品，直到剩餘資料符合 5-core。
4. 按使用者及時間戳排序，輸出互動檔與商品類別檔。

**5-core 的計數單位是互動筆數**，不保證每位使用者都有 5 件不同商品。同一使用者對同一商品在不同時間的紀錄可以保留；同時間紀錄不人為加秒或加毫秒。

這個版本將保留的評論紀錄視為正向互動，未以 `rating` 篩選，也未以 `verified_purchase` 篩選。評論時間不等於實際購買時間，評分、評論文字與圖片也未輸入此流程。

### 商品類別檔：`meta_All_Beauty.json`

同樣是每行一筆 JSON：

```json
{"asin": "B089R7S73D", "categories": [["All_Beauty"]]}
```

官方預處理使用 `asin` 對應商品，並讀取 `categories[0][-1]` 作為類別。此處所有商品使用同一類別，能提供所需欄位，但**不能提供商品間的細分類差異**。

## 3. 重新轉換資料

在本專案根目錄執行，並先將原始檔 `All_Beauty.jsonl` 放在腳本可讀取的位置：

```bash
python3 convert_for_surge.py All_Beauty
```

產物為：

```text
All_Beauty/reviews_All_Beauty.json
All_Beauty/meta_All_Beauty.json
```

其他類別依相同方式重新產生，例如原始檔為 `Amazon_Fashion.jsonl` 時：

```bash
python3 convert_for_surge.py Amazon_Fashion
```

不要將舊的秒時間戳資料與新版毫秒資料混用同一訓練設定。

## 4. 官方 SURGE 執行步驟

以下以 `All_Beauty` 為例。先依[官方 README](https://github.com/tsinghua-fib-lab/SIGIR21-SURGE#readme) 建立相容環境並安裝依賴；單純下載資料並不足以執行訓練。官方專案使用 TensorFlow 1.x，請依其環境要求安裝。

### Step 1：放置來源檔，使用新的預處理目錄

在官方 `SIGIR21-SURGE` 專案根目錄建立目錄：

```bash
mkdir -p tests/resources/deeprec/sequential/amazon_beauty_ms/amazon
```

下載本專案的兩個 `All_Beauty` JSON 檔，放入上述目錄：

```text
tests/resources/deeprec/sequential/amazon_beauty_ms/amazon/reviews_All_Beauty.json
tests/resources/deeprec/sequential/amazon_beauty_ms/amazon/meta_All_Beauty.json
```

官方程式會將 `dataset` 名稱附加到 `--data_path` 後方。因此下方指令的 `--data_path` 指向 `amazon_beauty_ms`，來源檔則位於它的 `amazon` 子目錄。

使用新目錄是為了避免沿用舊的秒單位產物。官方腳本在 `train_data` 已存在時會略過預處理；若之後再次修改來源資料，也應改用另一個新的資料目錄。

### Step 2：修改 `examples/00_quick_start/sequential.py`

使用程式片段搜尋定位，避免因版本不同而依賴固定行號。

**（1）在 Amazon 資料集分支修改來源檔名：**

```python
if flags_obj.dataset == 'amazon':
    reviews_name = 'reviews_All_Beauty.json'
    meta_name = 'meta_All_Beauty.json'
```

保留這個分支後方其他資料集的設定。

**（2）在測試序列分組區塊補上預設切分長度：**

```python
if not os.path.exists(test_file + '_group1'):
    if flags_obj.dataset == 'kuaishou':
        split_length = [50, 100, 150, 200]
    elif flags_obj.dataset == 'taobao_global':
        split_length = [10, 20, 30, 40]
    else:
        split_length = [10, 20, 30, 40]
    group_sequence(test_file=test_file, split_length=split_length)
```

這個補充分支讓 Amazon 也能取得 `split_length`，避免該變數尚未定義。

**（3）在 SURGE 的 `prepare_hparams(...)` 呼叫加入毫秒設定：**

找到 `elif flags_obj.model == 'SURGE':`，在這個分支的 `prepare_hparams(...)` 參數中加入：

```python
time_unit="ms",
```

例如原本的參數附近可改成以下片段；保留其餘參數與完整函式呼叫：

```python
max_seq_length=max_seq_length,
time_unit="ms",
hidden_size=40,
```

必須加在 **SURGE 分支的參數呼叫內**。僅修改其他分支，或僅在函式前面宣告 `time_unit`，不保證該值會傳入 SURGE。

### Step 3：啟動預處理與訓練

從官方專案根目錄執行：

```bash
cd examples/00_quick_start
python sequential.py \
  --dataset=amazon \
  --model=SURGE \
  --name=amazon-beauty-ms-SURGE \
  --data_path=../../tests/resources/deeprec/sequential/amazon_beauty_ms \
  --gpu_id=0 \
  --batch_size=128 \
  --sample_rate=1.0 \
  --val_num_ngs=4 \
  --test_num_ngs=99
```

`--sample_rate=1.0` 保留進入官方流程的全部商品。驗證集每筆正例抽取 4 個負例，測試集抽取 99 個負例；這是抽樣候選評估，不能直接當作全商品排序的結果。

**小類別的負例數須調低。** 官方抽樣需要足夠的不同商品。已整理的 `Amazon_Fashion` 僅有 7 件商品，不能使用 99 個不同負例；流程測試可改為 `--val_num_ngs=4 --test_num_ngs=5`，並同步更換來源檔名、資料目錄與實驗名稱。這類小資料集的結果不宜作為主要成效證據。

## 5. 官方預處理產物與模型讀取格式

官方 Amazon 流程會整理時間序列、切分資料、產生歷史序列、建立 ID 字典，並加入驗證／測試負例。切分方式為每位使用者最後一筆作測試、倒數第二筆作驗證，其餘供訓練使用；實際序列產生仍依官方程式的歷史條件執行。

| 產物 | 用途 |
| :--- | :--- |
| `train_data` | 訓練序列。 |
| `valid_data` | 驗證序列與抽樣負例。 |
| `test_data` | 測試序列與抽樣負例。 |
| `user_vocab.pkl` | 使用者 ID 字典。 |
| `item_vocab.pkl` | 商品 ID 字典。 |
| `category_vocab.pkl` | 商品類別 ID 字典。 |
| `test_data_group1` 等 | 按歷史長度分組的測試資料。 |

`train_data`、`valid_data`、`test_data` 每行有 **8 個 Tab 分隔欄位**，沒有標題列：

| 順序 | 欄位內容 |
| :--- | :--- |
| 1 | 標籤：正例為 `1`，負例為 `0`。 |
| 2 | 使用者 ID。 |
| 3 | 目標商品 ID。 |
| 4 | 目標商品類別。 |
| 5 | 目標互動時間戳。 |
| 6 | 歷史商品序列，以逗號分隔。 |
| 7 | 歷史類別序列，以逗號分隔。 |
| 8 | 歷史時間戳序列，以逗號分隔。 |

文字序列中的 ID 再由模型 iterator 透過字典映射。此流程不需要自行準備商品相似度 CSV 或圖的連線表；SURGE 會根據輸入歷史序列及模型內部機制建立興趣圖。

## 6. 交接前檢查

- 兩個 JSON 檔均為每行一筆物件，且商品 ID 能在 `meta` 中找到對照。
- 來源時間戳單位與 SURGE 的 `time_unit` 一致；本文流程使用毫秒。
- 使用新的預處理目錄，確保沒有沿用舊 `train_data` 與字典。
- 不同類別分開產生資料與實驗結果，並依商品數設定負例數。
- 記錄資料規模、切分方式、負例數與評估指標，以便解讀與重現結果。

## 7. 參考來源

- [官方 SIGIR21-SURGE 專案與環境說明](https://github.com/tsinghua-fib-lab/SIGIR21-SURGE)
- [官方訓練入口 sequential.py](https://github.com/tsinghua-fib-lab/SIGIR21-SURGE/blob/main/examples/00_quick_start/sequential.py)
- [官方預處理 sequential_reviews.py](https://github.com/tsinghua-fib-lab/SIGIR21-SURGE/blob/main/reco_utils/dataset/sequential_reviews.py)
- [本專案 SURGE-Amazon-Data](https://github.com/yc0126/SURGE-Amazon-Data)
