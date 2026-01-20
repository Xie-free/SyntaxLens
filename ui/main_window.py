import sys
import os
import winreg
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QGroupBox,
                             QFormLayout, QTextEdit, QSystemTrayIcon, QMenu,
                             QApplication, QCheckBox, QMessageBox)
from PyQt6.QtGui import QIcon, QAction, QKeyEvent, QKeySequence, QDesktopServices # <--- 新增 QDesktopServices
from PyQt6.QtCore import Qt, pyqtSignal, QUrl # <--- 新增 QUrl




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
        self.setWindowTitle("SyntaxLens v0.2.0 - 智能屏幕助手")
        self.resize(500, 480)

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
        main_layout.setSpacing(15)

        self.status_indicator = QLabel("🟢 服务运行中")
        self.status_indicator.setStyleSheet("color: green; font-weight: bold; font-size: 16px;")
        self.status_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_indicator)

        group_api = QGroupBox("🤖 AI 模型配置")
        form_api = QFormLayout()
        self.input_api_key = QLineEdit()
        self.input_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_api_key.setPlaceholderText("sk-...")
        self.input_model = QLineEdit()
        self.input_url = QLineEdit()
        form_api.addRow("API Key:", self.input_api_key)
        form_api.addRow("Model ID:", self.input_model)
        form_api.addRow("Base URL:", self.input_url)
        group_api.setLayout(form_api)
        main_layout.addWidget(group_api)

        group_hotkey = QGroupBox("⌨️ 快捷键设置 (点击录制)")
        form_hotkey = QFormLayout()
        self.input_hk_gram = HotKeyLineEdit()
        self.input_hk_trans = HotKeyLineEdit()
        form_hotkey.addRow("语法分析:", self.input_hk_gram)
        form_hotkey.addRow("中英翻译:", self.input_hk_trans)
        group_hotkey.setLayout(form_hotkey)
        main_layout.addWidget(group_hotkey)

        group_sys = QGroupBox("⚙️ 系统选项")
        opts_layout = QVBoxLayout()
        self.chk_close_to_tray = QCheckBox("点击关闭时最小化到托盘")
        self.chk_auto_start = QCheckBox("开机自动启动 (后台静默运行)")
        opts_layout.addWidget(self.chk_close_to_tray)
        opts_layout.addWidget(self.chk_auto_start)
        group_sys.setLayout(opts_layout)
        main_layout.addWidget(group_sys)

        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("💾 保存并应用")
        self.btn_save.clicked.connect(self.save_config)
        self.btn_save.setMinimumHeight(35)
        self.btn_save.setStyleSheet("background-color: #007AFF; color: white; font-weight: bold; border-radius: 4px;")
        self.btn_toggle_log = QPushButton("📜 显示日志")
        self.btn_toggle_log.setCheckable(True)
        self.btn_toggle_log.setMinimumHeight(35)
        self.btn_toggle_log.clicked.connect(self.toggle_log_console)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_toggle_log)
        main_layout.addLayout(btn_layout)

        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setPlaceholderText("暂无日志...")
        self.log_console.setStyleSheet(
            "background-color: #f8f8f8; color: #555; font-family: Consolas; font-size: 11px; border: 1px solid #ddd; margin-top:5px;")
        self.log_console.setMaximumHeight(150)
        self.log_console.setVisible(False)
        main_layout.addWidget(self.log_console)
        main_layout.addStretch()

    def is_recording_mode(self):
        if self.isVisible() and (self.input_hk_gram.hasFocus() or self.input_hk_trans.hasFocus()):
            return True
        return False

    def toggle_log_console(self):
        if self.btn_toggle_log.isChecked():
            self.log_console.setVisible(True)
            self.btn_toggle_log.setText("📜 隐藏日志")
            self.resize(self.width(), 580)
        else:
            self.log_console.setVisible(False)
            self.btn_toggle_log.setText("📜 显示日志")
            self.resize(self.width(), 480)

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        if os.path.exists(self.icon_path):
            self.tray_icon.setIcon(QIcon(self.icon_path))
        else:
            from PyQt6.QtWidgets import QStyle
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))

        tray_menu = QMenu()

        # --- 新增：显示主界面 ---
        show_action = QAction("设置", self)
        show_action.triggered.connect(self.show_window)

        # --- 🚀 新增：项目主页/检查更新 ---
        github_action = QAction("项目主页 / 检查更新", self)
        # 请把下面的链接换成你自己的 GitHub 仓库地址
        github_action.triggered.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://github.com/Xie-free/SyntaxLens")))

        # --- 退出 ---
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_app)

        tray_menu.addAction(show_action)
        tray_menu.addAction(github_action)  # 加入菜单
        tray_menu.addSeparator()  # 加个分割线好看点
        tray_menu.addAction(quit_action)

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
        QApplication.instance().quit()

    def load_config_to_ui(self):
        self.input_api_key.setText(self.cfg.get("api_key"))
        self.input_model.setText(self.cfg.get("model"))
        self.input_url.setText(self.cfg.get("base_url"))
        self.input_hk_gram.setText(self.cfg.get("hotkey_grammar"))
        self.input_hk_trans.setText(self.cfg.get("hotkey_translate"))
        self.chk_close_to_tray.setChecked(bool(self.cfg.get("close_to_tray")))
        self.append_log("配置已加载")

    def save_config(self):
        if not self.input_hk_gram.text() or not self.input_hk_trans.text():
            QMessageBox.warning(self, "错误", "快捷键不能为空")
            return
        new_conf = {
            "api_key": self.input_api_key.text().strip(),
            "model": self.input_model.text().strip(),
            "base_url": self.input_url.text().strip(),
            "hotkey_grammar": self.input_hk_gram.text().strip(),
            "hotkey_translate": self.input_hk_trans.text().strip(),
            "close_to_tray": self.chk_close_to_tray.isChecked()
        }
        self.cfg.save_config(new_conf)
        self.config_updated.emit(new_conf)
        self.apply_autostart_setting()
        self.append_log("✅ 配置已保存")
        QMessageBox.information(self, "提示", "配置已保存！\n\n新快捷键已立即生效。")
        self.btn_save.setFocus()

    def append_log(self, text):
        self.log_console.append(text)
        if self.log_console.isVisible():
            scrollbar = self.log_console.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def check_autostart_status(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0,
                                 winreg.KEY_READ)
            winreg.QueryValueEx(key, "SyntaxLens")
            self.chk_auto_start.setChecked(True)
            winreg.CloseKey(key)
        except:
            self.chk_auto_start.setChecked(False)

    def apply_autostart_setting(self):
        exe_path = sys.executable
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0,
                                 winreg.KEY_ALL_ACCESS)
            if self.chk_auto_start.isChecked():
                # ✅ 关键修改：添加 --silent 参数
                # 注意引号的位置： "C:\path\to\exe" --silent
                cmd = f'"{exe_path}" --silent'
                winreg.SetValueEx(key, "SyntaxLens", 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, "SyntaxLens")
                except:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            self.append_log(f"注册表错误: {e}")

    def closeEvent(self, event):
        if self.chk_close_to_tray.isChecked():
            event.ignore()
            self.hide()
            self.tray_icon.showMessage("SyntaxLens", "已最小化到托盘", QSystemTrayIcon.MessageIcon.Information, 1000)
        else:
            event.accept()
            QApplication.instance().quit()