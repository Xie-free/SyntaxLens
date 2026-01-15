from PyQt6.QtCore import QThread, pyqtSignal
from openai import OpenAI

class AIWorker(QThread):
    finished_signal = pyqtSignal(str)

    def __init__(self, text, config_manager, task_type="grammar"):
        super().__init__()
        self.text = text
        self.cfg = config_manager
        self.task_type = task_type # 'grammar' 或 'translate'

    def run(self):
        api_key = self.cfg.get("api_key")
        base_url = self.cfg.get("base_url")
        model = self.cfg.get("model")

        # 1. 语法分析 Prompt
        prompt_grammar = """
        你是一个英语语法专家。请严格按照以下 HTML 格式返回（不要Markdown）：
        <h3 style='color: #00C853; margin:0;'>✅ 语法分析</h3>
        <p><b>结构：</b> [分析句子成分]</p>
        <hr style='border: 1px dashed #555;'>
        <h3 style='color: #FF9800; margin:0;'>⚠️ 诊断与修改</h3>
        <p><b>错误：</b> [指出错误，无则写无]</p>
        <p><b>建议：</b> <span style='color: #FFD600;'>[修改后的句子]</span></p>
        <p><b>解释：</b> [简短解释]</p>
        """

        # 2. 翻译 Prompt
        prompt_translate = """
        你是一个资深中英翻译家。
        1. 若输入英文，翻译成地道中文；若输入中文，翻译成地道英文。
        2. 请严格按照以下 HTML 格式返回（不要Markdown）：
        <h3 style='color: #2196F3; margin:0;'>🔤 翻译结果</h3>
        <p style='font-size: 16px; font-weight: bold;'>[翻译内容]</p>
        <hr style='border: 1px dashed #555;'>
        <p style='color: #aaa; font-size: 13px;'>📝 <b>备注：</b> [生僻词或背景知识]</p>
        """

        # 根据任务类型选择提示词
        system_content = prompt_translate if self.task_type == "translate" else prompt_grammar

        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": self.text}
                ],
                temperature=0.3
            )
            self.finished_signal.emit(response.choices[0].message.content)
        except Exception as e:
            self.finished_signal.emit(f"<span style='color:red'>API Error: {str(e)}</span>")