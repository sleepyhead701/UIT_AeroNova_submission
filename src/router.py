import re
class QuestionRouter:
    def classify(self, question_text):
        """
        Trả về: 'MATH', 'READING', 'SAFETY', 'KNOWLEDGE'
        """
        text_lower = question_text.lower()

        # 1. Phát hiện câu hỏi Đọc hiểu (Có đoạn văn trong input)
        # Dấu hiệu: "Đoạn thông tin:", "Title:", "Content:" như trong test.json
        if "đoạn thông tin" in text_lower or "title:" in text_lower or "content:" in text_lower:
            return "READING"
        if len(text_lower.split()) > 150:
            return "READING"

        # 2. Phát hiện câu hỏi Toán học/Logic
        # Dấu hiệu: LaTeX ($), từ khóa toán học
        math_keywords = [
            r"\$", "giá trị của", "tính", "phương trình", "hàm số", 
            "xác suất", "tọa độ", "tam giác", "hình trụ", "nguyên hàm", "biểu thức", "tích phân", "vector"
        ]
        for kw in math_keywords:
            if re.search(kw, text_lower):
                return "MATH"

        # 3. Phát hiện câu hỏi An toàn/Nhạy cảm (Safety)
        # Dấu hiệu: Hỏi về lách luật, trốn thuế, bôi nhọ, bí mật nhà nước
        safety_keywords = [
            "trốn thuế", "làm giả", "tham nhũng", "lật đổ", "phản động", 
            "bí mật nhà nước", "xúc phạm", "bạo loạn", "vũ khí", "ma túy",
            "cách nào để", "làm thế nào để"
        ]
        for kw in safety_keywords:
            if kw in text_lower:
                return "SAFETY"

        # 4. Mặc định là kiến thức chung (Cần RAG hoặc knowledge nội tại)
        return "KNOWLEDGE"