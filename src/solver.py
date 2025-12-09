import json
import re
from .utils import clean_text

class Solver:
    def __init__(self, client):
        self.client = client
    

    def get_valid_labels(self, choices):
        """
        Trả về danh sách nhãn hợp lệ dựa trên số lượng đáp án.
        Ví dụ: 4 đáp án -> ['A', 'B', 'C', 'D']
               10 đáp án -> ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
        """
        return [chr(65 + i) for i in range(len(choices))]

    def format_choices(self, choices):
        return "\n".join([f"{chr(65+i)}. {clean_text(str(choice))}" for i, choice in enumerate(choices)])

    def extract_answer_letter(self, text, valid_labels):
        """
        Trích xuất đáp án và kiểm tra xem nó có nằm trong range hợp lệ không.
        text: Output của LLM
        valid_labels: Danh sách các nhãn hợp lệ (ví dụ ['A', 'B', 'C', 'D', 'E'])
        """
        if not text: return None # Fallback
        
        # Chuẩn hóa văn bản trả về
        text = text.strip()
        
        # Pattern 1: Ưu tiên tìm định dạng rõ ràng "Đáp án: E" hoặc "Chọn E"
        # Hỗ trợ cả dấu chấm sau ký tự (ví dụ "E.")
        match = re.search(r'(?:áp án|là|chọn)[:\s]*([A-Z])', text, re.IGNORECASE)
        if match:
            ans = match.group(1).upper()
            if ans in valid_labels:
                return ans

        # Pattern 2: Tìm ký tự đứng một mình hoặc có dấu chấm/ngoặc (A., (A), [A])
        # Quét từ cuối chuỗi lên để lấy kết luận cuối cùng của model
        matches = re.findall(r'(?:^|[\s\(\[])([A-Z])(?:[\.\)\]]|$|\s)', text,re.IGNORECASE)
        if matches:
            # Lấy ký tự tìm thấy cuối cùng mà hợp lệ
            for ans in reversed(matches):
                if ans.upper() in valid_labels:
                    return ans.upper()
        
        # Pattern 3: Nếu model chỉ trả về đúng 1 ký tự duy nhất
        if len(text) == 1 and text.upper() in valid_labels:
            return text.upper()

        return None # Fallback cuối cùng nếu không tìm thấy gì

    def solve_safety(self, question, choices):
        # Lấy danh sách nhãn hợp lệ (ví dụ A-D hoặc A-J)
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
                    return chr(65 + i) # Trả về ký tự tương ứng (A, B, C...)
        
        return self.solve_knowledge(question, choices)

    def solve_reading(self, question, choices):
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
            return ans # Thành công với Large
        
        # --- FALLBACK: LARGE HỎNG -> DÙNG SMALL ---
        print("   -> ⚠️ Fallback to SMALL model (Reading)...")
        # Gọi hàm solve_knowledge (vốn dùng Small) để xử lý thay thế
        # Lưu ý: Small model yếu hơn nên ta dùng prompt đơn giản của solve_knowledge
        return self.solve_knowledge(question, choices)

    def solve_math(self, question, choices):
        valid_labels = self.get_valid_labels(choices)
        last_char = valid_labels[-1]

        prompt = f"""Giải bài toán sau:
{question}

Các lựa chọn:
{self.format_choices(choices)}

Hãy giải thích từng bước, sau đó kết luận bằng dòng: "Đáp án: X" (với X là một chữ cái từ A đến {last_char})."""
        
        messages = [{"role": "user", "content": prompt}]
        # Math bắt buộc dùng Large
        res = self.client.call_chat("large", messages, temperature=0.1)
        ans = self.extract_answer_letter(res, valid_labels)
        if ans:
            return ans # Thành công với Large

        # --- FALLBACK: LARGE HỎNG -> DÙNG SMALL ---
        print("   -> ⚠️ Fallback to SMALL model (Math)...")
        # Small model không giỏi Chain-of-Thought phức tạp, nên gửi prompt đơn giản
        return self.solve_knowledge(question, choices)

    def solve_knowledge(self, question, choices):
        valid_labels = self.get_valid_labels(choices)
        last_char = valid_labels[-1]

        prompt = f"""Câu hỏi: {question}

Các lựa chọn:
{self.format_choices(choices)}

Đáp án đúng là (chỉ ghi 1 chữ cái từ A đến {last_char}):"""
        
        messages = [{"role": "user", "content": prompt}]
        
        # Knowledge dùng Small để tiết kiệm, nhưng nếu câu hỏi quá dài (nhiều lựa chọn) thì nên cân nhắc Large
        # Ở đây ta giữ Small cho tiết kiệm
        res = self.client.call_chat("small", messages, temperature=0.1)
        ans = self.extract_answer_letter(res, valid_labels)
        if ans:
            return ans
        
        # Nếu Small cũng hỏng (hoặc hết quota cả 2) -> Chọn bừa A
        return "A"
    def solve_safety_local(self, question, choices):
        """
        Phiên bản rút gọn của solve_safety, chỉ trả về đáp án nếu tìm thấy từ khóa từ chối.
        Không gọi API (để dùng trong vòng lặp lọc trước khi batching).
        """
        refusal_keywords = [
            "tôi không thể", "không thể trả lời", "từ chối", 
            "vi phạm pháp luật", "không được phép", "ngoài phạm vi",
            "tôi không thể chia sẻ", "tôi từ chối"
        ]
        
        for i, choice in enumerate(choices):
            clean_c = str(choice).lower()
            for kw in refusal_keywords:
                if kw in clean_c:
                    return chr(65 + i)
        return None # Trả về None để biết là cần đẩy vào Batch xử lý bằng AI

    def format_batch_prompt(self, batch_questions):
        """
        Tạo prompt chứa nhiều câu hỏi cùng lúc.
        """
        prompt = "Hãy trả lời danh sách các câu hỏi trắc nghiệm sau đây.\n"
        prompt += "Yêu cầu: Trả về kết quả dưới dạng JSON Object, với key là ID câu hỏi (ví dụ 'q1') và value là chữ cái đáp án đúng (A, B, C...).\n"
        prompt += "Ví dụ format: {\"test_001\": \"A\", \"test_002\": \"C\"}\n\n"
        prompt += "DANH SÁCH CÂU HỎI:\n"

        for q in batch_questions:
            # Tận dụng hàm format_choices cũ
            choices_str = self.format_choices(q['choices'])
            prompt += f"--- ID: {q['qid']} ---\n"
            prompt += f"Câu hỏi: {q['question']}\n"
            prompt += f"Lựa chọn:\n{choices_str}\n\n"
        
        prompt += "HẾT.\nTuyệt đối chỉ trả về JSON đúng định dạng, không giải thích gì thêm."
        return prompt

    def parse_batch_response(self, response_text, batch_qids):
        """
        Phân tích JSON từ câu trả lời batch của model.
        Nếu JSON lỗi, dùng Regex để cứu vớt từng câu.
        """
        results = {}
        if not response_text:
            return {qid: "A" for qid in batch_qids} # Fallback nếu API lỗi

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
        
        # 2. Regex Fallback (Nếu JSON lỗi hoặc thiếu câu hỏi)
        # Tìm pattern: "qid": "A" hoặc qid: A
        for qid in batch_qids:
            if qid not in results:
                # Regex tìm ID cụ thể trong mớ hỗn độn
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
        """
        batch_qids = [q['qid'] for q in batch_questions]
        prompt = self.format_batch_prompt(batch_questions)
        
        messages = [{"role": "user", "content": prompt}]
        
        # Gọi API với max_tokens lớn để chứa đủ JSON trả về
        response_text = self.client.call_chat(model_type, messages, temperature=0.1, max_tokens=4096)
        
        return self.parse_batch_response(response_text, batch_qids)