import json
import argparse
import pandas as pd
import time

def parse_args():
    parser = argparse.ArgumentParser(description="將 Amazon 2023 資料集清洗並轉換為 SURGE 模型格式")
    parser.add_argument('-i', '--input', type=str, required=True, help="輸入的原始 .jsonl 檔案路徑")
    parser.add_argument('-o', '--output', type=str, required=True, help="輸出的 .txt 檔案路徑")
    parser.add_argument('-k', '--k_core', type=int, default=5, help="K-core 過濾閾值 (預設: 5)")
    return parser.parse_args()

def load_jsonl_fast(file_path):
    print(f"📂 正在逐行高速讀取 {file_path} ...")
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            record = json.loads(line)
            # 只保留核心三欄位，極大化節省記憶體
            if 'user_id' in record and 'parent_asin' in record and 'timestamp' in record:
                data.append((record['user_id'], record['parent_asin'], record['timestamp']))
    return pd.DataFrame(data, columns=['user_id', 'parent_asin', 'timestamp'])

def filter_k_core(df, k):
    print(f"🧹 初始互動資料量: {len(df)} 筆，開始執行 {k}-core 過濾...")
    round_num = 1
    while True:
        start_len = len(df)
        
        # 過濾商品與使用者
        item_counts = df['parent_asin'].value_counts()
        df = df[df['parent_asin'].isin(item_counts[item_counts >= k].index)]
        
        user_counts = df['user_id'].value_counts()
        df = df[df['user_id'].isin(user_counts[user_counts >= k].index)]
        
        print(f"   -> 第 {round_num} 輪過濾後剩餘: {len(df)} 筆")
        round_num += 1
        if len(df) == start_len:
            break
    print(f"✨ {k}-core 過濾完成！最終有效互動: {len(df)} 筆")
    return df

def main():
    start_time = time.time()
    args = parse_args()
    
    # 1. 讀取資料
    df = load_jsonl_fast(args.input)
    
    # 2. K-core 過濾
    df_clean = filter_k_core(df, args.k_core).copy()
    if len(df_clean) == 0:
        print("❌ 過濾後無剩餘資料，請嘗試調降 -k 參數！")
        return

    # 3. ID 重新映射 (從 1 開始編號，保留 0 作為 Padding)
    print("🔄 正在將字串 ID 轉換為連續整數，並依時間戳記排序...")
    user_mapping = {id_str: i + 1 for i, id_str in enumerate(df_clean['user_id'].unique())}
    item_mapping = {id_str: i + 1 for i, id_str in enumerate(df_clean['parent_asin'].unique())}
    
    df_clean['uid'] = df_clean['user_id'].map(user_mapping)
    df_clean['iid'] = df_clean['parent_asin'].map(item_mapping)
    
    # 4. 依時間排序並聚合為序列 {x_1, x_2, ..., x_n}
    df_clean = df_clean.sort_values(by=['uid', 'timestamp'])
    user_seqs = df_clean.groupby('uid')['iid'].apply(list).reset_index()
    
    # 5. 匯出為 SURGE 空白分隔格式
    print(f"💾 正在寫入目標檔案: {args.output} ...")
    with open(args.output, 'w', encoding='utf-8') as f:
        for _, row in user_seqs.iterrows():
            seq_str = ' '.join(map(str, row['iid']))
            f.write(f"{row['uid']} {seq_str}\n")
            
    elapsed = time.time() - start_time
    print("==========================================")
    print(f"✅ 處理完成！總耗時: {elapsed:.2f} 秒")
    print(f"👤 總有效使用者數 (Users): {len(user_mapping)}")
    print(f"📦 總有效商品數 (Items): {len(item_mapping)}")
    print("==========================================")

if __name__ == '__main__':
    main()
