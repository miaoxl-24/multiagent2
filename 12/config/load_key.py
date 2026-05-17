import os
import json

def load_key(key_name: str) -> str:
    """从环境变量或 JSON 配置文件中读取 API key"""
    # 首先尝试从环境变量中读取
    value = os.getenv(key_name)
    if value:
        return value
    
    # 尝试从 Keys.json 文件中读取
    config_dir = os.path.dirname(os.path.abspath(__file__))
    keys_path = os.path.join(config_dir, "Keys.json")
    
    if os.path.exists(keys_path):
        with open(keys_path, 'r', encoding='utf-8') as f:
            keys = json.load(f)
            if key_name in keys:
                return keys[key_name]
    
    raise ValueError(f"API key '{key_name}' not found in environment variables or Keys.json")