import json
import os

CONFIG_FILE = "config.json"

# ✅ 1. 更新默认配置结构，适配新的 JSON 格式
DEFAULT_CONFIG = {
    "api_key": "",  # 默认留空，让用户自己填
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "model": "ep-",
    # 根据你的要求设置默认快捷键
    "hotkey_grammar": "F9",  # 语法分析默认 F9
    "hotkey_translate": "Ctrl+T",  # 翻译默认 Ctrl+T
    "close_to_tray": False  # 默认点击关闭直接退出，而不是最小化
}


class ConfigManager:
    def __init__(self):
        self.config = self.load_config()

    def load_config(self):
        """加载配置，如果文件不存在或缺项，自动补全默认值"""
        if not os.path.exists(CONFIG_FILE):
            # 如果文件完全不存在，直接保存并返回默认配置
            self.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

                # ✅ 2. 关键逻辑：合并默认配置
                # 如果 config.json 里缺了新功能的字段（比如老用户升级上来），这里会自动补上
                is_updated = False
                for key, value in DEFAULT_CONFIG.items():
                    if key not in data:
                        data[key] = value
                        is_updated = True

                # 如果发现缺项并补全了，顺手把文件也更新一下，防止下次还缺
                if is_updated:
                    self.save_config(data)

                return data
        except Exception as e:
            print(f"配置文件读取出错: {e}, 已重置为默认配置")
            return DEFAULT_CONFIG.copy()

    def save_config(self, new_config):
        """保存配置到文件"""
        self.config = new_config
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(new_config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"配置保存失败: {e}")

    def get(self, key):
        """获取配置项，如果获取不到则返回默认值"""
        return self.config.get(key, DEFAULT_CONFIG.get(key))