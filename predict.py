import json
import pandas as pd
import os
import time
from tqdm import tqdm
from src.api_client import VNPTClient
from src.router import QuestionRouter
from src.solver import Solver
from src.config import INPUT_PATH, OUTPUT_PATH

def main():
    print("=== STARTING PIPELINE WITH RESUME ===")
    
    # 1. Load Data
    if not os.path.exists(INPUT_PATH):
        print(f"ERROR: Input not found at {INPUT_PATH}")
        return

    try:
        with open(INPUT_PATH, 'r', encoding='utf-8') as f:
            questions = json.load(f)
    except:
        df = pd.read_csv(INPUT_PATH)
        questions = []
        for _, row in df.iterrows():
            questions.append({
                "qid": row.get('id', row.get('qid')),
                "question": row['question'],
                "choices": [row['option_1'], row['option_2'], row['option_3'], row['option_4']]
            })
            
    # 2. Check processed questions (Tính năng Resume)
    processed_qids = set()
    results = []
    
    if os.path.exists(OUTPUT_PATH):
        try:
            df_done = pd.read_csv(OUTPUT_PATH)
            if 'qid' in df_done.columns and 'answer' in df_done.columns:
                processed_qids = set(df_done['qid'].astype(str))
                results = df_done.to_dict('records')
                print(f"-> Found existing result file. Resuming from {len(results)}/{len(questions)} questions.")
        except Exception as e:
            print(f"-> Warning: Could not read existing file ({e}). Starting fresh.")

    # 3. Init
    client = VNPTClient()
    router = QuestionRouter()
    solver = Solver(client)

    # 4. Run Loop
    questions_to_process = [q for q in questions if str(q['qid']) not in processed_qids]
    
    if not questions_to_process:
        print("All questions already processed!")
        return

    print(f"Processing remaining {len(questions_to_process)} questions...")

    for i, item in enumerate(tqdm(questions_to_process)):
        # Save checkpoint mỗi 10 câu (để lỡ sập thì không mất hết)
        if i > 0 and i % 10 == 0:
            pd.DataFrame(results).to_csv(OUTPUT_PATH, index=False)
        
        time.sleep(1) # Delay bảo vệ quota
        
        qid = item['qid']
        q_text = item['question']
        choices = item['choices']
        
        q_type = router.classify(q_text)
        
        try:
            if q_type == "SAFETY":
                ans = solver.solve_safety(q_text, choices)
            elif q_type == "READING":
                ans = solver.solve_reading(q_text, choices)
            elif q_type == "MATH":
                ans = solver.solve_math(q_text, choices)
            else:
                ans = solver.solve_knowledge(q_text, choices)
        except Exception as e:
            print(f"Error {qid}: {e}")
            ans = "A"

        results.append({"qid": qid, "answer": ans})

    # 5. Save Final
    df_out = pd.DataFrame(results)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df_out.to_csv(OUTPUT_PATH, index=False)
    print(f"=== COMPLETED. Saved to {OUTPUT_PATH} ===")

if __name__ == "__main__":
    main()