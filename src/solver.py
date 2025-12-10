import json
import re
import time
from .utils import clean_text

class Solver:
    def __init__(self, client):
        self.client = client
    
    # =========================================================================
    # CÁC HÀM HỖ TRỢ XỬ LÝ VĂN BẢN VÀ ĐÁP ÁN
    # =========================================================================

    def get_valid_labels(self, choices):
        """
        Trả về danh sách nhãn hợp lệ dựa trên số lượng đáp án.
        Ví dụ: 4 đáp án -> ['A', 'B', 'C', 'D']
               10 đáp án -> ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
        """
        return [chr(65 + i) for i in range(len(choices))]

    def format_choices(self, choices):
        """
        Định dạng danh sách lựa chọn thành chuỗi:
        A. Lựa chọn 1
        B. Lựa chọn 2
        ...
        """
        return "\n".join([f"{chr(65+i)}. {clean_text(str(choice))}" for i, choice in enumerate(choices)])

    def extract_answer_letter(self, text, valid_labels):
        """
        Trích xuất ký tự đáp án từ phản hồi của LLM.
        Chỉ chấp nhận ký tự nằm trong valid_labels.
        """
        if not text: return None # Fallback nếu API lỗi trả về None
        
        # Chuẩn hóa văn bản trả về
        text = text.strip()
        
        # Pattern 1: Ưu tiên tìm định dạng rõ ràng "Đáp án: E" hoặc "Chọn E"
        match = re.search(r'(?:áp án|là|chọn)[:\s]*([A-Z])', text, re.IGNORECASE)
        if match:
            ans = match.group(1).upper()
            if ans in valid_labels:
                return ans

        # Pattern 2: Tìm ký tự đứng một mình hoặc có dấu chấm/ngoặc (A., (A), [A])
        # Quét từ cuối chuỗi lên để lấy kết luận cuối cùng của model
        matches = re.findall(r'(?:^|[\s\(\[])([A-Z])(?:[\.\)\]]|$|\s)', text, re.IGNORECASE)
        
        if matches:
            # Lấy ký tự tìm thấy CUỐI CÙNG trong chuỗi mà hợp lệ
            for ans in reversed(matches):
                if ans.upper() in valid_labels:
                    return ans.upper()
        
        # Pattern 3: Nếu model chỉ trả về đúng 1 ký tự duy nhất
        if len(text) == 1 and text.upper() in valid_labels:
            return text.upper()

        return None # Trả về None để báo hiệu cần Fallback (chưa vội chọn A)

    # =========================================================================
    # CÁC HÀM GIẢI QUYẾT TỪNG CÂU (SINGLE MODE) - CÓ FALLBACK
    # =========================================================================

    def solve_safety(self, question, choices):
        """
        Xử lý câu hỏi an toàn (có gọi API fallback nếu không tìm thấy keyword).
        """
        valid_labels = self.get_valid_labels(choices)
        
        refusal_keywords = [
            "tôi không thể", "không thể trả lời", "từ chối", 
            "vi phạm pháp luật", "không được phép", "ngoài phạm vi",
            "tôi không thể chia sẻ", "tôi từ chối"
        ]
        
        # Quét keyword trong các lựa chọn
        for i, choice in enumerate(choices):
            clean_choice = str(choice).lower() 
            for kw in refusal_keywords:
                if kw in clean_choice:
                    return chr(65 + i)
        
        # Nếu không tìm thấy từ chối -> Chuyển sang giải như câu hỏi kiến thức
        return self.solve_knowledge(question, choices)

    def solve_safety_local(self, question, choices):
        """
        Hàm xử lý safety offline (KHÔNG gọi API).
        Dùng để lọc nhanh trước khi đưa vào Batch.
        """
        refusal_keywords = [
            "tôi không thể", "không thể trả lời", "từ chối", 
            "vi phạm pháp luật", "không được phép", "ngoài phạm vi",
            "tôi không thể chia sẻ", "tôi từ chối",
            "lật đổ", "phản động", "kích động", "bạo lực", 
            "khiêu dâm", "trốn thuế", "làm giả", "tham nhũng",
            "bí mật quốc gia", "xúc phạm lãnh tụ"
        ]
        
        # Kiểm tra cả trong CÂU HỎI và ĐÁP ÁN
        combined_text = (question + " " + " ".join(map(str, choices))).lower()
        
        # Nếu câu hỏi hỏi về cách làm việc xấu
        if "làm thế nào để" in question.lower() or "hướng dẫn" in question.lower():
             for kw in ["trốn", "lậu", "giả", "bom", "thuốc nổ"]:
                 if kw in question.lower():
                     for i, choice in enumerate(choices):
                         if "không" in str(choice).lower() or "từ chối" in str(choice).lower():
                             return chr(65 + i)

        # Logic cũ: Tìm trong đáp án
        for i, choice in enumerate(choices):
            clean_c = str(choice).lower()
            for kw in refusal_keywords:
                if kw in clean_c:
                    return chr(65 + i)
        return None

    def solve_reading(self, question, choices):
        """
        Giải câu hỏi đọc hiểu (Dùng Large Model).
        """
        valid_labels = self.get_valid_labels(choices)
        last_char = valid_labels[-1]
        
        prompt = f"""Đọc đoạn thông tin trên và trả lời câu hỏi dưới đây.
        
{question}

Các lựa chọn:
{self.format_choices(choices)}

Hãy suy luận và chỉ đưa ra một chữ cái duy nhất (từ A đến {last_char}) tương ứng với đáp án đúng.
Ví dụ: Đáp án: A"""
        
        messages = [{"role": "user", "content": prompt}]
        
        # Reading bắt buộc dùng Large
        res = self.client.call_chat("large", messages, temperature=0.1)
        ans = self.extract_answer_letter(res, valid_labels)
        
        if ans: 
            return ans
        
        # Fallback: Chuyển sang Small model
        print("   -> ⚠️ Fallback to SMALL model (Reading)...")
        return self.solve_knowledge(question, choices)

    def solve_math(self, question, choices):
        """
        Giải câu hỏi toán/logic (Dùng Large Model + CoT).
        """
        valid_labels = self.get_valid_labels(choices)
        last_char = valid_labels[-1]

        prompt = f"""Bạn là chuyên gia toán học. Hãy giải bài toán sau thật cẩn thận:
{question}

Các lựa chọn:
{self.format_choices(choices)}

Yêu cầu:
1. Suy nghĩ từng bước logic để tìm ra kết quả.
2. So sánh kết quả với các lựa chọn.
3. Kết luận bằng dòng: "Đáp án: X" (với X là một chữ cái từ A đến {last_char})."""
        
        messages = [{"role": "user", "content": prompt}]
        # Math bắt buộc dùng Large
        res = self.client.call_chat("large", messages, temperature=0.1)
        ans = self.extract_answer_letter(res, valid_labels)
        
        if ans:
            return ans

        # Fallback: Chuyển sang Small model
        print("   -> ⚠️ Fallback to SMALL model (Math)...")
        return self.solve_knowledge(question, choices)

    def solve_knowledge(self, question, choices):
        """
        Giải câu hỏi kiến thức chung (Dùng Small Model).
        """
        valid_labels = self.get_valid_labels(choices)
        last_char = valid_labels[-1]

        prompt = f"""Bạn là một trợ lý AI am hiểu sâu sắc về Văn hóa, Lịch sử, Địa lý và Pháp luật Việt Nam.
Hãy trả lời câu hỏi trắc nghiệm sau:

Câu hỏi: {question}

Các lựa chọn:
{self.format_choices(choices)}

Đáp án đúng là (chỉ ghi 1 chữ cái từ A đến {last_char}):"""
        
        messages = [{"role": "user", "content": prompt}]
        res = self.client.call_chat("small", messages, temperature=0.1)
        
        ans = self.extract_answer_letter(res, valid_labels)
        if ans:
            return ans
            
        return "A" # Fallback cuối cùng nếu cả 2 model đều chết

    # =========================================================================
    # PHẦN 3: BATCH PROCESSING (XỬ LÝ THEO LÔ ĐỂ TỐI ƯU TỐC ĐỘ)
    # =========================================================================

    def format_batch_prompt(self, batch_questions):
        """
        Tạo prompt chứa nhiều câu hỏi cùng lúc (JSON Format).
        """
        prompt = "Hãy trả lời danh sách các câu hỏi trắc nghiệm sau đây.\n"
        prompt += "Yêu cầu: Trả về kết quả dưới dạng JSON Object, với key là ID câu hỏi (ví dụ 'q1') và value là chữ cái đáp án đúng (A, B, C...).\n"
        prompt += "Ví dụ format: {\"test_001\": \"A\", \"test_002\": \"C\"}\n\n"
        prompt += "DANH SÁCH CÂU HỎI:\n"

        for q in batch_questions:
            choices_str = self.format_choices(q['choices'])
            prompt += f"--- ID: {q['qid']} ---\n"
            prompt += f"Câu hỏi: {q['question']}\n"
            prompt += f"Lựa chọn:\n{choices_str}\n\n"
        
        prompt += "HẾT.\nTuyệt đối chỉ trả về JSON đúng định dạng, không giải thích gì thêm."
        return prompt

    def parse_batch_response(self, response_text, batch_qids):
        """
        Phân tích JSON từ câu trả lời batch của model.
        Sử dụng Regex Fallback nếu JSON bị lỗi.
        """
        results = {}
        if not response_text:
            return {qid: "A" for qid in batch_qids} # Fallback tạm thời là A nếu API lỗi

        # 1. Thử Parse JSON chuẩn
        try:
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if match:
                json_str = match.group(0)
                data = json.loads(json_str)
                for k, v in data.items():
                    # Lấy chữ cái đầu tiên của value (A, B, C...) và Upper
                    results[str(k)] = str(v).strip().upper()[0] 
        except:
            print(f"   [Batch Parse Warning] JSON failed. Switching to Regex fallback.")
        
        # 2. Regex Fallback (Tìm từng ID trong văn bản)
        for qid in batch_qids:
            if qid not in results:
                # Sử dụng raw string (rf) để tránh SyntaxWarning với \s
                pattern = rf"[\"']?{re.escape(qid)}[\"']?\s*[:=]\s*[\"']?([A-J])[\"']?"
                m = re.search(pattern, response_text, re.IGNORECASE)
                if m:
                    results[qid] = m.group(1).upper()
                else:
                    results[qid] = "A" # Không tìm thấy thì đành chọn A

        return results

    def solve_batch(self, batch_questions, model_type="small"):
        """
        Xử lý nguyên một lô câu hỏi.
        Nếu thất bại, tự động chuyển sang xử lý từng câu (Sequential Fallback).
        """
        batch_qids = [q['qid'] for q in batch_questions]
        prompt = self.format_batch_prompt(batch_questions)
        
        messages = [{"role": "user", "content": prompt}]
        
        # 1. Thử gọi API (Max tokens lớn để chứa đủ JSON)
        response_text = self.client.call_chat(model_type, messages, temperature=0.1, max_tokens=4096)
        
        # 2. Phân tích kết quả
        results = self.parse_batch_response(response_text, batch_qids)
        
        # 3. KIỂM TRA CHẤT LƯỢNG BATCH (Logic Cứu hộ)
        # Nếu API trả về None HOẶC quá nhiều câu trả lời là 'A' (dấu hiệu model lười hoặc lỗi parse)
        a_count = sum(1 for v in results.values() if v == "A")
        
        if not response_text or (len(batch_questions) > 2 and a_count == len(batch_questions)):
            print(f"   -> Batch failed or suspicious (All A). Switching to SEQUENTIAL processing for this batch...")
            
            # --- CƠ CHẾ CỨU HỘ: CHẠY LẠI TỪNG CÂU ---
            results = {}
            for q in batch_questions:
                try:
                    # Tự động định tuyến lại cho phù hợp
                    if len(q['question'].split()) > 150 or "đoạn thông tin" in q['question'].lower():
                         ans = self.solve_reading(q['question'], q['choices'])
                    else:
                         ans = self.solve_knowledge(q['question'], q['choices'])
                    
                    results[q['qid']] = ans
                    
                    # Nghỉ nhẹ giữa các câu cứu hộ
                    time.sleep(2) 
                except:
                    results[q['qid']] = "A" # Chịu thua
                    
        return results