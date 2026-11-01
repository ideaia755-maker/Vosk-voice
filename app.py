import json
import math
import os
import sys
import threading
import time
import tkinter as tk
import ctypes
from ctypes import wintypes
from PIL import Image, ImageDraw

import pyperclip
from pynput import mouse
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import pystray

# Блокировка одиночного экземпляра через Win32 Mutex (защита от дублирования!)
MUTEX_NAME = "Global\\AURA_Voice_Injector_Single_Instance_Mutex"
kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32

mutex = kernel32.CreateMutexW(None, False, MUTEX_NAME)
if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
    print("[WARN] Приложение уже запущено! Вторая копия закрывается.")
    sys.exit(0)

# ==============================================================================
# ТОЧНАЯ МАТЕМАТИКА ФИЗИКИ ИЗ D:\AI Платформа\DS AURA (liquid-mercury-physics.ts)
# ==============================================================================
BLOB_SEEDS = [
    {"id": 0, "orbit": 0.02, "lane": -0.18, "radius": 0.082, "depth": 0.92, "wobble": 0.2},
    {"id": 1, "orbit": 0.14, "lane": 0.24,  "radius": 0.058, "depth": 0.54, "wobble": 1.1},
    {"id": 2, "orbit": 0.25, "lane": -0.36, "radius": 0.072, "depth": 0.74, "wobble": 2.0},
    {"id": 3, "orbit": 0.37, "lane": 0.12,  "radius": 0.048, "depth": 0.42, "wobble": 2.8},
    {"id": 4, "orbit": 0.48, "lane": 0.34,  "radius": 0.064, "depth": 0.64, "wobble": 3.4},
    {"id": 5, "orbit": 0.58, "lane": -0.22, "radius": 0.050, "depth": 0.50, "wobble": 4.2},
    {"id": 6, "orbit": 0.68, "lane": 0.02,  "radius": 0.090, "depth": 1.00, "wobble": 5.0},
    {"id": 7, "orbit": 0.78, "lane": -0.42, "radius": 0.044, "depth": 0.38, "wobble": 5.8},
    {"id": 8, "orbit": 0.88, "lane": 0.20,  "radius": 0.068, "depth": 0.72, "wobble": 6.3},
    {"id": 9, "orbit": 0.95, "lane": -0.04, "radius": 0.052, "depth": 0.46, "wobble": 7.2},
]

def smoothstep(edge0, edge1, value):
    t = min(1.0, max(0.0, (value - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)

def mix(a, b, t):
    return a + (b - a) * t

def viscous_ease(value):
    t = smoothstep(0.0, 1.0, value)
    return t * t * (3.0 - 2.0 * t)

def resolve_mercury_blobs(cycle, width, height):
    t = cycle % 1.0
    centerX = width / 2.0
    centerY = height / 2.0
    buttonWidth = width / 1.84
    buttonHeight = height / 2.16
    unit = min(buttonWidth, buttonHeight * 2.4)

    converge = viscous_ease((t - 0.48) / 0.24) if (t >= 0.48 and t <= 0.72) else (1.0 if t > 0.72 else 0.0)
    fill = smoothstep(0.72, 0.88, t)
    release = smoothstep(0.96, 1.0, t)
    pull = 1.0 - release if t >= 0.96 else max(converge, fill)
    spinBase = cycle * math.pi * 2.0 * 1.18

    blobs = []
    for seed in BLOB_SEEDS:
        spin = spinBase + seed["orbit"] * math.pi * 2.0 + math.sin(cycle * 2.6 + seed["wobble"]) * 0.12
        spiralRadius = 1.0 - pull * 0.72
        orbitScale = 0.67
        spiralX = math.cos(spin) * buttonWidth * (0.66 + seed["depth"] * 0.2) * spiralRadius * orbitScale
        spiralY = (
            math.sin(spin * 1.32) * buttonHeight * (0.92 + seed["depth"] * 0.24) * spiralRadius * orbitScale +
            seed["lane"] * buttonHeight * 0.28 * (1.0 - pull) * orbitScale
        )
        entryX = (seed["orbit"] - 0.5) * width * 0.26 * (1.0 - fill)
        entryY = seed["lane"] * height * 0.12 * (1.0 - fill)
        settledX = (seed["orbit"] - 0.5) * buttonWidth * 0.42
        settledY = math.sin(seed["orbit"] * math.pi * 2.0) * height * 0.09
        targetX = mix(entryX, settledX, fill)
        targetY = mix(entryY, settledY, fill)
        localX = mix(spiralX, targetX, pull)
        localY = mix(spiralY, targetY, pull)
        breathing = math.sin(cycle * math.pi * 4.0 + seed["wobble"]) * 0.035
        radius = seed["radius"] * unit * (1.0 + converge * 0.18 + fill * 0.34 + breathing)

        blobs.append({
            "x": centerX + localX,
            "y": centerY + localY,
            "radius": max(0.8, radius),
        })
    return blobs


def send_paste_to_target(hwnd):
    """
    Надёжная вставка текста Ctrl+V в активное окно Windows:
    работает в браузере (Chrome, Edge, DeepSeek), терминале (Codex) и IDE (Antigravity).
    """
    if hwnd:
        try:
            cur_tid = kernel32.GetCurrentThreadId()
            tgt_tid = user32.GetWindowThreadProcessId(hwnd, None)
            if cur_tid != tgt_tid:
                user32.AttachThreadInput(cur_tid, tgt_tid, True)
                user32.SetForegroundWindow(hwnd)
                user32.SetFocus(hwnd)
                user32.AttachThreadInput(cur_tid, tgt_tid, False)
            else:
                user32.SetForegroundWindow(hwnd)
                user32.SetFocus(hwnd)
        except Exception as e:
            print(f"[ERR фокуса]: {e}")

    # Небольшая пауза, чтобы целевое окно (браузер / консоль) успело принять фокус
    time.sleep(0.08)

    # Эмуляция нажатия Ctrl+V через keybd_event
    user32.keybd_event(0x11, 0, 0, 0)       # Control Down
    user32.keybd_event(0x56, 0, 0, 0)       # V Down
    time.sleep(0.02)
    user32.keybd_event(0x56, 0, 2, 0)       # V Up
    user32.keybd_event(0x11, 0, 2, 0)       # Control Up


class AuraExactPhysicsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AURA Exact Physics")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        # РАЗМЕР: ВЫСОТА СТРОГО 12 ПИКСЕЛЕЙ!
        self.width = 76
        self.height = 12

        # 100% прозрачность
        self.TRANS_KEY = "#000001"
        self.root.configure(bg=self.TRANS_KEY)
        self.root.wm_attributes("-transparentcolor", self.TRANS_KEY)

        # WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW
        self.root.update_idletasks()
        hwnd = self.root.winfo_id()
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, 0x08000080)

        # Размещение внизу экрана
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        pos_x = screen_w - self.width - 25
        pos_y = screen_h - self.height - 45
        self.root.geometry(f"{self.width}x{self.height}+{pos_x}+{pos_y}")

        self.canvas = tk.Canvas(
            self.root, width=self.width, height=self.height,
            bg=self.TRANS_KEY, highlightthickness=0, bd=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._do_drag)

        # Состояния
        self.is_recording = False
        self.mic_available = False
        self.target_hwnd = None
        self.audio_data_list = []
        self.sample_rate = 16000
        self.recognizer = None
        self.model = None

        self.cycle_time = 0.0
        self.last_anim_time = time.time()

        # Параметры удержания правой кнопки мыши (ПКМ Hold-to-Talk)
        self.rmb_press_time = 0.0
        self.rmb_hold_threshold = 0.28  # 280 мс порог удержания для запуска записи
        self.rmb_timer = None

        self._check_mic()
        threading.Thread(target=self._init_vosk, daemon=True).start()

        self.mouse_listener = mouse.Listener(on_click=self._on_mouse_click)
        self.mouse_listener.start()

        self._init_tray()
        self._animate()

    def _start_drag(self, event):
        self.drag_x = event.x
        self.drag_y = event.y

    def _do_drag(self, event):
        x = self.root.winfo_x() + (event.x - self.drag_x)
        y = self.root.winfo_y() + (event.y - self.drag_y)
        self.root.geometry(f"+{x}+{y}")

    def _init_tray(self):
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((4, 4, 60, 60), fill=(42, 23, 59, 255), outline=(168, 85, 247, 255), width=3)
        menu = pystray.Menu(
            pystray.MenuItem("AURA Exact Physics (12px)", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Выход", self._quit_app)
        )
        self.tray = pystray.Icon("aura_exact", img, "AURA Voice 12px", menu)
        threading.Thread(target=self.tray.run, daemon=True).start()

    def _quit_app(self):
        if self.tray:
            self.tray.stop()
        self.root.destroy()
        os._exit(0)

    def _check_mic(self):
        try:
            devs = sd.query_devices()
            self.mic_available = any(d.get("max_input_channels", 0) > 0 for d in devs)
        except Exception:
            self.mic_available = False

    def _get_safe_model_path(self):
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model")
        buf = ctypes.create_unicode_buffer(1024)
        res = kernel32.GetShortPathNameW(model_path, buf, 1024)
        return buf.value if res > 0 else model_path

    def _init_vosk(self):
        try:
            path = self._get_safe_model_path()
            self.model = Model(path)
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
            print("[OK] Модель Vosk загружена.")
        except Exception as e:
            print(f"[ERR] Vosk error: {e}")

    def _on_mouse_click(self, x, y, button, pressed):
        # Поддержка ПКМ (правая кнопка) и сохранение скролла (колесико)
        if button == mouse.Button.right:
            if pressed:
                # Фиксируем окно с фокусом в момент нажатия
                fg = user32.GetForegroundWindow()
                if fg and fg != self.root.winfo_id():
                    self.target_hwnd = fg
                self.rmb_press_time = time.time()

                # Таймер: если ПКМ зажата дольше 280мс -> включаем запись!
                if self.rmb_timer:
                    self.rmb_timer.cancel()
                self.rmb_timer = threading.Timer(self.rmb_hold_threshold, self._on_rmb_held)
                self.rmb_timer.start()
            else:
                # Отпустили ПКМ
                if self.rmb_timer:
                    self.rmb_timer.cancel()
                    self.rmb_timer = None

                if self.is_recording:
                    # Была запись: отпускаем ПКМ -> распознаем и вставляем
                    self.root.after(0, self.stop_recording)
                    # Подавляем появление контекстного меню нажатием клавиши Esc
                    threading.Thread(target=self._dismiss_context_menu, daemon=True).start()
                else:
                    # Обычный быстрый клик ПКМ (<280мс): не мешаем системе вызвать контекстное меню
                    pass

        elif button == mouse.Button.middle:
            # Запасной вариант на колёсико мыши
            if pressed:
                fg = user32.GetForegroundWindow()
                if fg and fg != self.root.winfo_id():
                    self.target_hwnd = fg
                self.root.after(0, self.start_recording)
            else:
                self.root.after(0, self.stop_recording)

    def _on_rmb_held(self):
        """Вызывается, когда ПКМ удерживается дольше порога."""
        self.root.after(0, self.start_recording)

    def _dismiss_context_menu(self):
        """Мягко закрывает всплывшее контекстное меню Windows после завершения голосовой записи."""
        time.sleep(0.04)
        user32.keybd_event(0x1B, 0, 0, 0) # VK_ESCAPE
        time.sleep(0.01)
        user32.keybd_event(0x1B, 0, 2, 0)

    def start_recording(self):
        if not self.mic_available or not self.recognizer or self.is_recording:
            return
        self.is_recording = True
        self.audio_data_list = []
        threading.Thread(target=self._record_audio_loop, daemon=True).start()

    def _audio_callback(self, indata, frames, time_info, status):
        if self.is_recording:
            self.audio_data_list.append(bytes(indata))

    def _record_audio_loop(self):
        try:
            with sd.RawInputStream(samplerate=self.sample_rate, blocksize=4000, dtype='int16',
                                   channels=1, callback=self._audio_callback):
                while self.is_recording:
                    time.sleep(0.02)
        except Exception as e:
            print(f"Ошибка микрофона: {e}")
            self.mic_available = False

    def stop_recording(self):
        if not self.is_recording:
            return
        self.is_recording = False
        threading.Thread(target=self._process_and_inject, daemon=True).start()

    def _process_and_inject(self):
        rec = KaldiRecognizer(self.model, self.sample_rate)
        rec.SetWords(True)

        recognized_parts = []
        for chunk in self.audio_data_list:
            if rec.AcceptWaveform(chunk):
                res = json.loads(rec.Result())
                chunk_text = res.get("text", "").strip()
                if chunk_text:
                    recognized_parts.append(chunk_text)

        # Забираем остаток фразы из буфера
        final_res = json.loads(rec.FinalResult())
        final_text = final_res.get("text", "").strip()
        if final_text:
            recognized_parts.append(final_text)

        full_text = " ".join(recognized_parts).strip()

        if full_text:
            formatted = full_text[0].upper() + full_text[1:] + " "
            print(f"[AURA Голос -> Вставка]: {formatted}")
            pyperclip.copy(formatted)
            send_paste_to_target(self.target_hwnd)
        else:
            print("[AURA]: Речь не распознана")

    def _animate(self):
        now = time.time()
        dt = now - self.last_anim_time
        self.last_anim_time = now

        self.canvas.delete("all")
        cx = self.width / 2.0
        cy = self.height / 2.0

        pill_w = 40.0
        x1 = cx - pill_w / 2.0
        x2 = cx + pill_w / 2.0
        r = 5.5

        fill_col = "#38194e" if self.is_recording else "#1f102c"
        border_col = "#ec4899" if self.is_recording else "#9333ea"

        self.canvas.create_oval(x1, 0.5, x1 + r*2, 11.5, fill=fill_col, outline=border_col, width=1)
        self.canvas.create_oval(x2 - r*2, 0.5, x2, 11.5, fill=fill_col, outline=border_col, width=1)
        self.canvas.create_rectangle(x1 + r, 0.5, x2 - r, 11.5, fill=fill_col, outline="")
        self.canvas.create_line(x1 + r, 0.5, x2 - r, 0.5, fill=border_col, width=1)
        self.canvas.create_line(x1 + r, 11.5, x2 - r, 11.5, fill=border_col, width=1)

        txt = "REC" if self.is_recording else "AURA"
        self.canvas.create_text(cx, cy, text=txt, fill="#ffffff", font=("Segoe UI", 6, "bold"))

        if not self.mic_available:
            self.canvas.create_oval(cx - 2, cy - 2, cx + 2, cy + 2, fill="#f43f5e", outline="")
            self.root.after(150, self._animate)
            return

        if self.is_recording:
            self.cycle_time += dt * 0.28
        else:
            self.cycle_time = 0.18

        blobs = resolve_mercury_blobs(self.cycle_time, self.width, self.height)

        for b in blobs:
            bx = b["x"]
            by = b["y"]
            br = b["radius"] * 0.42

            self.canvas.create_oval(bx - br, by - br, bx + br, by + br, fill="#cbd5e1", outline="#64748b", width=1)
            if br >= 1.2:
                self.canvas.create_oval(bx - br*0.4, by - br*0.4, bx, by, fill="#ffffff", outline="")

        self.root.after(16, self._animate)


def main():
    root = tk.Tk()
    app = AuraExactPhysicsApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
