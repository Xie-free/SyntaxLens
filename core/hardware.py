import ctypes
import time

# --- Windows 底层结构体定义 ---
PUL = ctypes.POINTER(ctypes.c_ulong)


class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]


class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]


class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]


class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]


class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]


# --- 核心发送函数 ---
def send_scan_code(hexKeyCode, is_press):
    """
    发送硬件扫描码
    :param hexKeyCode: 扫描码
    :param is_press: True按下, False松开
    """
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()

    # 0x0008: KEYEVENTF_SCANCODE
    flags = 0x0008

    if not is_press:
        flags |= 0x0002  # KEYEVENTF_KEYUP

    # 处理扩展键 (Home, End, Arrows等)
    if hexKeyCode in [0x47, 0x4F, 0x48, 0x50, 0x4B, 0x4D, 0x1D]:
        flags |= 0x0001  # KEYEVENTF_EXTENDEDKEY

    ii_.ki = KeyBdInput(0, hexKeyCode, flags, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


# --- 常用扫描码映射 ---
DIK_LSHIFT = 0x2A
DIK_LCONTROL = 0x1D
DIK_HOME = 0x47
DIK_END = 0x4F
DIK_C = 0x2E
DIK_RIGHT = 0x4D


# --- 便捷操作函数 ---
def hard_press(code):
    send_scan_code(code, True)


def hard_release(code):
    send_scan_code(code, False)


def hard_click(code):
    """单击：按下并松开"""
    hard_press(code)
    time.sleep(0.05)
    hard_release(code)