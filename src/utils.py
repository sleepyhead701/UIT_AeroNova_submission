

import re
import json

def clean_text(text):
    """
    Làm sạch văn bản đầu vào: xóa khoảng trắng thừa, ký tự rác.
    """
    if not isinstance(text, str):
        return ""
    
    # Xóa các ký tự unicode ẩn hoặc lỗi
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', text)
    
    # Thay thế nhiều khoảng trắng bằng 1 khoảng trắng
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def parse_json_garbage(text):
    """
    Cố gắng đọc JSON từ output của LLM nếu nó bị lẫn text.
    Ví dụ: "Kết quả là: {'answer': 'A'}" -> Lấy phần dict
    """
    try:
        # Tìm đoạn bắt đầu bằng { và kết thúc bằng }
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
    except:
        pass
    return None