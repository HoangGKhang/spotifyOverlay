import ctypes
import ctypes.wintypes

# Thêm vào đầu file
WM_WINDOWPOSCHANGING = 0x0046
SWP_NOZORDER = 0x0004

WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_long,
    ctypes.wintypes.HWND,
    ctypes.wintypes.UINT,
    ctypes.wintypes.WPARAM,
    ctypes.wintypes.LPARAM
)

class WINDOWPOS(ctypes.Structure):
    _fields_ = [
        ("hwnd", ctypes.wintypes.HWND),
        ("hwndInsertAfter", ctypes.wintypes.HWND),
        ("x", ctypes.c_int),
        ("y", ctypes.c_int),
        ("cx", ctypes.c_int),
        ("cy", ctypes.c_int),
        ("flags", ctypes.wintypes.UINT),
    ]