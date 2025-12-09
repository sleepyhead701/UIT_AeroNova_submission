import requests
import json
import time
from .config import API_CONFIG

class VNPTClient:
    def __init__(self):
        self.headers_template = {
            'Content-Type': 'application/json'
        }
        self.last_call_time = {
            "small": 0,
            "large": 0
        }
        self.min_interval = {
            "small": 65,
            "large": 95
        }
    def _wait_for_rate_limit(self, model_type):
        """Hàm bắt buộc chờ để không vi phạm Rate Limit"""
        elapsed = time.time() - self.last_call_time[model_type]
        wait_time = self.min_interval[model_type] - elapsed
        if wait_time > 0:
            print(f"   [RateLimit] {model_type}: Waiting {wait_time:.1f}s...")
            time.sleep(wait_time)
        self.last_call_time[model_type] = time.time()

    def _get_headers(self, model_type):
        cfg = API_CONFIG[model_type]
        headers = self.headers_template.copy()
        headers['Authorization'] = cfg['token'] 
        headers['Token-id'] = cfg['token_id']
        headers['Token-key'] = cfg['token_key']
        return headers

    def call_chat(self, model_type, messages, temperature=0.1, max_tokens=4096):
        """
        model_type: 'small' or 'large'
        """
        # Chờ trước khi gọi
        self._wait_for_rate_limit(model_type)

        cfg = API_CONFIG[model_type]
        model_name = f"vnptai_hackathon_{model_type}"
        
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "top_p": 0.9,
            "top_k": 20,
            "max_completion_tokens": max_tokens,
            "stream": False
        }

        retries = 5
        for i in range(retries):
            try:
                print(f"   -> Sending request to {model_type}...")
                response = requests.post(
                    cfg['url'], 
                    headers=self._get_headers(model_type), 
                    json=payload, 
                    timeout=120
                )
                if response.status_code == 200:
                    data = response.json()
                    if 'choices' in data and len(data['choices']) > 0:
                        return data['choices'][0]['message']['content']
                    return None
                elif response.status_code in [401, 429]:
                    print(f"!!! Rate/Quota Error {response.status_code}. Waiting 2 min...")
                    time.sleep(120)
                else:
                    print(f"Error {response.status_code}. Retry...")
                    time.sleep(5)
            except Exception as e:
                print(f"Exception: {e}")
                time.sleep(5)
        
        return None