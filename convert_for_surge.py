import json
import os
import sys
from collections import defaultdict

# 檢查是否有輸入類別名稱
if len(sys.argv) < 2:
    print("❌ 請輸入要清洗的 Amazon 類別名稱！")
    print("👉 範例用法: python3 convert_for_surge.py Video_Games")
    sys.exit(1)

category = sys.argv[1].replace(".jsonl", "")
input_file = f"{category}.jsonl"

# 若原始檔放在該類別資料夾內也找得到
if not os.path.exists(input_file) and os.path.exists(f"{category}/{category}.jsonl"):
    input_file = f"{category}/{category}.jsonl"

if not os.path.exists(input_file):
    print(f"❌ 找不到原始檔案: {input_file}，請確認檔案是否放在『專題』資料夾中！")
    sys.exit(1)

# 自動建立該類別的專屬資料夾
os.makedirs(category, exist_ok=True)
out_reviews = f"{category}/reviews_{category}.json"
out_meta = f"{category}/meta_{category}.json"

print(f"1. 正在讀取 {input_file} 並進行初步去重...")
raw_records = []
seen = set()

with open(input_file, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            u = data.get('user_id')
            i = data.get('parent_asin') or data.get('asin')
            t = data.get('timestamp')
            if u and i and t:
                t_sec = int(t) // 1000  # 毫秒轉秒
                key = (u, i, t_sec)
                if key not in seen:
                    seen.add(key)
                    raw_records.append((u, i, t_sec))
        except Exception:
            continue

print(f"   初步有效紀錄共 {len(raw_records)} 筆，開始執行 5-core 過濾...")

# 5-core 迭代過濾 (確保每人、每商品至少有 5 筆互動)
while True:
    u_counts = defaultdict(int)
    i_counts = defaultdict(int)
    for u, i, t in raw_records:
        u_counts[u] += 1
        i_counts[i] += 1
    
    filtered = [
        (u, i, t) for u, i, t in raw_records
        if u_counts[u] >= 5 and i_counts[i] >= 5
    ]
    if len(filtered) == len(raw_records):
        break
    raw_records = filtered

# 針對同一使用者在同一秒買多個商品的微調（避免 SURGE 排序衝突）
raw_records.sort(key=lambda x: (x[0], x[2]))
final_records = []
last_u = None
last_t = -1
for u, i, t in raw_records:
    if u == last_u and t <= last_t:
        t = last_t + 1
    final_records.append((u, i, t))
    last_u = u
    last_t = t

unique_users = set(x[0] for x in final_records)
unique_items = sorted(list(set(x[1] for x in final_records)))

print(f"2. 過濾完成！剩餘 {len( unique_users )} 位使用者、{len(unique_items)} 件商品、共 {len(final_records)} 筆互動。")

# 輸出符合 SURGE eval() 格式的 reviews 檔
with open(out_reviews, 'w', encoding='utf-8') as f:
    for u, i, t in final_records:
        record = {"reviewerID": u, "asin": i, "unixReviewTime": t}
        f.write(json.dumps(record) + "\n")

# 輸出符合 SURGE _meta_preprocessing 格式的 meta 檔
with open(out_meta, 'w', encoding='utf-8') as f:
    for i in unique_items:
        meta_record = {"asin": i, "categories": [[category]]}
        f.write(json.dumps(meta_record) + "\n")

print(f"✅ 轉換成功！檔案已自動存入『{category}/』資料夾中：")
print(f"   - {out_reviews}")
print(f"   - {out_meta}")
