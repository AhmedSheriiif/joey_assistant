"""Screen capture of the Power of Chaos window (Windows, standard library + Pillow)."""
import ctypes, ctypes.wintypes as wt
from PIL import ImageGrab

user32 = ctypes.windll.user32
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try: user32.SetProcessDPIAware()
    except Exception: pass


def find_window(title_part="Power of Chaos"):
    found = []
    EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)
    def cb(h, _):
        if user32.IsWindowVisible(h):
            n = user32.GetWindowTextLengthW(h)
            if n:
                buf = ctypes.create_unicode_buffer(n + 1); user32.GetWindowTextW(h, buf, n + 1)
                if title_part.lower() in buf.value.lower(): found.append((h, buf.value))
        return True
    user32.EnumWindows(EnumProc(cb), 0)
    return found[0] if found else None


def client_rect(hwnd):
    rc = wt.RECT(); user32.GetClientRect(hwnd, ctypes.byref(rc))
    pt = wt.POINT(0, 0); user32.ClientToScreen(hwnd, ctypes.byref(pt))
    return pt.x, pt.y, pt.x + rc.right, pt.y + rc.bottom


def grab_game():
    w = find_window()
    if not w:
        raise RuntimeError("game window not found")
    x0, y0, x1, y1 = client_rect(w[0])
    return ImageGrab.grab(bbox=(x0, y0, x1, y1)), (x0, y0, x1, y1)


if __name__ == "__main__":
    img, box = grab_game()
    print("window", box, img.size)
    img.save("calibration/game.png")


def grab_window_printwindow(hwnd):
    """Capture a window even when it is covered (works for GDI windows; DirectX games may come out black)."""
    import ctypes
    from PIL import Image
    gdi32 = ctypes.windll.gdi32
    rc = wt.RECT(); user32.GetClientRect(hwnd, ctypes.byref(rc)); w, h = rc.right, rc.bottom
    hdc = user32.GetWindowDC(hwnd); mdc = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h); gdi32.SelectObject(mdc, bmp)
    ok = user32.PrintWindow(hwnd, mdc, 3)          # PW_CLIENTONLY | PW_RENDERFULLCONTENT
    class BIH(ctypes.Structure):
        _fields_ = [("biSize", ctypes.c_uint32), ("biWidth", ctypes.c_int32), ("biHeight", ctypes.c_int32), ("biPlanes", ctypes.c_uint16),
                    ("biBitCount", ctypes.c_uint16), ("biCompression", ctypes.c_uint32), ("biSizeImage", ctypes.c_uint32),
                    ("x", ctypes.c_int32), ("y", ctypes.c_int32), ("a", ctypes.c_uint32), ("b", ctypes.c_uint32)]
    bi = BIH(ctypes.sizeof(BIH), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(mdc, bmp, 0, h, buf, ctypes.byref(bi), 0)
    img = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB")
    gdi32.DeleteObject(bmp); gdi32.DeleteDC(mdc); user32.ReleaseDC(hwnd, hdc)
    return img, ok
