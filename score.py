import json
import pandas as pd
import os

# Cấu hình đường dẫn file gốc và file dự đoán
VAL_FILE = "data/val.json"
PRED_FILE = "output/submission_val.csv"

def calculate_score():
    if not os.path.exists(VAL_FILE) or not os.path.exists(PRED_FILE):
        print("Lỗi: Không tìm thấy file dữ liệu hoặc file dự đoán.")
        return

    # 1. Đọc đáp án gốc (Ground Truth)
    try:
        with open(VAL_FILE, 'r', encoding='utf-8') as f:
            val_data = json.load(f)
            # Tạo dictionary {qid: answer_chuẩn}
            # Lưu ý: Cần chắc chắn key trong json là 'answer' hay 'correct_option' hay gì đó
            # Code này giả định key là 'answer'
            ground_truth = {str(item['qid']): str(item.get('answer', '')).strip().upper() for item in val_data}
    except Exception as e:
        print(f"Lỗi đọc file JSON: {e}")
        return

    # 2. Đọc kết quả dự đoán
    try:
        df_pred = pd.read_csv(PRED_FILE)
        # Tạo dictionary {qid: answer_dự_đoán}
        predictions = {str(row['qid']): str(row['answer']).strip().upper() for _, row in df_pred.iterrows()}
    except Exception as e:
        print(f"Lỗi đọc file CSV: {e}")
        return

    # 3. So sánh
    correct = 0
    total = 0
    missing = 0
    wrong_list = []

    print("-" * 30)
    print("CHI TIẾT CHẤM ĐIỂM")
    print("-" * 30)

    for qid, true_ans in ground_truth.items():
        if not true_ans: continue # Bỏ qua nếu data gốc không có đáp án
        
        total += 1
        pred_ans = predictions.get(qid, "N/A")

        if pred_ans == "N/A":
            missing += 1
        elif pred_ans == true_ans:
            correct += 1
        else:
            wrong_list.append(f"QID: {qid} | True: {true_ans} | Pred: {pred_ans}")

    # 4. Báo cáo
    if total == 0:
        print("Không tìm thấy đáp án trong file gốc để chấm.")
        return

    accuracy = (correct / total) * 100
    
    print(f"Tổng số câu: {total}")
    print(f"Số câu đúng: {correct}")
    print(f"Số câu sai:  {len(wrong_list)}")
    print(f"Số câu thiếu: {missing}")
    print("-" * 30)
    print(f"ĐỘ CHÍNH XÁC (ACCURACY): {accuracy:.2f}%")
    print("-" * 30)
    
    # In ra 10 câu sai đầu tiên để debug
    if wrong_list:
        print("\nVí dụ 10 câu sai đầu tiên:")
        for w in wrong_list[:10]:
            print(w)

if __name__ == "__main__":
    calculate_score()