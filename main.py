import sys
import time
import keyboard
import pyperclip
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal

# 导入模块
from core.config import ConfigManager
from core.hardware import hard_click, hard_press, hard_release, DIK_HOME, DIK_END, DIK_LSHIFT, DIK_LCONTROL, DIK_C
from core.ai_worker import AIWorker
from ui.popup import PopupResult
from ui.main_window import MainWindow  # 导入新写的主界面


class Bridge(QObject):
    request_start = pyqtSignal(str)  # 启动任务信号
    log_message = pyqtSignal(str)  # 日志信号


class Controller:
    def __init__(self, config_manager, main_window):
        self.cfg = config_manager
        self.ui = main_window  # 持有 UI 对象，用于获取状态

        self.popup = PopupResult()
        self.worker = None
        self.bridge = Bridge()

        # 连接信号
        self.bridge.request_start.connect(self.start_pipeline)
        self.bridge.log_message.connect(self.ui.append_log)  # 把日志打到 UI 上

        # 监听 UI 的配置保存信号
        self.ui.config_updated.connect(self.reload_hotkeys)

        self.is_processing = False
        self.current_hotkeys = []  # 记录当前注册的快捷键，用于清理

        # 初始注册
        self.reload_hotkeys(self.cfg.config)

    def reload_hotkeys(self, new_config):
        """热重载快捷键"""
        # 1. 清除旧的
        try:
            keyboard.unhook_all_hotkeys()
            self.bridge.log_message.emit("♻️ 正在刷新快捷键绑定...")
        except:
            pass

        # 2. 注册新的
        hk_gram = new_config.get("hotkey_grammar")
        hk_trans = new_config.get("hotkey_translate")

        try:
            keyboard.add_hotkey(hk_gram, lambda: self.on_hotkey("grammar"))
            keyboard.add_hotkey(hk_trans, lambda: self.on_hotkey("translate"))
            self.bridge.log_message.emit(f"✅ 快捷键已绑定:\n   语法分析: [{hk_gram}]\n   中英翻译: [{hk_trans}]")
        except Exception as e:
            self.bridge.log_message.emit(f"❌ 快捷键注册失败: {e}")

    def on_hotkey(self, task_type):
        """快捷键入口"""
        # 如果 UI 上点击了暂停，则不处理
        if not self.ui.is_running:
            return

        if not self.is_processing:
            self.bridge.request_start.emit(task_type)

    def start_pipeline(self, task_type):
        self.is_processing = True
        mode_name = "语法分析" if task_type == "grammar" else "中英翻译"
        self.bridge.log_message.emit(f">>> ⚡ 触发任务: {mode_name}")

        try:
            # 1. 等待按键释放
            self.bridge.log_message.emit("⏳ 等待按键释放...")
            while keyboard.is_pressed('ctrl') or keyboard.is_pressed('shift') or keyboard.is_pressed('alt'):
                time.sleep(0.1)
            time.sleep(0.3)

            # 2. 混合取词
            pyperclip.copy("")

            # 尝试直接复制
            hard_press(DIK_LCONTROL)
            time.sleep(0.1)
            hard_click(DIK_C)
            time.sleep(0.1)
            hard_release(DIK_LCONTROL)

            time.sleep(0.1)
            manual_text = pyperclip.paste()
            target_text = ""

            if manual_text.strip():
                self.bridge.log_message.emit(f"✅ 手动选中: {manual_text[:10]}...")
                target_text = manual_text
            else:
                self.bridge.log_message.emit("⚠️ 未选中，执行自动全选...")
                hard_click(DIK_HOME)
                time.sleep(0.1)
                hard_press(DIK_LSHIFT)
                time.sleep(0.2)
                hard_click(DIK_END)
                time.sleep(0.2)
                hard_release(DIK_LSHIFT)
                time.sleep(0.1)

                hard_press(DIK_LCONTROL)
                time.sleep(0.2)
                hard_click(DIK_C)
                time.sleep(0.2)
                hard_release(DIK_LCONTROL)

                for _ in range(5):
                    time.sleep(0.1)
                    target_text = pyperclip.paste()
                    if target_text.strip(): break

            if target_text.strip():
                self.bridge.log_message.emit(f"✅ 获取文本: {target_text[:15]}...")
                self.popup.show_loading(mode_name)

                self.worker = AIWorker(target_text, self.cfg, task_type)
                self.worker.finished_signal.connect(self.handle_ai_result)
                self.worker.start()
            else:
                self.bridge.log_message.emit("❌ 获取文本失败")
                self.popup.show_message("⚠️ <b>获取失败</b>")

        except Exception as e:
            self.bridge.log_message.emit(f"❌ 错误: {e}")
        finally:
            hard_release(DIK_LSHIFT)
            hard_release(DIK_LCONTROL)
            self.is_processing = False

    def handle_ai_result(self, result):
        """处理 AI 返回结果"""
        self.popup.show_message(result)
        self.bridge.log_message.emit("✅ AI 分析完成")


def main():
    app = QApplication(sys.argv)

    # 1. 加载配置
    cfg_mgr = ConfigManager()

    # 2. 创建主窗口
    main_win = MainWindow(cfg_mgr)

    # 3. 创建控制器 (把窗口传进去)
    controller = Controller(cfg_mgr, main_win)

    # 4. 显示主窗口
    main_win.show()

    print("🚀 SyntaxLens UI 已启动")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()