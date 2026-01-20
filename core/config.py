import json
import os

CONFIG_FILE = "config.json"

# 这里定义“内存版”的默认配置
DEFAULT_CONFIG = {
    "api_key": "",
    "base_url": "https://api.deepseek.com",  # 默认给一个常用的
    "model": "deepseek-chat",
    "hotkey_grammar": "f9",
    "hotkey_translate": "ctrl+t",
    "close_to_tray": True
}


class ConfigManager:
    def __init__(self):
        # 初始化时只读取，绝对不写入
        self.config = self.load_config()

    def load_config(self):
        # 1. 如果文件不存在，直接返回默认配置（内存操作，0ms）
        if not os.path.exists(CONFIG_FILE):
            return DEFAULT_CONFIG.copy()

        # 2. 如果文件存在，尝试读取
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

                # 3. 合并逻辑：防止旧配置文件缺少新字段
                # 如果 config.json 里缺了某个 key，就用默认值补上
                for key, value in DEFAULT_CONFIG.items():
                    if key not in data:
                        data[key] = value
                return data
        except Exception as e:
            print(f"Config load error: {e}")
            # 如果文件坏了，降级回默认配置，不崩
            return DEFAULT_CONFIG.copy()

    def save_config(self, new_config):
        # 4. 只有用户点击保存时，才真正写入硬盘
        self.config = new_config
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(new_config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Config save error: {e}")

    def get(self, key):
        return self.config.get(key, DEFAULT_CONFIG.get(key))