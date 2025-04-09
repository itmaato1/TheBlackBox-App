import customtkinter as ctk
from PIL import Image
import subprocess
import os
import json
import threading
import time
import tkinter.messagebox
import ctypes
import sys

# Константы
CONFIG_PATH = "vpn_settings.json"
APP_VERSION = "0.2.1"
OVPN_PATH = os.path.join(os.getcwd(), "TBB.ovpn")
ICON_PATH = "ZG_APP.ico"  # Иконка приложения (для заголовка и панели задач)
LOGO_PATH = "logo.png"    # Логотип внутри интерфейса
STARTMENU_ICON = "STARTMENUAPP.ico"  # Иконка для меню "Пуск"

# Проверка запуска от имени администратора
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# Перезапуск приложения с правами администратора
if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",  # Запуск от имени администратора
        sys.executable,
        " ".join(sys.argv),  # Аргументы командной строки
        None,
        1  # Показать окно
    )
    sys.exit()

def load_settings():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            if settings.get("version") != APP_VERSION:
                settings["first_launch"] = True
                settings["version"] = APP_VERSION
            return settings
    return {
        "autostart": False,
        "autoconnect": False,
        "minimized": False,
        "language": "Русский",
        "logging": False,
        "first_launch": True,
        "version": APP_VERSION
    }

def save_settings(settings):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

class OpenVPNConnector:
    def __init__(self, config_file, executable_path='C:\\Program Files\\OpenVPN\\bin\\openvpn.exe'):
        self.config_file = config_file
        self.executable_path = executable_path
        self.process = None

    def connect(self):
        try:
            self.process = subprocess.Popen(
                [self.executable_path, '--config', self.config_file]
            )
            print('Connected to OpenVPN')
        except Exception as e:
            print(f'Failed to connect to VPN: {e}')
            tkinter.messagebox.showerror("Ошибка подключения", f"Не удалось подключиться к VPN.\n{e}")

    def disconnect(self):
        try:
            if self.process:
                self.process.kill()
                print('Disconnected from OpenVPN')
        except Exception as e:
            print(f'Failed to disconnect from VPN: {e}')
            tkinter.messagebox.showerror("Ошибка отключения", f"Не удалось отключиться от VPN.\n{e}")

class VPNApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("TBB VPN")
        self.geometry("450x600")
        self.resizable(False, False)  # Разрешаем изменять размер окна

        # Установка цвета фона приложения
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        self.configure(fg_color="#2B2B2B")  # Основной цвет фона

        # Установка иконки приложения
        try:
            self.iconbitmap(ICON_PATH)  # Установка иконки для заголовка и панели задач
        except Exception as e:
            print(f"Ошибка загрузки иконки приложения: {e}")

        self.settings = load_settings()
        save_settings(self.settings)

        self.connector = OpenVPNConnector(OVPN_PATH)
        self.status = 0

        # Создание контейнера для страниц
        self.container = ctk.CTkFrame(self, fg_color="#2B2B2B")  # Фон контейнера
        self.container.pack(fill="both", expand=True)

        # Создание страниц
        self.frames = {}
        for F in (MainPage, SettingsPage):
            frame = F(parent=self.container, controller=self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Отображение главной страницы
        self.show_frame(MainPage)

        if self.settings["first_launch"]:
            self.show_welcome()
            self.settings["first_launch"] = False
            save_settings(self.settings)

        if self.settings["autoconnect"]:
            self.toggle_connection()

    def show_frame(self, page):
        """Переключение между страницами."""
        frame = self.frames[page]
        frame.tkraise()

    def show_welcome(self):
        splash = ctk.CTkToplevel(self)
        splash.geometry("400x300")
        splash.configure(fg_color="#2B2B2B")  # Цвет фона всплывающего окна
        splash_label = ctk.CTkLabel(splash, text="Добро пожаловать в TBB VPN!", font=("SF Pro Rounded", 20, "bold"))
        splash_label.pack(pady=50)
        splash_button = ctk.CTkButton(splash, text="Начать", command=splash.destroy, font=("SF Pro Rounded", 16))
        splash_button.pack(pady=20)
        splash.grab_set()
        splash.lift()
        splash.focus_force()

    def toggle_connection(self):
        self.frames[MainPage].progress.start()
        threading.Thread(target=self._handle_vpn_toggle, daemon=True).start()

    def _handle_vpn_toggle(self):
        time.sleep(1.2)
        if self.status == 0:
            self.connector.connect()
            self.status = 1
            self.frames[MainPage].status_label.configure(text="🟢 Подключено")
            self.frames[MainPage].toggle_button.configure(text="Отключиться", fg_color="#FF453A", hover_color="#E63A30")
        else:
            self.connector.disconnect()
            self.status = 0
            self.frames[MainPage].status_label.configure(text="🔴 Отключено")
            self.frames[MainPage].toggle_button.configure(text="Подключиться", fg_color="#30D158", hover_color="#28B34C")
        self.frames[MainPage].progress.stop()

class MainPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#2B2B2B")  # Цвет фона страницы
        self.controller = controller

        # Логотип внутри интерфейса
        try:
            logo_image = ctk.CTkImage(dark_image=Image.open(LOGO_PATH), size=(100, 100))
            self.logo_label = ctk.CTkLabel(self, image=logo_image, text="")
            self.logo_label.pack(pady=(20, 10))
        except Exception as e:
            print(f"Ошибка загрузки логотипа: {e}")
            self.logo_label = ctk.CTkLabel(self, text="TBB VPN", font=("SF Pro Rounded", 32, "bold"))
            self.logo_label.pack(pady=(20, 10))

        # Статус подключения
        self.status_label = ctk.CTkLabel(self, text="🔴 Отключено", font=("SF Pro Rounded", 18))
        self.status_label.pack(pady=(5, 20))

        # Кнопка подключения/отключения
        self.toggle_button = ctk.CTkButton(
            self,
            text="Подключиться",
            font=("SF Pro Rounded", 20, "bold"),
            fg_color="#30D158",
            hover_color="#28B34C",
            corner_radius=15,
            height=50,
            command=self.controller.toggle_connection
        )
        self.toggle_button.pack(pady=10, ipadx=20, ipady=10)

        # Прогрессбар
        self.progress = ctk.CTkProgressBar(self, orientation="horizontal", mode="indeterminate", fg_color="#2B2B2B", progress_color="#30D158")
        self.progress.pack(pady=4, fill="x", padx=0)  # Растягиваем по всей ширине
        self.progress.stop()

        # Кнопка перехода к настройкам
        self.settings_button = ctk.CTkButton(
            self,
            text="Настройки",
            font=("SF Pro Rounded", 16),
            fg_color="#1C1D21",
            hover_color="#2C2C2E",
            corner_radius=15,
            height=40,
            command=lambda: self.controller.show_frame(SettingsPage)
        )
        self.settings_button.pack(pady=20)

        # Нижний колонтитул
        self.footer = ctk.CTkLabel(self, text=f"Версия: {APP_VERSION}", font=("SF Pro Rounded", 12), text_color="gray")
        self.footer.pack(pady=(10, 10))

class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#2B2B2B")  # Цвет фона страницы
        self.controller = controller

        # Заголовок страницы настроек
        self.title_label = ctk.CTkLabel(self, text="Настройки", font=("SF Pro Rounded", 24, "bold"))
        self.title_label.pack(pady=(20, 10))

        # Раздел настроек
        self.settings_frame = ctk.CTkScrollableFrame(self, corner_radius=15, fg_color="#1C1C1E", width=400, height=400)
        self.settings_frame.pack(pady=(0, 20))

        self.create_switch(self.settings_frame, "Автозапуск", "autostart")
        self.create_switch(self.settings_frame, "Автоподключение", "autoconnect")
        self.create_switch(self.settings_frame, "Свернутый запуск", "minimized")
        self.create_switch(self.settings_frame, "Логирование", "logging")

        # Кнопка возврата на главную страницу
        self.back_button = ctk.CTkButton(
            self,
            text="Назад",
            font=("SF Pro Rounded", 16),
            fg_color="#1C1D21",
            hover_color="#2C2C2E",
            corner_radius=15,
            height=40,
            command=lambda: self.controller.show_frame(MainPage)
        )
        self.back_button.pack(pady=20)

    def create_switch(self, parent, label, key):
        frame = ctk.CTkFrame(parent, fg_color="#2C2C2E")
        frame.pack(fill="x", pady=6, padx=10)

        title = ctk.CTkLabel(frame, text=label, font=("SF Pro Rounded", 14))
        title.pack(side="left", padx=10)
        switch = ctk.CTkSwitch(frame, command=lambda k=key: self.toggle_setting(k))
        switch.pack(side="right", padx=10)
        switch.select() if self.controller.settings[key] else switch.deselect()

    def toggle_setting(self, key):
        self.controller.settings[key] = not self.controller.settings[key]
        save_settings(self.controller.settings)

if __name__ == "__main__":
    app = VPNApp()
    app.mainloop()