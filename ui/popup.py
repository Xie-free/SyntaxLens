from PyQt6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout,
                             QGraphicsDropShadowEffect, QFrame, QPushButton,
                             QApplication, QScrollArea, QSizePolicy, QSizeGrip)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor


class PopupResult(QWidget):
    closed_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        # 设置无边框、置顶、工具窗口，同时关键：不接受焦点，不激活窗口（防偷光标焦点）
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # 允许调整大小
        self.setMinimumWidth(300)  # 最小宽度
        self.setMinimumHeight(150)  # 最小高度

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(self.main_layout)

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
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

            /* 调整右下角手柄样式 */
            QSizeGrip {
                background: transparent;
                width: 16px;
                height: 16px;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.container.setGraphicsEffect(shadow)

        self.main_layout.addWidget(self.container)

        # 容器布局
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(12, 12, 5, 5)  # 底部留空给 SizeGrip
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
        btn_close.clicked.connect(self.close_popup)
        header.addWidget(self.title)
        header.addStretch()
        header.addWidget(btn_close)
        container_layout.addLayout(header)

        # 2. 滚动内容区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent;")

        # ❌ 关键：彻底禁用水平滚动条，强制换行
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 5, 5, 5)

        self.label = QLabel("Waiting...")
        self.label.setObjectName("content_lbl")
        self.label.setWordWrap(True)  # 允许文字换行
        self.label.setTextFormat(Qt.TextFormat.RichText)
        self.label.setOpenExternalLinks(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        # 允许垂直方向无限伸展
        self.label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)

        scroll_layout.addWidget(self.label)
        self.scroll_area.setWidget(scroll_content)
        container_layout.addWidget(self.scroll_area)

        # 3. 底部右下角拖拽手柄
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()  # 把手柄挤到最右边
        self.size_grip = QSizeGrip(self.container)  # 绑定到 container 上
        self.size_grip.setFixedSize(16, 16)
        bottom_layout.addWidget(self.size_grip)
        container_layout.addLayout(bottom_layout)

        self.m_Position = None
        self.is_pressed = False

    def close_popup(self):
        self.hide()
        self.closed_signal.emit()

    def show_loading(self, title="AI 思考中"):
        self.title.setText(f"🤖 {title}")
        self.label.setText("""
            <div style='text-align:center; margin-top:20px;'>
                <span style='font-size:16px; color:#569cd6; font-weight:bold;'>🚀 正在分析...</span><br>
                <span style='font-size:12px; color:#666;'>Thinking...</span>
            </div>
        """)
        self.scroll_area.verticalScrollBar().setValue(0)

        # 默认稍微宽一点 (340 -> 380)
        self.resize(380, 180)
        self.move_to_mouse()
        # 使用 show 结合 WA_ShowWithoutActivating 和 WindowDoesNotAcceptFocus 不会抢焦点
        self.show()
        # 注意：不要调用 self.raise_() 或 self.activateWindow() ，这会强制抢夺焦点

    def update_stream_content(self, html_content, is_finished=False):
        self.label.setText(html_content)

        # 自动长高
        doc_height = self.label.sizeHint().height()
        target_height = min(max(doc_height + 80, 180), 600)

        # 只调整高度，不改变当前宽度（因为用户可能手动拉宽了）
        current_width = self.width()

        if abs(self.height() - target_height) > 30:
            self.resize(current_width, target_height)

    def show_message(self, text):
        self.label.setText(f"<div style='color:#ce9178'>{text}</div>")
        self.resize(320, 120)
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