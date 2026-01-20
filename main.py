import sys
import os
import time
import ctypes
import queue
import threading
import pyperclip

# 1. 强制软件渲染
os.environ["QT_OPENGL"] = "software"

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QDir, Qt
# ✅ 引入网络模块，用于进程间通信
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtGui import QIcon

import keyboard

from core.hardware import hard_click, hard_press, hard_release, DIK_HOME, DIK_END, DIK_LSHIFT, DIK_LCONTROL, DIK_C
from core.ai_worker import AIRequestWorker

from ui.main_window import MainWindow
from ui.popup import PopupResult

HOTKEY_QUEUE = queue.Queue()
# 唯一的通信管道名称
IPC_SERVER_NAME = "SyntaxLens_IPC_Server_v002"


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def hotkey_daemon(grammar_key, translate_key):
    def on_grammar():
        HOTKEY_QUEUE.put("grammar")

    def on_translate():
        HOTKEY_QUEUE.put("translate")

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


class SyntaxLensApp(MainWindow):
    def __init__(self, config_manager):
        super().__init__(config_manager)
        self.popup = PopupResult()
        self.ai_worker = None
        self.is_processing = False

        self.poller = QTimer()
        self.poller.timeout.connect(self.check_queue)
        self.poller.start(100)

        self.append_log("✅ 系统就绪")

        threading.Thread(target=hotkey_daemon,
                         args=(self.cfg.get("hotkey_grammar"), self.cfg.get("hotkey_translate")),
                         daemon=True).start()

        threading.Thread(target=self.preload_heavy_libs, daemon=True).start()

        # ✅ 启动 IPC 服务器 (监听唤醒指令)
        self.init_ipc_server()

    # --- 进程通信服务端 ---
    def init_ipc_server(self):
        # 如果残留了旧的 server 文件，先删除
        QLocalServer.removeServer(IPC_SERVER_NAME)

        self.ipc_server = QLocalServer()
        self.ipc_server.newConnection.connect(self.handle_new_connection)
        if self.ipc_server.listen(IPC_SERVER_NAME):
            self.append_log("✅ 唤醒服务已启动")
        else:
            self.append_log("❌ 唤醒服务启动失败")

    def handle_new_connection(self):
        # 收到新连接（说明有人试图再次打开软件）
        socket = self.ipc_server.nextPendingConnection()
        socket.readyRead.connect(lambda: self.read_socket_data(socket))

    def read_socket_data(self, socket):
        data = socket.readAll().data().decode()
        if data == "SHOW":
            # 收到 SHOW 指令，强制把自己置顶显示
            self.force_show_window()

    def force_show_window(self):
        self.showNormal()
        self.show()
        self.raise_()
        self.activateWindow()

    # -----------------------

    def preload_heavy_libs(self):
        try:
            import markdown2
            from openai import OpenAI
        except:
            pass

    def check_queue(self):
        try:
            while not HOTKEY_QUEUE.empty():
                task_type = HOTKEY_QUEUE.get_nowait()
                self.start_task_flow(task_type)
        except:
            pass

    def start_task_flow(self, task_type):
        if self.is_recording_mode():
            self.append_log(f"⚠️ 正在录制快捷键，忽略触发: {task_type}")
            return

        if self.is_processing: return
        self.is_processing = True
        mode = "语法分析" if task_type == "grammar" else "翻译"
        self.append_log(f">>> 触发: {mode}")
        self.perform_copy(task_type)

    def perform_copy(self, task_type):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            pyperclip.copy("")
            hard_press(DIK_LCONTROL)
            time.sleep(0.01)
            hard_click(DIK_C)
            time.sleep(0.01)
            hard_release(DIK_LCONTROL)
            time.sleep(0.02)
            text = pyperclip.paste()

            if not text.strip():
                self.append_log("⚠️ 未选中，尝试全选...")
                hard_click(DIK_HOME)
                time.sleep(0.01)
                hard_press(DIK_LSHIFT)
                time.sleep(0.01)
                hard_click(DIK_END)
                time.sleep(0.01)
                hard_release(DIK_LSHIFT)
                time.sleep(0.01)
                hard_press(DIK_LCONTROL)
                time.sleep(0.01)
                hard_click(DIK_C)
                time.sleep(0.01)
                hard_release(DIK_LCONTROL)
                time.sleep(0.2)
                text = pyperclip.paste()

            if text.strip():
                self.append_log(f"✅ 获取文本: {text[:10]}...")
                self.popup.show_loading(f"正在分析...")
                self.ai_worker = AIRequestWorker(text, self.cfg, task_type)
                self.ai_worker.finished_signal.connect(self.on_ai_finished)
                self.ai_worker.start()
            else:
                self.append_log("❌ 未获取到文本")
                self.popup.show_message("⚠️ 未选中内容")
                self.reset_state()

        except Exception as e:
            self.append_log(f"❌ 错误: {e}")
            self.reset_state()

    def on_ai_finished(self, html):
        self.popup.update_stream_content(html, True)
        self.append_log("✅ 分析完成")
        self.reset_state()

    def reset_state(self):
        self.is_processing = False
        QApplication.restoreOverrideCursor()


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
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))

        # === 🚀 核心修改：检测多开并唤醒旧窗口 ===
        # 尝试连接已存在的服务器
        socket = QLocalSocket()
        socket.connectToServer(IPC_SERVER_NAME)

        if socket.waitForConnected(500):
            # 连接成功！说明已经有一个实例在跑了
            # 发送唤醒指令
            socket.write(b"SHOW")
            socket.flush()
            socket.waitForBytesWritten(1000)
            # 退出当前这个多余的进程
            return

            # === 如果没有连接成功，说明我是第一个，正常启动 ===

        from core.config import ConfigManager
        cfg = ConfigManager()

        win = SyntaxLensApp(cfg)

        # 🚀 启动显示逻辑判断
        # 1. 检查命令行参数是否有 --silent (由注册表开机自启传入)
        is_silent_start = "--silent" in sys.argv

        # 2. 检查是否有 API Key
        has_api_key = bool(cfg.get("api_key"))

        if not has_api_key:
            # 没 Key 必须显示
            win.force_show_window()
        elif is_silent_start:
            # 是开机自启，且有 Key -> 静默启动 (仅托盘)
            # 可以在这里加个气泡提示
            win.tray_icon.showMessage("SyntaxLens", "已在后台静默运行", QSystemTrayIcon.MessageIcon.Information, 2000)
        else:
            # 普通双击启动 -> 显示窗口
            win.force_show_window()

        sys.exit(app.exec())
    except Exception as e:
        ctypes.windll.user32.MessageBoxW(0, str(e), "Fatal Error", 0x10)


if __name__ == "__main__":
    main()