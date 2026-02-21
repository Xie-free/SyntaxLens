import sys
import os
import time
import ctypes
import queue
import threading
import pyperclip

# 1. 强制软件渲染
os.environ["QT_OPENGL"] = "software"

# GUI 相关 (必须保留 QLockFile, QDir, Qt)
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer, QLockFile, QDir, Qt, QThread, pyqtSignal
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtGui import QIcon

import keyboard

from core.hardware import hard_click, hard_press, hard_release, DIK_HOME, DIK_END, DIK_LSHIFT, DIK_LCONTROL, DIK_C, DIK_INSERT, DIK_RIGHT
from ui.main_window import MainWindow
from ui.popup import PopupResult

# 引入跨线程安全的信号机制
from PyQt6.QtCore import QObject

class HotkeySignals(QObject):
    triggered = pyqtSignal(str)

hotkey_signals = HotkeySignals()

IPC_SERVER_NAME = "SyntaxLens_IPC_Server_v002"


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def hotkey_daemon(grammar_key, translate_key):
    def on_grammar():
        hotkey_signals.triggered.emit("grammar")

    def on_translate():
        hotkey_signals.triggered.emit("translate")

    try:
        try:
            keyboard.unhook_all_hotkeys()
        except:
            pass
        keyboard.add_hotkey(grammar_key, on_grammar)
        keyboard.add_hotkey(translate_key, on_translate)
        keyboard.wait()
    except Exception as e:
        print(f"Hotkey Error: {e}")


# === 🚀 核心重构：工作流线程 (复制 + AI) ===
# 这个线程负责所有的脏活累活，确保 UI 线程丝滑流畅
class WorkflowThread(QThread):
    stream_update = pyqtSignal(str)  # 发送 HTML 片段
    finished_signal = pyqtSignal()  # 任务结束
    error_signal = pyqtSignal(str)  # 报错
    log_signal = pyqtSignal(str)  # 日志

    def __init__(self, config_manager, task_type):
        super().__init__()
        self.cfg = config_manager
        self.task_type = task_type  # "grammar" 或 "translate"
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            # 1. 获取对应的提示词 (支持用户自定义)
            if self.task_type == "grammar":
                system_prompt = self.cfg.get("prompt_grammar")
            else:
                system_prompt = self.cfg.get("prompt_translate")

            # 2. 执行取词 (后台执行，不卡UI)
            text = self.perform_copy_sequence()
            if not text:
                self.error_signal.emit("未选中内容，请重试")
                return

            self.log_signal.emit(f"✅ 获取文本: {text[:15]}...")

            # 3. 延迟加载 AI 库
            import markdown2
            from openai import OpenAI

            # 4. 准备 API
            api_key = self.cfg.get("api_key")
            base_url = self.cfg.get("base_url")
            model = self.cfg.get("model")

            # 拼接 user 内容
            user_content = f"待分析数据：\n```text\n{text}\n```"

            client = OpenAI(api_key=api_key, base_url=base_url)

            # 5. 发起请求
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                stream=True,
                timeout=20
            )

            collected_text = ""
            # 深色模式 CSS
            # 深色模式 CSS (优化版：强制换行)
            css = """
                        <style>
                            body { 
                                color: #d4d4d4; 
                                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; 
                                font-size: 14px; 
                                line-height: 1.6;
                                word-wrap: break-word; /* 关键：允许长单词换行 */
                            }
                            h1, h2, h3 { color: #569cd6; margin-top: 10px; }
                            strong { color: #dcdcaa; }
                            /* 代码块样式优化 */
                            code { 
                                background-color: #2d2d2d; 
                                padding: 2px 5px; 
                                border-radius: 4px; 
                                color: #ce9178; 
                                font-family: Consolas, monospace;
                            }
                            pre {
                                background-color: #1e1e1e;
                                border: 1px solid #333;
                                padding: 10px;
                                border-radius: 5px;
                                white-space: pre-wrap; /* 关键：强制代码块自动换行，不许出现横向滚动条 */
                                word-wrap: break-word;
                            }
                            pre code {
                                background-color: transparent;
                                border: none;
                                color: #9cdcfe;
                                padding: 0;
                            }
                            blockquote { 
                                border-left: 4px solid #569cd6; 
                                margin: 10px 0; 
                                padding-left: 10px; 
                                color: #808080; 
                                background-color: #252526; 
                            }
                        </style>
                        """
            # 6. 流式处理
            for chunk in response:
                if self.isInterruptionRequested() or self._is_cancelled: break
                content = chunk.choices[0].delta.content
                if content:
                    collected_text += content
                    html = markdown2.markdown(collected_text, extras=["break-on-newline", "fenced-code-blocks"])
                    self.stream_update.emit(css + html)

            # 最后发一次确保完整
            if not self._is_cancelled:
                html = markdown2.markdown(collected_text, extras=["break-on-newline", "fenced-code-blocks"])
                self.stream_update.emit(css + html)

            # 💡 检查是否需要自动复制纠错后的句子
            if not self._is_cancelled and self.task_type == "grammar" and self.cfg.get("auto_copy_grammar"):
                import re
                self.log_signal.emit("正在提取纠错后的句子...")
                match = re.search(r'<fixed>(.*?)</fixed>', collected_text, re.DOTALL)
                if match:
                    fixed_text = match.group(1).strip()
                    if fixed_text:
                        import pyperclip
                        pyperclip.copy(fixed_text)
                        self.log_signal.emit(f"✅ 已复制纠错后的句子: {fixed_text[:15]}...")

        except Exception as e:
            self.error_signal.emit(f"错误: {str(e)}")
        finally:
            self.finished_signal.emit()

    def perform_copy_sequence(self):
        try:
            original_clipboard = pyperclip.paste()
        except Exception:
            original_clipboard = ""

        def wait_for_clipboard(timeout_ms=500, interval_ms=20):
            start = time.time()
            timeout_sec = timeout_ms / 1000.0
            interval_sec = interval_ms / 1000.0
            while time.time() - start < timeout_sec:
                text = pyperclip.paste()
                if text.strip(): return text.strip()
                time.sleep(interval_sec)
            return None

        # 定义按键常量，方便下面调用
        try:
            time.sleep(0.05)  # 稍微缩短初始等待

            # 清空剪贴板
            pyperclip.copy("")

            # === 方案 A: 强力复制 (Ctrl + Insert) ===
            # 针对 PyCharm/IdeaVim 优化
            self.log_signal.emit("⚡ 尝试强力复制 (Ctrl+Insert)...")

            hard_press(DIK_LCONTROL)
            time.sleep(0.05)
            hard_press(DIK_INSERT)
            time.sleep(0.05)
            hard_release(DIK_INSERT)
            time.sleep(0.02)
            hard_release(DIK_LCONTROL)

            # 检查 A (动态等待最多400ms)
            text = wait_for_clipboard(400)
            if text: return text

            # === 方案 B: 标准复制 (Ctrl + C) ===
            self.log_signal.emit("🔄 尝试标准复制 (Ctrl+C)...")

            hard_press(DIK_LCONTROL)
            time.sleep(0.03)
            hard_press(DIK_C)
            time.sleep(0.03)
            hard_release(DIK_C)
            time.sleep(0.02)
            hard_release(DIK_LCONTROL)

            # 检查 B (动态等待最多400ms)
            text = wait_for_clipboard(400)
            if text: return text

            # === 方案 C: 自动全选兜底 (Home -> Shift+End) ===
            self.log_signal.emit("⚠️ 未选中，尝试自动全选...")

            # Home
            hard_press(DIK_HOME)
            time.sleep(0.03)
            hard_release(DIK_HOME)
            time.sleep(0.03)

            # Shift + End
            hard_press(DIK_LSHIFT)
            time.sleep(0.03)
            hard_press(DIK_END)
            time.sleep(0.03)
            hard_release(DIK_END)
            time.sleep(0.03)
            hard_release(DIK_LSHIFT)  # 这里必须先释放 Shift
            time.sleep(0.05)

            # 全选后再 Ctrl + C
            hard_press(DIK_LCONTROL)
            time.sleep(0.03)
            hard_press(DIK_C)
            time.sleep(0.03)
            hard_release(DIK_C)
            time.sleep(0.02)
            hard_release(DIK_LCONTROL)

            # 检查 C (动态等待最多600ms)
            text = wait_for_clipboard(600)
            if text: return text

            return None

        except Exception as e:
            self.log_signal.emit(f"❌ 取词错误: {e}")
            return None

        finally:
            # === 🛡️ 绝对防御 (兜底释放) ===
            # 无论上面发生了什么（报错、return、断电），这里都会执行
            # 确保按键一定被松开！
            hard_release(DIK_LCONTROL)
            hard_release(DIK_LSHIFT)
            hard_release(DIK_INSERT)
            hard_release(DIK_C)
            
            # ⚠️ 恢复剪贴板原始内容
            try:
                pyperclip.copy(original_clipboard)
            except Exception as e:
                self.log_signal.emit(f"⚠️ 恢复剪贴板失败: {e}")


# --- 主程序逻辑 ---
class SyntaxLensApp(MainWindow):
    def __init__(self, config_manager):
        super().__init__(config_manager)
        self.popup = PopupResult()
        
        # 绑定弹窗关闭信号，用于中断 AI 请求
        self.popup.closed_signal.connect(self.cancel_current_task)

        self.worker = None  # 现在用新的 WorkflowThread
        self.is_processing = False

        self.append_log("✅ 系统就绪")

        # 绑定热键触发信号到处理函数
        hotkey_signals.triggered.connect(self.start_task_flow)

        threading.Thread(target=hotkey_daemon,
                         args=(self.cfg.get("hotkey_grammar"), self.cfg.get("hotkey_translate")),
                         daemon=True).start()

        threading.Thread(target=self.preload_heavy_libs, daemon=True).start()
        self.init_ipc_server()

    def init_ipc_server(self):
        QLocalServer.removeServer(IPC_SERVER_NAME)
        self.ipc_server = QLocalServer()
        self.ipc_server.newConnection.connect(self.handle_new_connection)
        self.ipc_server.listen(IPC_SERVER_NAME)

    def handle_new_connection(self):
        socket = self.ipc_server.nextPendingConnection()
        socket.readyRead.connect(lambda: self.read_socket_data(socket))

    def read_socket_data(self, socket):
        if socket.readAll().data().decode() == "SHOW":
            self.force_show_window()

    def force_show_window(self):
        self.showNormal()
        self.show()
        # self.raise_()
        # self.activateWindow()

    def preload_heavy_libs(self):
        try:
            import markdown2; from openai import OpenAI
        except:
            pass

    def start_task_flow(self, task_type):
        if self.is_recording_mode(): return
        if self.is_processing: return

        self.is_processing = True

        # 显示 "正在分析..."
        # 注意：这里我们立即显示弹窗，但文字显示 "正在获取文本..."
        self.popup.show_loading("准备中...")

        # 创建并启动后台线程
        self.worker = WorkflowThread(self.cfg, task_type)
        self.worker.stream_update.connect(lambda html: self.popup.update_stream_content(html, False))
        self.worker.log_signal.connect(self.append_log)
        self.worker.error_signal.connect(self.handle_error)
        self.worker.finished_signal.connect(self.reset_state)

        self.worker.start()

    def cancel_current_task(self):
        if self.worker and self.worker.isRunning():
            self.append_log("🛑 用户关闭弹窗，已中断当前 AI 请求")
            self.worker.cancel()
            self.worker.requestInterruption()
            self.reset_state()

    def handle_error(self, msg):
        self.append_log(f"❌ {msg}")
        self.popup.show_message(f"⚠️ {msg}")
        # error 也会触发 finished -> reset_state，所以这里不用手动 reset

    def reset_state(self):
        self.is_processing = False
        # 任务结束，Worker 线程会自动销毁


def main():
    try:
        myappid = 'mycompany.syntaxlens.pro.v002'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        pass

    try:
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)

        icon_path = resource_path("app.ico")
        if os.path.exists(icon_path): app.setWindowIcon(QIcon(icon_path))

        socket = QLocalSocket()
        socket.connectToServer(IPC_SERVER_NAME)
        if socket.waitForConnected(500):
            socket.write(b"SHOW")
            socket.flush()
            socket.waitForBytesWritten(1000)
            return

        from core.config import ConfigManager
        cfg = ConfigManager()
        win = SyntaxLensApp(cfg)

        is_silent = "--silent" in sys.argv
        has_key = bool(cfg.get("api_key"))

        if not has_key:
            win.force_show_window()
        elif is_silent:
            win.tray_icon.showMessage("SyntaxLens", "已在后台静默运行", QSystemTrayIcon.MessageIcon.Information, 2000)
        else:
            win.force_show_window()

        sys.exit(app.exec())
    except Exception as e:
        ctypes.windll.user32.MessageBoxW(0, str(e), "Fatal Error", 0x10)


if __name__ == "__main__":
    main()