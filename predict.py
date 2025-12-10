import json
import pandas as pd
import os
import math
import time
from tqdm import tqdm
from src.api_client import VNPTClient
from src.router import QuestionRouter
from src.solver import Solver
from src.config import INPUT_PATH, OUTPUT_PATH

# --- CẤU HÌNH BATCH SIZE TỐI ƯU ---
# Small (32k context) chịu được batch lớn, Large (22k) batch vừa phải
BATCH_SIZE_SMALL = 24
BATCH_SIZE_LARGE = 13

def main():
    print("=== STARTING HYBRID BATCH PIPELINE ===")
    
    # ---------------------------------------------------------
    # 1. LOAD DATA (Logic của bạn)
    # ---------------------------------------------------------
    if not os.path.exists(INPUT_PATH):
        print(f"ERROR: Input not found at {INPUT_PATH}")
        return

    try:
        with open(INPUT_PATH, 'r', encoding='utf-8') as f:
            all_questions = json.load(f)
    except:
        df = pd.read_csv(INPUT_PATH)
        all_questions = []
        for _, row in df.iterrows():
            all_questions.append({
                "qid": str(row.get('id', row.get('qid'))),
                "question": row['question'],
                "choices": [row['option_1'], row['option_2'], row['option_3'], row['option_4']]
            })
    
    print(f"Total questions loaded: {len(all_questions)}")

    # ---------------------------------------------------------
    # 2. RESUME LOGIC (Thêm vào để fix lỗi biến processed_qids)
    # ---------------------------------------------------------
    results = []
    processed_qids = set()

    if os.path.exists(OUTPUT_PATH):
        try:
            df_done = pd.read_csv(OUTPUT_PATH)
            if 'qid' in df_done.columns and 'answer' in df_done.columns:
                valid_results = df_done[df_done['answer'] != 'A']
                
                results = valid_results.to_dict('records')
                processed_qids = set(str(r['qid']) for r in results)
                
                print(f"-> Found checkpoint. Resuming... (Skipping {len(df_done) - len(results)} failed 'A' answers)")
        except Exception as e:
            print(f"-> Warning: Could not read checkpoint ({e}). Starting fresh.")

    # ---------------------------------------------------------
    # 3. ROUTING & BUCKETING (Logic của bạn + Filter đã làm)
    # ---------------------------------------------------------
    router = QuestionRouter()
    buckets = {
        "LARGE_BATCH": [], # Toán, Đọc hiểu
        "SMALL_BATCH": [], # Kiến thức chung
        "SAFETY": []       # Xử lý ngay
    }
    
    print("Classifying & Bucketing questions...")
    # Chỉ xử lý những câu CHƯA làm
    questions_to_process = [q for q in all_questions if str(q['qid']) not in processed_qids]
    
    if not questions_to_process:
        print("All questions completed!")
        return

    for q in tqdm(questions_to_process):
        q_type = router.classify(q['question'])
        
        if q_type == "SAFETY":
            buckets["SAFETY"].append(q)
        elif q_type in ["MATH", "READING"]:
            buckets["LARGE_BATCH"].append(q)
        else:
            buckets["SMALL_BATCH"].append(q)

    # Init Client & Solver
    client = VNPTClient()
    solver = Solver(client)

    # ---------------------------------------------------------
    # 4. XỬ LÝ SAFETY (Logic của bạn - Local Rule Based)
    # ---------------------------------------------------------
    if buckets["SAFETY"]:
        print(f"Processing {len(buckets['SAFETY'])} SAFETY questions (Local)...")
        for q in buckets["SAFETY"]:
            ans = solver.solve_safety_local(q['question'], q['choices'])
            if ans is None: 
                # Nếu rule-based không bắt được, đẩy sang Small Batch để AI làm
                buckets["SMALL_BATCH"].append(q)
            else:
                results.append({"qid": q['qid'], "answer": ans})
        
        # Save ngay sau khi xong Safety
        pd.DataFrame(results).to_csv(OUTPUT_PATH, index=False)

    # ---------------------------------------------------------
    # 5. XỬ LÝ BATCH (Logic của tôi - Để tối ưu tốc độ)
    # ---------------------------------------------------------
    def process_bucket(questions, model_type, batch_size):
        if not questions: return
        print(f"Processing {len(questions)} questions using {model_type.upper()} model (Batch size: {batch_size})...")
        
        num_batches = math.ceil(len(questions) / batch_size)
        pbar = tqdm(total=num_batches)
        
        for i in range(0, len(questions), batch_size):
            batch = questions[i : i + batch_size]
            
            # Gọi hàm solve_batch (đã thêm vào solver.py)
            try:
                batch_results = solver.solve_batch(batch, model_type=model_type)
                
                # Lưu kết quả
                for qid, ans in batch_results.items():
                    results.append({"qid": qid, "answer": ans})
            except Exception as e:
                print(f"Batch Error: {e}")
                # Fallback nếu cả batch lỗi: Điền A tạm
                for q in batch:
                    results.append({"qid": q['qid'], "answer": "A"})

            # Checkpoint liên tục
            pd.DataFrame(results).to_csv(OUTPUT_PATH, index=False)
            pbar.update(1)
            
            # Nghỉ nhẹ giữa các batch để giảm tải server (dù đã có rate limit trong client)
            time.sleep(1)
            
        pbar.close()

    # Chạy nhóm Large (Toán, Đọc hiểu) - Batch nhỏ hơn
    process_bucket(buckets["LARGE_BATCH"], "large", batch_size=BATCH_SIZE_LARGE)

    # Chạy nhóm Small (Kiến thức) - Batch lớn hơn
    process_bucket(buckets["SMALL_BATCH"], "small", batch_size=BATCH_SIZE_SMALL)

    # ---------------------------------------------------------
    # 6. FINAL CHECK & SAVE
    # ---------------------------------------------------------
    # Đảm bảo không sót câu nào (Fallback A cho những câu bị lỗi logic)
    final_processed_ids = set(str(r['qid']) for r in results)
    missing_count = 0
    for q in all_questions:
        if str(q['qid']) not in final_processed_ids:
            results.append({"qid": q['qid'], "answer": "A"})
            missing_count += 1
    
    if missing_count > 0:
        print(f"Filled {missing_count} missing answers with 'A'.")

    df_out = pd.DataFrame(results)
    df_out.to_csv(OUTPUT_PATH, index=False)
    print(f"=== COMPLETED. Total: {len(df_out)}. Saved to {OUTPUT_PATH} ===")

if __name__ == "__main__":
    main()