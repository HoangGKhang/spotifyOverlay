import ctypes
import ctypes.wintypes

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QFrame
from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtGui import QFont


# ── Extended window styles ──────────────────────────────────────────────────
GWL_EXSTYLE       = -20
WS_EX_LAYERED     = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW  = 0x00000080
WS_EX_NOACTIVATE  = 0x08000000
WS_EX_TOPMOST     = 0x00000008

# ── SetWindowPos flags ──────────────────────────────────────────────────────
HWND_TOPMOST   = ctypes.wintypes.HWND(-1)
SWP_NOMOVE     = 0x0002
SWP_NOSIZE     = 0x0001
SWP_NOACTIVATE = 0x0010

# ── SetWinEventHook ─────────────────────────────────────────────────────────
EVENT_SYSTEM_FOREGROUND = 0x0003
WINEVENT_OUTOFCONTEXT   = 0x0000

WinEventProc = ctypes.WINFUNCTYPE(
    None,
    ctypes.wintypes.HANDLE,   # hWinEventHook
    ctypes.wintypes.DWORD,    # event
    ctypes.wintypes.HWND,     # hwnd
    ctypes.wintypes.LONG,     # idObject
    ctypes.wintypes.LONG,     # idChild
    ctypes.wintypes.DWORD,    # dwEventThread
    ctypes.wintypes.DWORD,    # dwmsEventTime
)

user32 = ctypes.windll.user32


class LyricsOverlay(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Spotify Lyrics Overlay")

        self.locked = True
        self.dragging = False
        self.drag_position = QPoint()

        # Giữ ref tránh GC thu hồi callback
        self._win_event_proc = None
        self._win_event_hook = None

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowDoesNotAcceptFocus
        )

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        # ── Layout ──────────────────────────────────────────────────────────
        self.container = QFrame()
        self.container.setObjectName("container")

        self.current_label = QLabel("Đang chờ nhạc...")
        self.current_label.setAlignment(Qt.AlignCenter)
        self.current_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.current_label.setObjectName("currentLabel")

        layout = QVBoxLayout()
        layout.addWidget(self.current_label)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(0)
        self.container.setLayout(layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        self.setStyleSheet("""
            QFrame#container {
                background-color: rgb(255, 255, 255);
                border: 1px solid rgba(255, 255, 255, 70);
                border-radius: 8px;
            }
            QLabel#currentLabel {
                color: rgba(20, 20, 20, 245);
                background: transparent;
            }
        """)

        # Tọa độ taskbar của bạn — chỉnh lại nếu cần
        self.setGeometry(6, 991, 489, 30)

        # Backup timer — lưới an toàn phụ
        self.keep_top_timer = QTimer(self)
        self.keep_top_timer.timeout.connect(self.force_topmost)
        self.keep_top_timer.start(250)

    # ── Show / close ─────────────────────────────────────────────────────────

    def showEvent(self, event):
        super().showEvent(event)
        self.apply_window_styles()
        self.force_topmost()
        self._install_foreground_hook()

    def closeEvent(self, event):
        self._uninstall_foreground_hook()
        super().closeEvent(event)

    # ── Win32 hook: lắng nghe mọi lần foreground window thay đổi ────────────

    def _install_foreground_hook(self):
        if self._win_event_hook:
            return

        def on_foreground_change(hWinEventHook, event, hwnd,
                                 idObject, idChild, dwEventThread, dwmsEventTime):
            # Bất kỳ app nào được focus → ép overlay lên trên ngay lập tức
            self.force_topmost()

        self._win_event_proc = WinEventProc(on_foreground_change)

        self._win_event_hook = user32.SetWinEventHook(
            EVENT_SYSTEM_FOREGROUND,  # eventMin
            EVENT_SYSTEM_FOREGROUND,  # eventMax
            None,                     # hmodWinEventProc
            self._win_event_proc,
            0,                        # idProcess (0 = tất cả process)
            0,                        # idThread  (0 = tất cả thread)
            WINEVENT_OUTOFCONTEXT
        )

    def _uninstall_foreground_hook(self):
        if self._win_event_hook:
            user32.UnhookWinEvent(self._win_event_hook)
            self._win_event_hook = None

    # ── Window styles ────────────────────────────────────────────────────────

    def apply_window_styles(self):
        hwnd = int(self.winId())
        ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)

        ex_style |= WS_EX_LAYERED
        ex_style |= WS_EX_TOOLWINDOW
        ex_style |= WS_EX_NOACTIVATE
        ex_style |= WS_EX_TOPMOST

        if self.locked:
            ex_style |= WS_EX_TRANSPARENT
            self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        else:
            ex_style &= ~WS_EX_TRANSPARENT
            self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)

    def force_topmost(self):
        hwnd = int(self.winId())
        user32.SetWindowPos(
            hwnd,
            HWND_TOPMOST,
            0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
        )

    # ── Lock / drag ──────────────────────────────────────────────────────────

    def toggle_lock(self):
        self.locked = not self.locked
        self.apply_window_styles()
        self.force_topmost()

    def mouseDoubleClickEvent(self, event):
        self.toggle_lock()
        event.accept()

    def mousePressEvent(self, event):
        if self.locked:
            return
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if self.locked:
            return
        if self.dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            self.force_topmost()
            event.accept()

    def mouseReleaseEvent(self, event):
        if self.locked:
            return
        self.dragging = False
        pos = self.pos()
        print(f"Overlay position: x={pos.x()}, y={pos.y()}")
        print(f"Overlay size: width={self.width()}, height={self.height()}")
        event.accept()

    # ── Text helpers ─────────────────────────────────────────────────────────

    def shorten(self, text: str, max_len: int = 58) -> str:
        if not text:
            return ""
        if len(text) > max_len:
            return text[:max_len] + "..."
        return text

    def set_lyric(self, text: str):
        self.current_label.setText(self.shorten(text or "..."))

    def set_lyric_context(self, previous_text: str, current_text: str, next_text: str):
        self.set_lyric(current_text)