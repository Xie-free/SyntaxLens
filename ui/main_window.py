import sys
import os
import winreg  # <--- ✅ 新增：用于操作注册表
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QGroupBox,
                             QFormLayout, QTextEdit, QSystemTrayIcon, QMenu,
                             QMessageBox, QApplication, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QAction


class MainWindow(QMainWindow):
    config_updated = pyqtSignal(dict)

    def __init__(self, config_manager):
        super().__init__()
        self.cfg = config_manager
        self.setWindowTitle("SyntaxLens - 智能屏幕取词助手")
        self.resize(500, 520)  # 稍微把高度加大一点

        self.is_running = True

        self.init_ui()
        self.load_config_to_ui()
        self.init_tray()

        # ✅ 启动时检查注册表，同步“开机自启”勾选框的状态
        self.check_autostart_status()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 1. 顶部状态
        self.status_indicator = QLabel("🟢 服务运行中")
        self.status_indicator.setStyleSheet("color: green; font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        self.status_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_indicator)

        # 1.任务栏图标设置
        icon_path = resource_path("app.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        # 2. 配置区域
        # ... API 设置 ...

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
        main_layout.addWidget(group_api)

        # ... 快捷键设置 ...
        group_hotkey = QGroupBox("⌨️ 快捷键设置")
        form_hotkey = QFormLayout()
        self.input_hk_gram = QLineEdit()
        self.input_hk_trans = QLineEdit()
        form_hotkey.addRow("语法分析:", self.input_hk_gram)
        form_hotkey.addRow("中英翻译:", self.input_hk_trans)
        group_hotkey.setLayout(form_hotkey)
        main_layout.addWidget(group_hotkey)

        # 3. 系统选项 (✅ 修改部分)
        # 用一个 VBoxLayout 把两个勾选框放一起
        opts_layout = QVBoxLayout()
        opts_layout.setSpacing(5)  # 间距小一点

        # 选项 1: 最小化到托盘
        self.chk_close_to_tray = QCheckBox("点击关闭按钮时，最小化到系统托盘 (后台运行)")

        # 选项 2: 开机自启 (✅ 新增)
        self.chk_auto_start = QCheckBox("开机自动启动 SyntaxLens")

        opts_layout.addWidget(self.chk_close_to_tray)
        opts_layout.addWidget(self.chk_auto_start)
        main_layout.addLayout(opts_layout)

        # 4. 按钮
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("💾 保存配置")
        self.btn_save.clicked.connect(self.save_config)
        self.btn_save.setMinimumHeight(40)
        self.btn_save.setStyleSheet("background-color: #007AFF; color: white; font-weight: bold; border-radius: 5px;")

        self.btn_toggle = QPushButton("⏸️ 暂停服务")
        self.btn_toggle.clicked.connect(self.toggle_listening)
        self.btn_toggle.setMinimumHeight(40)

        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_toggle)
        main_layout.addLayout(btn_layout)

        main_layout.addStretch()

        # 5. 日志
        log_label = QLabel("📋 状态日志:")
        log_label.setStyleSheet("color: #666; font-size: 12px; margin-top: 10px;")
        main_layout.addWidget(log_label)

        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setMaximumHeight(80)
        self.log_console.setStyleSheet(
            "background-color: #f0f0f0; color: #333; font-family: Consolas; font-size: 12px; border: 1px solid #ccc;")
        main_layout.addWidget(self.log_console)

    # ... (init_tray, load_config_to_ui 等保持不变) ...
    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)


        icon_path = resource_path("app.ico")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            from PyQt6.QtWidgets import QStyle
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))

        tray_menu = QMenu()
        show_action = QAction("显示主界面", self)
        show_action.triggered.connect(self.show_window)
        quit_action = QAction("退出程序", self)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.on_tray_activated)

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()

    def show_window(self):
        self.show()
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
        self.append_log("配置已加载。")

    def save_config(self):
        # 1. 保存普通配置
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

        # 2. ✅ 应用开机自启设置
        self.apply_autostart_setting()

    # --- ✅ 核心功能：检查注册表状态 ---
    def check_autostart_status(self):
        """检查当前是否已经设置了开机自启"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run",
                                 0, winreg.KEY_READ)
            try:
                # 尝试获取 SyntaxLens 的值
                winreg.QueryValueEx(key, "SyntaxLens")
                # 如果没报错，说明已设置，勾选框打勾
                self.chk_auto_start.setChecked(True)
            except FileNotFoundError:
                # 没找到，说明没设置
                self.chk_auto_start.setChecked(False)
            winreg.CloseKey(key)
        except Exception as e:
            self.append_log(f"读取注册表失败: {e}")

    # --- ✅ 核心功能：写入/删除注册表 ---
    def apply_autostart_setting(self):
        """根据勾选框状态，修改注册表"""
        app_name = "SyntaxLens"
        # 获取当前运行的 exe 路径
        exe_path = sys.executable

        # 注意：如果是脚本运行(python main.py)，sys.executable 是 python.exe
        # 如果是打包后运行，sys.executable 是 SyntaxLens.exe

        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run",
                                 0, winreg.KEY_ALL_ACCESS)

            if self.chk_auto_start.isChecked():
                # 写入注册表
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{exe_path}"')
                self.append_log("✅ 开机自启：已启用")
            else:
                # 删除注册表
                try:
                    winreg.DeleteValue(key, app_name)
                    self.append_log("✅ 开机自启：已关闭")
                except FileNotFoundError:
                    pass  # 本来就没设置，忽略

            winreg.CloseKey(key)
        except Exception as e:
            self.append_log(f"❌ 设置开机自启失败: {e}")
            QMessageBox.warning(self, "权限错误", "无法修改注册表，请尝试以管理员身份运行程序。")

    # ... (toggle_listening, append_log, closeEvent 保持不变) ...
    def toggle_listening(self):
        self.is_running = not self.is_running
        if self.is_running:
            self.status_indicator.setText("🟢 服务运行中")
            self.status_indicator.setStyleSheet(
                "color: green; font-weight: bold; font-size: 16px; margin-bottom: 10px;")
            self.btn_toggle.setText("⏸️ 暂停服务")
            self.append_log("服务已恢复。")
        else:
            self.status_indicator.setText("🔴 服务已暂停")
            self.status_indicator.setStyleSheet("color: red; font-weight: bold; font-size: 16px; margin-bottom: 10px;")
            self.btn_toggle.setText("▶️ 开启服务")
            self.append_log("服务已暂停。")

    def append_log(self, text):
        self.log_console.append(text)
        scrollbar = self.log_console.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def closeEvent(self, event):
        if self.chk_close_to_tray.isChecked():
            event.ignore()
            self.hide()
            self.tray_icon.showMessage("SyntaxLens", "程序已最小化到托盘运行", QSystemTrayIcon.MessageIcon.Information,
                                       2000)
        else:
            event.accept()
            QApplication.instance().quit()

        # 资源路径处理
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)