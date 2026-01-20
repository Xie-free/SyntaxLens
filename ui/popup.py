from PyQt6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout,
                             QGraphicsDropShadowEffect, QFrame, QPushButton,
                             QApplication, QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QCursor


class PopupResult(QWidget):
    def __init__(self):
        super().__init__()
        # 无边框 + 置顶 + 工具窗口
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(self.main_layout)

        # --- 样式核心 ---
        self.container = QFrame()
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            #container {
                background-color: #1e1e1e; 
                border: 1px solid #333333;
                border-radius: 10px;
            }
            QLabel#title_lbl {
                color: #888888;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton#close_btn {
                background: transparent;
                color: #666666;
                border: none;
                font-size: 16px;
                font-family: Arial;
                border-radius: 4px;
            }
            QPushButton#close_btn:hover {
                background-color: #c42b1c;
                color: white;
            }
            QLabel#content_lbl {
                color: #d4d4d4;
                font-family: 'Segoe UI', 'Microsoft YaHei';
                font-size: 14px;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #1e1e1e;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #444;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #666;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.container.setGraphicsEffect(shadow)

        self.main_layout.addWidget(self.container)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(12, 12, 5, 12)
        container_layout.setSpacing(5)

        # 1. 标题栏
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 5, 0)

        self.title = QLabel("🤖 分析结果")
        self.title.setObjectName("title_lbl")

        btn_close = QPushButton("×")
        btn_close.setObjectName("close_btn")
        btn_close.setFixedSize(24, 24)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.hide)

        header.addWidget(self.title)
        header.addStretch()
        header.addWidget(btn_close)
        container_layout.addLayout(header)

        # 2. 滚动内容区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent;")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 5, 5, 5)

        self.label = QLabel("Waiting...")
        self.label.setObjectName("content_lbl")
        self.label.setWordWrap(True)
        self.label.setTextFormat(Qt.TextFormat.RichText)
        self.label.setOpenExternalLinks(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)

        scroll_layout.addWidget(self.label)
        self.scroll_area.setWidget(scroll_content)

        container_layout.addWidget(self.scroll_area)

        self.m_Position = None
        self.is_pressed = False

    def show_loading(self, title="AI 思考中"):
        self.title.setText(f"🤖 {title}")
        self.label.setText("""
            <div style='text-align:center; margin-top:20px;'>
                <span style='font-size:16px; color:#569cd6; font-weight:bold;'>🚀 正在分析语义...</span><br>
                <span style='font-size:12px; color:#666;'>Thinking...</span>
            </div>
        """)
        # 重置回顶部 (关键)
        self.scroll_area.verticalScrollBar().setValue(0)
        self.resize(340, 180)
        self.move_to_mouse()
        self.show()
        self.raise_()

    def update_stream_content(self, html_content, is_finished=False):
        self.label.setText(html_content)

        # --- 窗口高度自动伸展逻辑 ---
        # 目标：让窗口变高，显示更多内容
        doc_height = self.label.sizeHint().height()
        target_height = min(max(doc_height + 60, 150), 600)  # 最大高度 600

        if abs(self.height() - target_height) > 30:
            self.resize(self.width(), target_height)

        # --- ❌ 删除了“自动滚动到底部”的代码 ---
        # 现在的行为是：窗口变高，内容增加，但滚动条位置不动。
        # 如果用户在顶部，看到的就是顶部；如果用户自己滑到底部，那就是底部。

    def show_message(self, text):
        self.label.setText(f"<div style='color:#ce9178'>{text}</div>")
        self.resize(300, 120)
        self.move_to_mouse()
        self.show()

    def move_to_mouse(self):
        cursor = QCursor.pos()
        screen = QApplication.primaryScreen().availableGeometry()
        x, y = cursor.x() + 20, cursor.y() + 20
        w, h = self.width(), self.height()

        if x + w > screen.right(): x = cursor.x() - w - 10
        if y + h > screen.bottom(): y = cursor.y() - h - 10
        self.move(x, y)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.is_pressed = True
            self.m_Position = e.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, e):
        if self.is_pressed: self.move(e.globalPosition().toPoint() - self.m_Position)

    def mouseReleaseEvent(self, e):
        self.is_pressed = False