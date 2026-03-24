import sys
import os
import subprocess
import winreg
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QGroupBox,
                             QFormLayout, QTextEdit, QSystemTrayIcon, QMenu,
                             QApplication, QCheckBox, QMessageBox, QTabWidget, QPlainTextEdit)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QIcon, QAction, QKeyEvent, QKeySequence, QDesktopServices


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


class HotKeyLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("点击录制...")
        self.setReadOnly(True)
        self.setStyleSheet("""
            QLineEdit { border: 1px solid #ccc; border-radius: 4px; padding: 5px; background: white; color: #333; }
            QLineEdit:focus { border: 2px solid #007AFF; background: #eef6ff; }
        """)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta): return
        if key == Qt.Key.Key_Backspace or key == Qt.Key.Key_Delete:
            self.clear();
            return

        modifiers = event.modifiers()
        key_parts = []
        if modifiers & Qt.KeyboardModifier.ControlModifier: key_parts.append("ctrl")
        if modifiers & Qt.KeyboardModifier.AltModifier:     key_parts.append("alt")
        if modifiers & Qt.KeyboardModifier.ShiftModifier:   key_parts.append("shift")
        if modifiers & Qt.KeyboardModifier.MetaModifier:    key_parts.append("win")
        key_text = QKeySequence(key).toString().lower()
        if key_text: key_parts.append(key_text)
        self.setText("+".join(key_parts))


class MainWindow(QMainWindow):
    config_updated = pyqtSignal(dict)

    def __init__(self, config_manager):
        super().__init__()
        self.cfg = config_manager
        self.setWindowTitle("SyntaxLens v0.2.0 - 设置")
        self.resize(550, 600)  # 稍微加大一点

        self.force_quit = False
        self.icon_path = resource_path("app.ico")
        if os.path.exists(self.icon_path):
            self.setWindowIcon(QIcon(self.icon_path))

        self.init_ui()
        self.load_config_to_ui()
        self.init_tray()
        self.check_autostart_status()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)

        # 状态栏
        self.status_indicator = QLabel("🟢 服务运行中")
        self.status_indicator.setStyleSheet("color: green; font-weight: bold; font-size: 16px;")
        self.status_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_indicator)

        # === 引入选项卡 ===
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # --- Tab 1: 基础设置 ---
        tab_basic = QWidget()
        layout_basic = QVBoxLayout(tab_basic)

        # AI 配置
        group_api = QGroupBox("🤖 AI 模型配置")
        form_api = QFormLayout()
        self.input_api_key = QLineEdit()
        self.input_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_model = QLineEdit()
        self.input_url = QLineEdit()
        form_api.addRow("API Key:", self.input_api_key)
        form_api.addRow("Model ID:", self.input_model)
        form_api.addRow("Base URL:", self.input_url)
        group_api.setLayout(form_api)
        layout_basic.addWidget(group_api)

        # 快捷键
        group_hotkey = QGroupBox("⌨️ 快捷键设置")
        form_hotkey = QFormLayout()
        self.input_hk_gram = HotKeyLineEdit()
        self.input_hk_trans = HotKeyLineEdit()
        form_hotkey.addRow("功能 A (默认语法):", self.input_hk_gram)
        form_hotkey.addRow("功能 B (默认翻译):", self.input_hk_trans)
        group_hotkey.setLayout(form_hotkey)
        layout_basic.addWidget(group_hotkey)

        # 系统选项
        group_sys = QGroupBox("⚙️ 系统选项")
        opts_layout = QVBoxLayout()
        self.chk_close_to_tray = QCheckBox("点击关闭时最小化到托盘")
        self.chk_auto_start = QCheckBox("开机自动启动")
        self.chk_auto_copy = QCheckBox("语法纠错后自动将正确句子复制到剪贴板")
        opts_layout.addWidget(self.chk_close_to_tray)
        opts_layout.addWidget(self.chk_auto_start)
        opts_layout.addWidget(self.chk_auto_copy)
        group_sys.setLayout(opts_layout)
        layout_basic.addWidget(group_sys)

        layout_basic.addStretch()
        self.tabs.addTab(tab_basic, "基础设置")

        # --- Tab 2: 提示词设置 (Custom Prompts) ---
        tab_prompts = QWidget()
        layout_prompts = QVBoxLayout(tab_prompts)

        layout_prompts.addWidget(QLabel("在这里定义 AI 的人设和任务。你可以把它们改成解释代码、润色文章等。"))

        # 功能 A 提示词
        layout_prompts.addWidget(QLabel("📝 <b>功能 A 提示词</b> (对应上方快捷键 A):"))
        self.input_prompt_gram = QPlainTextEdit()
        self.input_prompt_gram.setPlaceholderText("输入系统提示词...")
        layout_prompts.addWidget(self.input_prompt_gram)

        # 功能 B 提示词
        layout_prompts.addWidget(QLabel("📝 <b>功能 B 提示词</b> (对应上方快捷键 B):"))
        self.input_prompt_trans = QPlainTextEdit()
        self.input_prompt_trans.setPlaceholderText("输入系统提示词...")
        layout_prompts.addWidget(self.input_prompt_trans)

        self.tabs.addTab(tab_prompts, "AI 指令定制")

        # 底部按钮
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("💾 保存并应用")
        self.btn_save.clicked.connect(self.save_config)
        self.btn_save.setMinimumHeight(35)
        self.btn_save.setStyleSheet("background-color: #007AFF; color: white; font-weight: bold; border-radius: 4px;")

        self.btn_toggle_log = QPushButton("📜 日志")
        self.btn_toggle_log.setCheckable(True)
        self.btn_toggle_log.setMinimumHeight(35)
        self.btn_toggle_log.clicked.connect(self.toggle_log_console)

        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_toggle_log)
        main_layout.addLayout(btn_layout)

        # 日志
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setVisible(False)
        self.log_console.setStyleSheet(
            "background-color: #f8f8f8; color: #555; font-family: Consolas; font-size: 11px;")
        self.log_console.setMaximumHeight(100)
        main_layout.addWidget(self.log_console)

    def is_recording_mode(self):
        if self.isVisible() and (self.input_hk_gram.hasFocus() or self.input_hk_trans.hasFocus()):
            return True
        return False

    def toggle_log_console(self):
        self.log_console.setVisible(self.btn_toggle_log.isChecked())

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        if os.path.exists(self.icon_path):
            self.tray_icon.setIcon(QIcon(self.icon_path))
        else:
            from PyQt6.QtWidgets import QStyle
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        tray_menu = QMenu()
        tray_menu.addAction("设置", self.show_window)
        tray_menu.addAction("项目主页",
                            lambda: QDesktopServices.openUrl(QUrl("https://github.com/Xie-free/SyntaxLens")))
        tray_menu.addSeparator()
        tray_menu.addAction("退出", self.quit_app)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.on_tray_activated)

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()

    def show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def quit_app(self):
        self.force_quit = True
        QApplication.instance().quit()

    def load_config_to_ui(self):
        self.input_api_key.setText(self.cfg.get("api_key"))
        self.input_model.setText(self.cfg.get("model"))
        self.input_url.setText(self.cfg.get("base_url"))
        self.input_hk_gram.setText(self.cfg.get("hotkey_grammar"))
        self.input_hk_trans.setText(self.cfg.get("hotkey_translate"))
        self.chk_close_to_tray.setChecked(bool(self.cfg.get("close_to_tray")))
        self.chk_auto_copy.setChecked(bool(self.cfg.get("auto_copy_grammar")))
        # 加载提示词
        self.input_prompt_gram.setPlainText(self.cfg.get("prompt_grammar"))
        self.input_prompt_trans.setPlainText(self.cfg.get("prompt_translate"))
        self.append_log("配置已加载")

    def save_config(self):
        new_conf = {
            "api_key": self.input_api_key.text().strip(),
            "model": self.input_model.text().strip(),
            "base_url": self.input_url.text().strip(),
            "hotkey_grammar": self.input_hk_gram.text().strip(),
            "hotkey_translate": self.input_hk_trans.text().strip(),
            "close_to_tray": self.chk_close_to_tray.isChecked(),
            "auto_copy_grammar": self.chk_auto_copy.isChecked(),
            # 保存提示词
            "prompt_grammar": self.input_prompt_gram.toPlainText().strip(),
            "prompt_translate": self.input_prompt_trans.toPlainText().strip()
        }
        self.cfg.save_config(new_conf)
        self.config_updated.emit(new_conf)
        self.apply_autostart_setting()
        self.append_log("✅ 配置已保存")
        QMessageBox.information(self, "提示", "配置已保存！\n\n所有更改已立即生效。")
        self.btn_save.setFocus()

    def append_log(self, text):
        self.log_console.append(text)

    def get_startup_shortcut_path(self):
        startup_dir = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")
        return os.path.join(startup_dir, "SyntaxLens.lnk")

    def check_autostart_status(self):
        lnk_path = self.get_startup_shortcut_path()
        if os.path.exists(lnk_path):
            self.chk_auto_start.setChecked(True)
        else:
            self.chk_auto_start.setChecked(False)

    def apply_autostart_setting(self):
        lnk_path = self.get_startup_shortcut_path()
        try:
            if self.chk_auto_start.isChecked():
                # 创建快捷方式 (使用 VBScript 以免引入 pywin32)
                exe_path = sys.executable
                work_dir = os.path.dirname(exe_path)
                
                vbs_code = f'''
Set ws = CreateObject("WScript.Shell")
Set shortcut = ws.CreateShortcut("{lnk_path}")
shortcut.TargetPath = "{exe_path}"
shortcut.Arguments = "--silent"
shortcut.WorkingDirectory = "{work_dir}"
shortcut.WindowStyle = 1
shortcut.Description = "SyntaxLens Autostart"
shortcut.Save
'''
                vbs_path = os.path.join(os.environ["TEMP"], "create_shortcut.vbs")
                with open(vbs_path, "w", encoding="gbk") as f:
                    f.write(vbs_code)
                subprocess.run(
                    ["cscript.exe", "//nologo", vbs_path],
                    check=False,
                    capture_output=True
                )
                try:
                    os.remove(vbs_path)
                except OSError:
                    pass
            else:
                # 删除快捷方式
                if os.path.exists(lnk_path):
                    os.remove(lnk_path)
                    
        except Exception as e:
            self.append_log(f"自启设置失败: {e}")

    def closeEvent(self, event):
        if self.force_quit:
            event.accept()
            return
        if self.chk_close_to_tray.isChecked():
            event.ignore()
            self.hide()
            self.tray_icon.showMessage("SyntaxLens", "已最小化到托盘", QSystemTrayIcon.MessageIcon.Information, 1000)
        else:
            event.accept()
            QApplication.instance().quit()
