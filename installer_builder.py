import os
import sys
import zipfile
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import winreg
import ctypes
from PIL import Image, ImageTk

# Название продукта и пути
APP_NAME = "AURA Voice Injector"
STUDIO_NAME = "AI STUDIO ShenData"
VERSION = "1.0.0 Commercial"
DEFAULT_INSTALL_DIR = os.path.join(os.environ.get("LOCALAPPDATA", "C:\\"), "ShenData", "AuraVoice")

class AuraInstallerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Установка — {APP_NAME}")
        self.root.geometry("540x400")
        self.root.resizable(False, False)
        self.root.configure(bg="#12131A")

        # Тёмная палитра DS AURA
        self.bg_dark = "#12131A"
        self.bg_card = "#1C1D27"
        self.accent_purple = "#9333EA"
        self.accent_pink = "#EC4899"
        self.text_main = "#F8FAFC"
        self.text_muted = "#94A3B8"

        self.install_dir = tk.StringVar(value=DEFAULT_INSTALL_DIR)
        self.autostart_var = tk.BooleanVar(value=True)
        self.desktop_icon_var = tk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self):
        # Шапка с логотипом и брендингом DS AURA
        header_frame = tk.Frame(self.root, bg="#181825", height=80)
        header_frame.pack(fill=tk.X)

        title_lbl = tk.Label(
            header_frame, text=APP_NAME, font=("Segoe UI", 16, "bold"),
            bg="#181825", fg=self.text_main
        )
        title_lbl.pack(anchor="w", padx=20, pady=(15, 2))

        sub_lbl = tk.Label(
            header_frame, text=f"{STUDIO_NAME} • Версия {VERSION}",
            font=("Segoe UI", 9), bg="#181825", fg=self.accent_purple
        )
        sub_lbl.pack(anchor="w", padx=20, pady=(0, 10))

        # Тело установщика
        body = tk.Frame(self.root, bg=self.bg_dark)
        body.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

        desc = tk.Label(
            body,
            text="Вас приветствует мастер установки AURA Voice Injector.\n"
                 "Приложение позволяет вводить текст голосом во все ИИ (Antigravity, Codex, DeepSeek)\n"
                 "с оригинальной физикой Liquid Mercury и минималистичной 12px капсулой.",
            font=("Segoe UI", 9), bg=self.bg_dark, fg=self.text_muted, justify=tk.LEFT
        )
        desc.pack(anchor="w", pady=(0, 15))

        # Папка установки
        dir_lbl = tk.Label(body, text="Папка установки:", font=("Segoe UI", 9, "bold"), bg=self.bg_dark, fg=self.text_main)
        dir_lbl.pack(anchor="w")

        dir_frame = tk.Frame(body, bg=self.bg_dark)
        dir_frame.pack(fill=tk.X, pady=(4, 15))

        dir_entry = tk.Entry(dir_frame, textvariable=self.install_dir, font=("Segoe UI", 9), bg=self.bg_card, fg=self.text_main, bd=1, relief=tk.SOLID)
        dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)

        # Опции
        chk1 = tk.Checkbutton(
            body, text="Запускать AURA Voice при старте Windows",
            variable=self.autostart_var, font=("Segoe UI", 9),
            bg=self.bg_dark, fg=self.text_main, selectcolor=self.bg_card, activebackground=self.bg_dark, activeforeground=self.text_main
        )
        chk1.pack(anchor="w", pady=2)

        chk2 = tk.Checkbutton(
            body, text="Создать ярлык на Рабочем столе",
            variable=self.desktop_icon_var, font=("Segoe UI", 9),
            bg=self.bg_dark, fg=self.text_main, selectcolor=self.bg_card, activebackground=self.bg_dark, activeforeground=self.text_main
        )
        chk2.pack(anchor="w", pady=2)

        # Прогресс бар
        self.progress = ttk.Progressbar(body, orient=tk.HORIZONTAL, mode='determinate')
        self.status_lbl = tk.Label(body, text="Нажмите «Установить» для продолжения", font=("Segoe UI", 8), bg=self.bg_dark, fg=self.text_muted)

        # Подвал с кнопками
        footer = tk.Frame(self.root, bg="#181825", height=60)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        self.btn_install = tk.Button(
            footer, text="Установить", font=("Segoe UI", 10, "bold"),
            bg=self.accent_purple, fg="#FFFFFF", bd=0, padx=24, pady=8,
            activebackground=self.accent_pink, command=self.start_install
        )
        self.btn_install.pack(side=tk.RIGHT, padx=20, pady=12)

        btn_cancel = tk.Button(
            footer, text="Отмена", font=("Segoe UI", 9),
            bg="#334155", fg=self.text_main, bd=0, padx=16, pady=8,
            activebackground="#475569", command=self.root.destroy
        )
        btn_cancel.pack(side=tk.RIGHT, padx=(0, 10), pady=12)

    def start_install(self):
        self.btn_install.config(state=tk.DISABLED)
        self.progress.pack(fill=tk.X, pady=(15, 5))
        self.status_lbl.pack(anchor="w")
        threading.Thread(target=self._install_worker, daemon=True).start()

    def _install_worker(self):
        target = self.install_dir.get().strip()
        os.makedirs(target, exist_ok=True)

        payload_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "installer_payload.zip")
        if not os.path.exists(payload_path):
            messagebox.showerror("Ошибка", f"Файл архива не найден: {payload_path}")
            return

        self.status_lbl.config(text="Распаковка файлов приложения...")
        with zipfile.ZipFile(payload_path, 'r') as z:
            total = len(z.infolist())
            for i, item in enumerate(z.infolist()):
                z.extract(item, target)
                percent = int((i + 1) * 100 / total)
                self.progress['value'] = percent
                self.status_lbl.config(text=f"Установка: {percent}% ({item.filename[:30]}...)")

        exe_path = os.path.join(target, "AuraVoice.exe")

        # Добавление в автозагрузку Windows
        if self.autostart_var.get():
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "AuraVoiceInjector", 0, winreg.REG_SZ, f'"{exe_path}"')
                winreg.CloseKey(key)
            except Exception as e:
                print("Autostart reg error:", e)

        # Создание ярлыка
        if self.desktop_icon_var.get():
            try:
                desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
                shortcut_path = os.path.join(desktop, "AURA Voice.lnk")
                # Создаем через powershell WScript.Shell
                cmd = f'$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut("{shortcut_path}"); $s.TargetPath = "{exe_path}"; $s.WorkingDirectory = "{target}"; $s.Description = "AURA Voice Injector"; $s.Save()'
                os.system(f'powershell -WindowStyle Hidden -Command "{cmd}"')
            except Exception as e:
                print("Shortcut error:", e)

        self.status_lbl.config(text="Установка успешно завершена!", fg="#10B981")
        self.btn_install.config(text="Готово", state=tk.NORMAL, bg="#10B981", command=lambda: self._finish(exe_path))

    def _finish(self, exe_path):
        # Запускаем приложение после установки
        try:
            os.startfile(exe_path)
        except Exception:
            pass
        self.root.destroy()


def main():
    root = tk.Tk()
    app = AuraInstallerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
