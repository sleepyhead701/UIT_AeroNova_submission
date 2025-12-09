import requests
import json
import time
from .config import API_CONFIG

class VNPTClient:
    def __init__(self):
        self.headers_template = {
            'Content-Type': 'application/json'
        }

    def _get_headers(self, model_type):
        cfg = API_CONFIG[model_type]
        headers = self.headers_template.copy()
        headers['Authorization'] = cfg['token'] 
        headers['Token-id'] = cfg['token_id']
        headers['Token-key'] = cfg['token_key']
        return headers

    def call_chat(self, model_type, messages, temperature=0.1, max_tokens=512):
        """
        model_type: 'small' or 'large'
        """
        cfg = API_CONFIG[model_type]
        model_name = f"vnptai_hackathon_{model_type}"
        
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "top_p": 0.7,
            "top_k": 30,
            "max_completion_tokens": max_tokens,
            "stream": False
        }

        retries = 5
        for i in range(retries):
            try:
                response = requests.post(
                    cfg['url'], 
                    headers=self._get_headers(model_type), 
                    json=payload, 
                    timeout=30
                )
                if response.status_code == 200:
                    data = response.json()
                    if 'choices' in data and len(data['choices']) > 0:
                        return data['choices'][0]['message']['content']
                    return None
                elif response.status_code == 401:
                    print(f"⚠️ [QUOTA EXCEEDED] Model {model_type} died (401).")
                    return None
                elif response.status_code == 429:
                    wait = 15 * (i + 1)
                    print(f"⏳ Rate limit (429). Waiting {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"Error {response.status_code}: {response.text}. Retrying...")
                    time.sleep(2)
            except Exception as e:
                print(f"Exception: {e}. Retrying...")
                time.sleep(2)
        return None