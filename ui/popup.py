from PyQt6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout,
                             QGraphicsDropShadowEffect, QFrame, QPushButton, QApplication)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QCursor


class PopupResult(QWidget):
    def __init__(self):
        super().__init__()
        # 窗口属性：无边框、置顶、工具窗口(不显示在任务栏)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowStaysOnTopHint |
                            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 拖拽变量
        self.m_Position = None
        self.is_pressed = False

        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        # 背景容器
        self.container = QFrame()
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            #container {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 12px;
            }
            QLabel {
                color: #e0e0e0;
                font-family: 'Microsoft YaHei', sans-serif;
                font-size: 14px;
            }
        """)

        # 阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)
        self.main_layout.addWidget(self.container)

        # 内部布局
        content_layout = QVBoxLayout(self.container)

        # 标题栏
        header_layout = QHBoxLayout()
        self.title_label = QLabel("🤖 SyntaxLens")
        self.title_label.setStyleSheet("font-weight: bold; color: #888; font-size: 12px;")

        self.btn_close = QPushButton("×")
        self.btn_close.setFixedSize(24, 24)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(self.hide)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #888;
                border: none;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #ff5f57;
            }
        """)

        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_close)

        # 内容区域
        self.content_label = QLabel("等待指令...")
        self.content_label.setWordWrap(True)
        self.content_label.setTextFormat(Qt.TextFormat.RichText)
        self.content_label.setMinimumWidth(280)
        self.content_label.setMaximumWidth(450)

        content_layout.addLayout(header_layout)
        content_layout.addWidget(self.content_label)

    def show_loading(self, task_name="分析中"):  # ✅ 关键修改在这里
        self.content_label.setText(f"🚀 正在{task_name}...<br><span style='font-size:12px;color:#888'>AI Thinking...</span>")
        self.resize(10, 10)
        self.adjustSize()
        self.move_to_mouse()
        self.show()
        self.raise_()


    def show_message(self, text):
        self.content_label.setText(text)
        self.adjustSize()
        self.show()
        self.raise_()

    def move_to_mouse(self):
        """移动窗口到鼠标附近"""
        cursor_pos = QCursor.pos()
        screen = QApplication.primaryScreen().geometry()

        x = cursor_pos.x() + 20
        y = cursor_pos.y() + 20

        # 防止超出屏幕右边界
        if x + self.width() > screen.width():
            x = screen.width() - self.width() - 20
        # 防止超出屏幕下边界
        if y + self.height() > screen.height():
            y = screen.height() - self.height() - 20

        self.move(x, y)

    # --- 鼠标拖拽逻辑 ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_pressed = True
            self.m_Position = event.globalPosition().toPoint() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.is_pressed and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.m_Position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.is_pressed = False

    # --- Esc 键关闭 ---
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()