import os

API_CONFIG = {
    "embedding": {
        "llmApiName": "LLM embedings",
        "url": "https://api.idg.vnpt.vn/data-service/vnptai-hackathon-embedding",
        "token": "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0cmFuc2FjdGlvbl9pZCI6ImVkNGEzNTFhLWZkZGQtNDI0ZS04OGUxLTIxNDQ5ZTQxYzBkMyIsInN1YiI6ImEyMTA3ZDBlLWQxZTktMTFmMC1hNzY5LTFmZDhiZGM5YjA2YiIsImF1ZCI6WyJyZXN0c2VydmljZSJdLCJ1c2VyX25hbWUiOiJwaHVjZXJhdGVkQGdtYWlsLmNvbSIsInNjb3BlIjpbInJlYWQiXSwiaXNzIjoiaHR0cHM6Ly9sb2NhbGhvc3QiLCJuYW1lIjoicGh1Y2VyYXRlZEBnbWFpbC5jb20iLCJ1dWlkX2FjY291bnQiOiJhMjEwN2QwZS1kMWU5LTExZjAtYTc2OS0xZmQ4YmRjOWIwNmIiLCJhdXRob3JpdGllcyI6WyJVU0VSIiwiVFJBQ0tfMiJdLCJqdGkiOiIyMmIyYmQzOS05Y2VhLTRmZTYtODFmZC0zOWMzZDkzMTY0ZWEiLCJjbGllbnRfaWQiOiJhZG1pbmFwcCJ9.hSw-z5tmw8Qtez8j87N23XGc-BLowN-NoEb5NJhB4eQoSTrkfhpC5iZV2f9Fx7vxagKKZNb0-nNBFVsdvUYnTQZlYrxdK8eOETon4ZRttSKAUAZyp4pTPKlDOayv38VnenD2oKewsqNGVDGCnE3hlZsao8s0Y3DTDemDvVoxQBrqv6vsSH3XqSyds6WJf-vLlxV2pFApf1_Ti5wGZgcuuPDu_ZWiytyHViN-MF4kKc121mWCLt-AHTFCEXoWGrMId0dxWBhUfTKWUSONNbqu_2h9WOh9AbhuTqsHqOO4BoRfEzNANH5vzQki29XXpMXU4uQYSrXz-i0PwCEesYxamA", 
        "token_id": "45381bb4-83c2-5ccb-e063-62199f0adfde",
        "token_key": "MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAKNWfP0LtXk1JgHFzejRDrAAbcJRqFgl+W0O+FwzAY/CM88XFjNWtcP3rcyZFyOF77jsNskvCCp669XkMeceW3MCAwEAAQ=="
    },
    "small": {
        "llmApiName": "LLM small",
        "url": "https://api.idg.vnpt.vn/data-service/v1/chat/completions/vnptai-hackathon-small",
        "token": "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0cmFuc2FjdGlvbl9pZCI6ImVkNGEzNTFhLWZkZGQtNDI0ZS04OGUxLTIxNDQ5ZTQxYzBkMyIsInN1YiI6ImEyMTA3ZDBlLWQxZTktMTFmMC1hNzY5LTFmZDhiZGM5YjA2YiIsImF1ZCI6WyJyZXN0c2VydmljZSJdLCJ1c2VyX25hbWUiOiJwaHVjZXJhdGVkQGdtYWlsLmNvbSIsInNjb3BlIjpbInJlYWQiXSwiaXNzIjoiaHR0cHM6Ly9sb2NhbGhvc3QiLCJuYW1lIjoicGh1Y2VyYXRlZEBnbWFpbC5jb20iLCJ1dWlkX2FjY291bnQiOiJhMjEwN2QwZS1kMWU5LTExZjAtYTc2OS0xZmQ4YmRjOWIwNmIiLCJhdXRob3JpdGllcyI6WyJVU0VSIiwiVFJBQ0tfMiJdLCJqdGkiOiIyMmIyYmQzOS05Y2VhLTRmZTYtODFmZC0zOWMzZDkzMTY0ZWEiLCJjbGllbnRfaWQiOiJhZG1pbmFwcCJ9.hSw-z5tmw8Qtez8j87N23XGc-BLowN-NoEb5NJhB4eQoSTrkfhpC5iZV2f9Fx7vxagKKZNb0-nNBFVsdvUYnTQZlYrxdK8eOETon4ZRttSKAUAZyp4pTPKlDOayv38VnenD2oKewsqNGVDGCnE3hlZsao8s0Y3DTDemDvVoxQBrqv6vsSH3XqSyds6WJf-vLlxV2pFApf1_Ti5wGZgcuuPDu_ZWiytyHViN-MF4kKc121mWCLt-AHTFCEXoWGrMId0dxWBhUfTKWUSONNbqu_2h9WOh9AbhuTqsHqOO4BoRfEzNANH5vzQki29XXpMXU4uQYSrXz-i0PwCEesYxamA", 
        "token_id": "45381bb8-b957-28d4-e063-62199f0ae609",
        "token_key": "MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAKn0ZIQA+znudLhxaQOjVZKCCoT081VyKbAiNTBnFYy51VW0tteJLV4EMMU/Dv3R1/LaQ9OkayT+HEaX4f1KSHsCAwEAAQ=="
    },
    "large": {
        "llmApiName": "LLM large",
        "url": "https://api.idg.vnpt.vn/data-service/v1/chat/completions/vnptai-hackathon-large",
        "token": "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0cmFuc2FjdGlvbl9pZCI6ImVkNGEzNTFhLWZkZGQtNDI0ZS04OGUxLTIxNDQ5ZTQxYzBkMyIsInN1YiI6ImEyMTA3ZDBlLWQxZTktMTFmMC1hNzY5LTFmZDhiZGM5YjA2YiIsImF1ZCI6WyJyZXN0c2VydmljZSJdLCJ1c2VyX25hbWUiOiJwaHVjZXJhdGVkQGdtYWlsLmNvbSIsInNjb3BlIjpbInJlYWQiXSwiaXNzIjoiaHR0cHM6Ly9sb2NhbGhvc3QiLCJuYW1lIjoicGh1Y2VyYXRlZEBnbWFpbC5jb20iLCJ1dWlkX2FjY291bnQiOiJhMjEwN2QwZS1kMWU5LTExZjAtYTc2OS0xZmQ4YmRjOWIwNmIiLCJhdXRob3JpdGllcyI6WyJVU0VSIiwiVFJBQ0tfMiJdLCJqdGkiOiIyMmIyYmQzOS05Y2VhLTRmZTYtODFmZC0zOWMzZDkzMTY0ZWEiLCJjbGllbnRfaWQiOiJhZG1pbmFwcCJ9.hSw-z5tmw8Qtez8j87N23XGc-BLowN-NoEb5NJhB4eQoSTrkfhpC5iZV2f9Fx7vxagKKZNb0-nNBFVsdvUYnTQZlYrxdK8eOETon4ZRttSKAUAZyp4pTPKlDOayv38VnenD2oKewsqNGVDGCnE3hlZsao8s0Y3DTDemDvVoxQBrqv6vsSH3XqSyds6WJf-vLlxV2pFApf1_Ti5wGZgcuuPDu_ZWiytyHViN-MF4kKc121mWCLt-AHTFCEXoWGrMId0dxWBhUfTKWUSONNbqu_2h9WOh9AbhuTqsHqOO4BoRfEzNANH5vzQki29XXpMXU4uQYSrXz-i0PwCEesYxamA",
        "token_id": "45381bc9-22cf-5d25-e063-63199f0abbeb",
        "token_key": "MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAJCcJ8bkHyqdG9en9KPrcBanF2lcsQ9dy3/K67duZVyZUyGwfArTTZaiJB8Ph3QWkc5IypLb/WV/NotTrx5sgSECAwEAAQ=="
    }
}


#INPUT_PATH = "/data/private_test.json" 
#OUTPUT_PATH = "/output/submission.csv"
#DB_PATH = "/code/chroma_db" 

#BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#INPUT_PATH = os.path.join(BASE_DIR, "data", "val.json") 
#OUTPUT_PATH = os.path.join(BASE_DIR, "output", "submission_val.csv")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_PATH = os.path.join(BASE_DIR, "data", "private_test.json") 
OUTPUT_PATH = os.path.join(BASE_DIR, "output", "submission_test3.csv")

#BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#INPUT_PATH = os.path.join(BASE_DIR, "data", "part.json") 
#OUTPUT_PATH = os.path.join(BASE_DIR, "output", "submission_test1.csv")