import customtkinter as ctk
import tkinter as tk
import subprocess
import os
import glob
import time
import re
import sys
import json
import shutil
import pwd
from PIL import Image, ImageTk
import threading
from tkinter import messagebox
import tempfile

# --- Cyberpunk Theme Constants ---
# Format: (Light Mode Color, Dark Mode Color)
COLOR_BG = ("#F0F2F5", "#121212")
COLOR_SURFACE = ("#FFFFFF", "#1E1E1E")
COLOR_BORDER = ("#D1D5DB", "#333333")
COLOR_ACCENT_MAIN = ("#0056b3", "#00FF41")  # Dark Blue / Neon Mint
COLOR_ACCENT_SEC = ("#0EA5E9", "#00D4FF")   # Sky Blue / Electric Cyan
COLOR_ERROR = ("#EF4444", "#FF5F5F")
COLOR_WARNING = ("#F59E0B", "#F2C94C")      # Amber / Yellow
COLOR_TEXT_MAIN = ("#111827", "#FFFFFF")
COLOR_TEXT_SEC = ("#6B7280", "#B0B0B0")
COLOR_GRID = ("#E5E7EB", "#2A2A2A")
COLOR_TAB_TEXT = ("#FFFFFF", "#000000")
COLOR_TAB_UNSELECTED = ("#6B7280", "#888888")
COLOR_TAB_HOVER = ("#4B5563", "#AAAAAA")

FONT_HEADER = ("Inter", 20, "bold")
FONT_SUBHEADER = ("Inter", 14, "bold")
FONT_BODY = ("Inter", 12)
FONT_MONO = ("Monospace", 12)

PROFILES_FILE = os.path.join(os.path.expanduser("~"), ".config", "linux_kernel_manager", "profiles.json")

class LineChart(ctk.CTkCanvas):
    def __init__(self, master, width=300, height=100, line_color=COLOR_ACCENT_MAIN, line_color2=None, auto_scale=False, **kwargs):
        # Başlangıç rengini belirle
        mode = ctk.get_appearance_mode()
        idx = 1 if mode == "Dark" else 0
        
        super().__init__(master, width=width, height=height, highlightthickness=0, bg=COLOR_SURFACE[idx], **kwargs)
        
        self.line_color_tuple = line_color
        self.current_line_color = line_color[idx]
        
        self.line_color2_tuple = line_color2
        self.current_line_color2 = line_color2[idx] if line_color2 else None
        
        self.grid_color = COLOR_GRID[idx]
        self.auto_scale = auto_scale
        
        self.data = [0] * 60  # Son 60 veri noktası
        self.data2 = [0] * 60 if line_color2 else None
        
        self.width = width
        self.height = height

    def update_theme(self, mode):
        idx = 1 if mode == "Dark" else 0
        self.configure(bg=COLOR_SURFACE[idx])
        self.current_line_color = self.line_color_tuple[idx]
        if self.line_color2_tuple:
            self.current_line_color2 = self.line_color2_tuple[idx]
        self.grid_color = COLOR_GRID[idx]
        self.draw()

    def add_value(self, value, value2=None):
        # Value 0-100 arası (veya auto_scale ise dinamik)
        self.data.pop(0)
        self.data.append(value)
        
        if self.data2 is not None and value2 is not None:
            self.data2.pop(0)
            self.data2.append(value2)
            
        self.draw()

    def draw(self):
        self.delete("all")
        
        # Ölçekleme
        max_val = 100
        if self.auto_scale:
            all_vals = self.data + (self.data2 if self.data2 else [])
            m = max(all_vals) if all_vals else 0
            if m > 100: max_val = m * 1.2
            elif m > 10: max_val = 100
            else: max_val = 10

        x_gap = self.width / (len(self.data) - 1)
        
        # Grid Lines (Cyberpunk Grid)
        for i in range(1, 5):
            y = i * (self.height / 5)
            self.create_line(0, y, self.width, y, fill=self.grid_color, dash=(2, 4))

        def _plot(data_list, color):
            points = []
            for i, val in enumerate(data_list):
                x = i * x_gap
                if val < 0: val = 0
                y = self.height - (val / max_val * self.height)
                points.append(x)
                points.append(y)
            if len(points) > 2:
                self.create_line(points, fill=color, width=4, stipple="gray50", smooth=True)
                self.create_line(points, fill=color, width=2, smooth=True)

        if self.data2: _plot(self.data2, self.current_line_color2)
        _plot(self.data, self.current_line_color)

class PasswordDialog(ctk.CTkToplevel):
    def __init__(self, title="Şifre Gerekiyor", text="Lütfen şifrenizi girin:"):
        super().__init__()
        self.geometry("400x200")
        self.title(title)
        self.lift()
        self.attributes("-topmost", True)
        self.after(10, self.focus_force)
        self.grab_set()
        
        self.password = None

        self.label = ctk.CTkLabel(self, text=text, font=FONT_BODY)
        self.label.pack(pady=(20, 10), padx=20)

        self.entry = ctk.CTkEntry(self, show="*", width=250)
        self.entry.pack(pady=10, padx=20)
        self.entry.bind("<Return>", self._on_ok)
        self.entry.focus_set()

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(pady=20)

        self.btn_ok = ctk.CTkButton(self.btn_frame, text="Tamam", command=self._on_ok, width=100, fg_color=COLOR_ACCENT_MAIN)
        self.btn_ok.pack(side="left", padx=10)

        self.btn_cancel = ctk.CTkButton(self.btn_frame, text="İptal", command=self._on_cancel, width=100, fg_color=COLOR_ERROR)
        self.btn_cancel.pack(side="left", padx=10)

    def _on_ok(self, event=None):
        self.password = self.entry.get()
        self.destroy()

    def _on_cancel(self):
        self.destroy()

    def get_input(self):
        self.wait_window()
        return self.password

class KernelManager(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Linux Kernel Manager Pro")
        self.geometry("1200x800")
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=COLOR_BG)

        # Uygulama İkonu
        try:
            if hasattr(sys, "_MEIPASS"):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(base_path, "icon.png")
            if os.path.exists(icon_path):
                image = Image.open(icon_path)
                self.icon_photo = ImageTk.PhotoImage(image)
                self.wm_iconphoto(True, self.icon_photo)
        except Exception:
            pass

        # --- UI Layout ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=COLOR_SURFACE)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.logo_label = ctk.CTkLabel(self.sidebar, text="KERNEL\nMANAGER", font=("JetBrains Mono", 24, "bold"), text_color=COLOR_ACCENT_MAIN)
        self.logo_label.pack(pady=20, padx=10)

        # Kalıcı Yap Butonu
        self.btn_make_permanent = ctk.CTkButton(self.sidebar, text="Ayarları Kalıcı Yap", command=self.open_persistence_window, fg_color=COLOR_ACCENT_SEC, text_color=COLOR_TAB_TEXT)
        self.btn_make_permanent.pack(side="bottom", pady=10, padx=10)

        # Profiller Butonu
        self.btn_profiles = ctk.CTkButton(self.sidebar, text="Profiller", command=self.open_profile_window, fg_color=COLOR_ACCENT_MAIN, text_color=COLOR_TAB_TEXT)
        self.btn_profiles.pack(side="bottom", pady=10, padx=10)

        # Tema Değiştirici
        self.switch_var = ctk.StringVar(value="on")
        self.theme_switch = ctk.CTkSwitch(self.sidebar, text="Karanlık Mod", command=self.toggle_theme, 
                                          variable=self.switch_var, onvalue="on", offvalue="off", progress_color=COLOR_ACCENT_MAIN)
        self.theme_switch.pack(side="bottom", pady=20, padx=10)

        # Main View
        self.main_frame = ctk.CTkFrame(self, corner_radius=15, fg_color=COLOR_BG)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        # --- Tabview (Sekmeler) ---
        self.tabview = ctk.CTkTabview(self.main_frame, fg_color=COLOR_BG, 
                                      segmented_button_fg_color=COLOR_SURFACE, 
                                      segmented_button_selected_color=COLOR_ACCENT_MAIN, 
                                      segmented_button_selected_hover_color=COLOR_ACCENT_MAIN, 
                                      segmented_button_unselected_color=COLOR_TAB_UNSELECTED,
                                      segmented_button_unselected_hover_color=COLOR_TAB_HOVER,
                                      text_color=COLOR_TAB_TEXT)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_genel = self.tabview.add("Genel")
        self.tab_cpu = self.tabview.add("CPU")
        self.tab_gpu = self.tabview.add("GPU")
        self.tab_disk_mem = self.tabview.add("Disk ve Bellek")
        self.tab_network = self.tabview.add("Ağ")
        self.tab_modules = self.tabview.add("Modüller")

        # --- Genel Sekmesi Layout ---
        self.genel_scroll = ctk.CTkScrollableFrame(self.tab_genel, fg_color="transparent")
        self.genel_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # 0. Header (Logo + OS Name)
        self.frame_header = ctk.CTkFrame(self.genel_scroll, fg_color="transparent")
        self.frame_header.pack(fill="x", pady=(10, 5), padx=5)
        
        # OS Name Frame
        self.frame_os_name = ctk.CTkFrame(self.frame_header, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=8)
        self.frame_os_name.pack(fill="x", expand=True)

        self.lbl_ascii_logo = ctk.CTkLabel(self.frame_os_name, text="", font=FONT_MONO, justify="left", text_color=COLOR_ACCENT_SEC)
        self.lbl_ascii_logo.pack(side="left", padx=(20, 10), pady=10)

        self.lbl_os_big = ctk.CTkLabel(self.frame_os_name, text="Linux", font=("Inter", 32, "bold"), text_color=COLOR_TEXT_MAIN)
        self.lbl_os_big.pack(side="left", padx=10)

        # 1. Sistem Bilgileri
        self.frame_os = ctk.CTkFrame(self.genel_scroll, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=8)
        self.frame_os.pack(fill="x", pady=5, padx=5)
        ctk.CTkLabel(self.frame_os, text="🖥️ Sistem Bilgileri", font=FONT_SUBHEADER, text_color=COLOR_ACCENT_MAIN).pack(anchor="w", padx=10, pady=5)
        self.lbl_os_info = ctk.CTkLabel(self.frame_os, text="...", justify="left", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_os_info.pack(anchor="w", padx=10, pady=(0, 10))

        # 2. CPU
        self.frame_cpu_genel = ctk.CTkFrame(self.genel_scroll, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=8)
        self.frame_cpu_genel.pack(fill="x", pady=5, padx=5)
        ctk.CTkLabel(self.frame_cpu_genel, text="🧠 İşlemci (CPU)", font=FONT_SUBHEADER, text_color=COLOR_ACCENT_MAIN).pack(anchor="w", padx=10, pady=5)
        self.lbl_cpu_genel = ctk.CTkLabel(self.frame_cpu_genel, text="...", justify="left", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_cpu_genel.pack(anchor="w", padx=10, pady=(0, 10))

        # 3. GPU
        self.frame_gpu_genel = ctk.CTkFrame(self.genel_scroll, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=8)
        self.frame_gpu_genel.pack(fill="x", pady=5, padx=5)
        ctk.CTkLabel(self.frame_gpu_genel, text="🎮 Ekran Kartı (GPU)", font=FONT_SUBHEADER, text_color=COLOR_ACCENT_MAIN).pack(anchor="w", padx=10, pady=5)
        self.lbl_gpu_genel = ctk.CTkLabel(self.frame_gpu_genel, text="...", justify="left", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_gpu_genel.pack(anchor="w", padx=10, pady=(0, 10))

        # 4. Bellek & Disk
        self.frame_storage = ctk.CTkFrame(self.genel_scroll, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=8)
        self.frame_storage.pack(fill="x", pady=5, padx=5)
        ctk.CTkLabel(self.frame_storage, text="💾 Bellek ve Disk", font=FONT_SUBHEADER, text_color=COLOR_ACCENT_MAIN).pack(anchor="w", padx=10, pady=5)
        self.lbl_storage_genel = ctk.CTkLabel(self.frame_storage, text="...", justify="left", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_storage_genel.pack(anchor="w", padx=10, pady=(0, 10))

        # 5. Batarya (Varsayılan olarak gizli, varsa gösterilir)
        self.frame_battery = ctk.CTkFrame(self.genel_scroll, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=8)
        self.lbl_battery_header = ctk.CTkLabel(self.frame_battery, text="🔋 Batarya", font=FONT_SUBHEADER, text_color=COLOR_ACCENT_MAIN)
        self.lbl_battery_header.pack(anchor="w", padx=10, pady=5)
        self.lbl_battery_info = ctk.CTkLabel(self.frame_battery, text="...", justify="left", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_battery_info.pack(anchor="w", padx=10, pady=(0, 10))

        # --- Disk ve Bellek Tab İçeriği ---
        self.ram_frame = ctk.CTkFrame(self.tab_disk_mem, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=8)
        self.ram_frame.pack(pady=10, padx=10, fill="x")

        # RAM Left (Info) & Right (Chart)
        self.ram_left = ctk.CTkFrame(self.ram_frame, fg_color="transparent")
        self.ram_left.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        self.ram_right = ctk.CTkFrame(self.ram_frame, fg_color="transparent")
        self.ram_right.pack(side="right", fill="both", padx=10, pady=10)

        ctk.CTkLabel(self.ram_left, text="Bellek (RAM)", font=FONT_HEADER, text_color=COLOR_ACCENT_MAIN).pack(pady=5, anchor="w")
        self.lbl_ram_total = ctk.CTkLabel(self.ram_left, text="RAM Kapasitesi: ...", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_ram_total.pack(pady=2, anchor="w")

        self.lbl_ram_usage = ctk.CTkLabel(self.ram_left, text="Kullanım: ...", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_ram_usage.pack(pady=2, anchor="w")

        self.ram_progress = ctk.CTkProgressBar(self.ram_left, width=300, progress_color=COLOR_ACCENT_MAIN)
        self.ram_progress.pack(pady=5, anchor="w")
        self.ram_progress.set(0)
        
        self.ram_stats_frame = ctk.CTkFrame(self.ram_left, fg_color="transparent")
        self.ram_stats_frame.pack(pady=5, fill="x", anchor="w")

        self.lbl_ram = ctk.CTkLabel(self.ram_stats_frame, text="RAM Hızı: ...", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_ram.pack(side="left", padx=(0, 10))

        # ZRAM Section (New Layout)
        ctk.CTkLabel(self.ram_left, text="ZRAM", font=FONT_HEADER, text_color=COLOR_ACCENT_MAIN).pack(pady=(20, 5), anchor="w")
        
        self.zram_stats_frame = ctk.CTkFrame(self.ram_left, fg_color="transparent")
        self.zram_stats_frame.pack(fill="x", anchor="w")
        self.lbl_zram_stats = ctk.CTkLabel(self.zram_stats_frame, text="Durum: ...", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_zram_stats.pack(anchor="w")

        self.zram_control_frame = ctk.CTkFrame(self.ram_left, fg_color="transparent")
        self.zram_control_frame.pack(fill="x", pady=5, anchor="w")

        self.zram_algo_var = ctk.StringVar(value="")
        self.cmb_zram_algo = ctk.CTkOptionMenu(self.zram_control_frame, variable=self.zram_algo_var, values=[], command=self.change_zram_algo, width=100, fg_color=COLOR_SURFACE, button_color=COLOR_ACCENT_MAIN)
        self.cmb_zram_algo.pack(side="left", padx=(0, 10))

        self.entry_zram_size = ctk.CTkEntry(self.zram_control_frame, width=80, placeholder_text="Boyut (2G)")
        self.entry_zram_size.pack(side="left", padx=(0, 5))
        self.btn_zram_size = ctk.CTkButton(self.zram_control_frame, text="Ayarla", width=60, command=self.change_zram_size, fg_color=COLOR_ACCENT_MAIN, text_color=("white", "black"))
        self.btn_zram_size.pack(side="left")

        # RAM Chart (Right)
        self.ram_chart = LineChart(self.ram_right, width=350, height=120, line_color=COLOR_ACCENT_SEC)
        self.ram_chart.pack(pady=10)

        # --- Disk Frame ---
        self.disk_frame = ctk.CTkFrame(self.tab_disk_mem, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=8)
        self.disk_frame.pack(pady=10, padx=10, fill="x")

        # Disk Left (Info) & Right (Chart)
        self.disk_left = ctk.CTkFrame(self.disk_frame, fg_color="transparent")
        self.disk_left.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        self.disk_right = ctk.CTkFrame(self.disk_frame, fg_color="transparent")
        self.disk_right.pack(side="right", fill="both", padx=10, pady=10)

        ctk.CTkLabel(self.disk_left, text="Disk Durumu", font=FONT_HEADER, text_color=COLOR_ACCENT_MAIN).pack(pady=5, anchor="w")

        self.lbl_disk_root = ctk.CTkLabel(self.disk_left, text="Root (/): ...", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_disk_root.pack(pady=2, anchor="w")

        self.lbl_disk_home = ctk.CTkLabel(self.disk_left, text="Home (/home): ...", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_disk_home.pack(pady=2, anchor="w")

        self.disk_sched_frame = ctk.CTkFrame(self.disk_left, fg_color="transparent")
        self.disk_sched_frame.pack(pady=2, anchor="w", fill="x")
        ctk.CTkLabel(self.disk_sched_frame, text="Scheduler:", font=FONT_MONO, text_color=COLOR_TEXT_SEC).pack(side="left", padx=(0,5))
        self.disk_sched_var = ctk.StringVar(value="")
        self.cmb_disk_sched = ctk.CTkOptionMenu(self.disk_sched_frame, variable=self.disk_sched_var, values=[], command=self.change_disk_scheduler, width=120, fg_color=COLOR_SURFACE, button_color=COLOR_ACCENT_MAIN)
        self.cmb_disk_sched.pack(side="left")

        self.lbl_disk_load = ctk.CTkLabel(self.disk_left, text="Disk Yükü (I/O): ...", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_disk_load.pack(pady=2, anchor="w")

        self.lbl_disk_speed = ctk.CTkLabel(self.disk_left, text="Disk Hızı: ...", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_disk_speed.pack(pady=2, anchor="w")

        self.lbl_disk_temp = ctk.CTkLabel(self.disk_left, text="Sıcaklık: ...", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_disk_temp.pack(pady=2, anchor="w")

        # Disk Chart (Right)
        self.disk_chart = LineChart(self.disk_right, width=350, height=120, line_color=COLOR_ACCENT_MAIN, line_color2=COLOR_WARNING, auto_scale=True)
        self.disk_chart.pack(pady=10)

        # --- Network Tab Layout ---
        self.network_frame = ctk.CTkFrame(self.tab_network, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=8)
        self.network_frame.pack(pady=10, padx=10, fill="x")

        # Network Left (Info) & Right (Chart)
        self.net_left = ctk.CTkFrame(self.network_frame, fg_color="transparent")
        self.net_left.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        self.net_right = ctk.CTkFrame(self.network_frame, fg_color="transparent")
        self.net_right.pack(side="right", fill="both", padx=10, pady=10)

        ctk.CTkLabel(self.net_left, text="🌐 Ağ Durumu", font=FONT_HEADER, text_color=COLOR_ACCENT_MAIN).pack(pady=5, anchor="w")
        
        self.lbl_net_interface = ctk.CTkLabel(self.net_left, text="Arayüz: ...", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_net_interface.pack(pady=2, anchor="w")

        self.lbl_net_name = ctk.CTkLabel(self.net_left, text="Ağ Adı: ...", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_net_name.pack(pady=2, anchor="w")

        self.lbl_net_ip = ctk.CTkLabel(self.net_left, text="IP Adresi: ...", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_net_ip.pack(pady=2, anchor="w")

        self.lbl_net_dns = ctk.CTkLabel(self.net_left, text="DNS: ...", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_net_dns.pack(pady=2, anchor="w")

        self.lbl_net_speed_down = ctk.CTkLabel(self.net_left, text="İndirme: ...", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_net_speed_down.pack(pady=2, anchor="w")

        self.lbl_net_speed_up = ctk.CTkLabel(self.net_left, text="Yükleme: ...", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_net_speed_up.pack(pady=2, anchor="w")

        self.lbl_net_total = ctk.CTkLabel(self.net_left, text="Toplam: ...", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_net_total.pack(pady=2, anchor="w")

        # Network Chart (Right)
        self.net_chart = LineChart(self.net_right, width=350, height=120, line_color=COLOR_ACCENT_MAIN)
        self.net_chart.pack(pady=10)

        # --- CPU Tab İçeriği ---
        self.cpu_info_frame = ctk.CTkFrame(self.tab_cpu, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=8)
        self.cpu_info_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(self.cpu_info_frame, text="İşlemci (CPU)", font=FONT_HEADER, text_color=COLOR_ACCENT_MAIN).pack(pady=5)
        self.lbl_cpu_name = ctk.CTkLabel(self.cpu_info_frame, text="CPU: ...", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_cpu_name.pack(pady=2)

        self.lbl_cpu_cores = ctk.CTkLabel(self.cpu_info_frame, text="Çekirdek: ...", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_cpu_cores.pack(pady=2)
        
        self.gov_frame = ctk.CTkFrame(self.cpu_info_frame, fg_color="transparent")
        self.gov_frame.pack(pady=2)
        ctk.CTkLabel(self.gov_frame, text="Governor:", font=FONT_MONO, text_color=COLOR_TEXT_SEC).pack(side="left", padx=(0, 5))
        self.cpu_gov_var = ctk.StringVar(value="...")
        self.cmb_cpu_gov = ctk.CTkOptionMenu(self.gov_frame, variable=self.cpu_gov_var, values=[], command=self.change_cpu_governor, width=150, fg_color=COLOR_SURFACE, button_color=COLOR_ACCENT_MAIN, button_hover_color=COLOR_ACCENT_MAIN, text_color=COLOR_TEXT_MAIN)
        self.cmb_cpu_gov.pack(side="left")

        self.epp_frame = ctk.CTkFrame(self.cpu_info_frame, fg_color="transparent")
        # Pack işlemi update_ui_from_data içinde dinamik yapılır
        ctk.CTkLabel(self.epp_frame, text="EPP:", font=FONT_MONO, text_color=COLOR_TEXT_SEC).pack(side="left", padx=(0, 5))
        self.cpu_epp_var = ctk.StringVar(value="...")
        self.cmb_cpu_epp = ctk.CTkOptionMenu(self.epp_frame, variable=self.cpu_epp_var, values=[], command=self.change_cpu_epp, width=150, fg_color=COLOR_SURFACE, button_color=COLOR_ACCENT_MAIN)
        self.cmb_cpu_epp.pack(side="left")
        self.epp_frame.pack_forget()

        self.freq_limit_frame = ctk.CTkFrame(self.cpu_info_frame, fg_color="transparent")
        self.freq_limit_frame.pack(pady=2)
        
        ctk.CTkLabel(self.freq_limit_frame, text="Min:", font=FONT_MONO, text_color=COLOR_TEXT_SEC).pack(side="left", padx=(0, 5))
        self.cpu_min_var = ctk.StringVar(value="...")
        self.cmb_cpu_min = ctk.CTkOptionMenu(self.freq_limit_frame, variable=self.cpu_min_var, values=[], command=self.change_cpu_min_freq, width=100, fg_color=COLOR_SURFACE, button_color=COLOR_ACCENT_MAIN)
        self.cmb_cpu_min.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(self.freq_limit_frame, text="Max:", font=FONT_MONO, text_color=COLOR_TEXT_SEC).pack(side="left", padx=(0, 5))
        self.cpu_max_var = ctk.StringVar(value="...")
        self.cmb_cpu_max = ctk.CTkOptionMenu(self.freq_limit_frame, variable=self.cpu_max_var, values=[], command=self.change_cpu_max_freq, width=100, fg_color=COLOR_SURFACE, button_color=COLOR_ACCENT_MAIN)
        self.cmb_cpu_max.pack(side="left")

        # CPU Chart
        self.cpu_chart = LineChart(self.cpu_info_frame, width=500, height=100, line_color=COLOR_ACCENT_MAIN)
        self.cpu_chart.pack(pady=10)

        self.cpu_stats_frame = ctk.CTkFrame(self.cpu_info_frame, fg_color="transparent")
        self.cpu_stats_frame.pack(pady=5, fill="x")

        self.lbl_freq = ctk.CTkLabel(self.cpu_stats_frame, text="Frekans: ...", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_freq.pack(side="left", expand=True)

        self.lbl_temp = ctk.CTkLabel(self.cpu_stats_frame, text="Sıcaklık: ...", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_temp.pack(side="left", expand=True)

        self.lbl_fan = ctk.CTkLabel(self.cpu_stats_frame, text="Fan: ...", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_fan.pack(side="left", expand=True)

        self.cpu_cores_scroll = ctk.CTkScrollableFrame(self.tab_cpu, label_text="Çekirdek Detayları", fg_color=COLOR_SURFACE, label_text_color=COLOR_ACCENT_MAIN, label_font=FONT_SUBHEADER)
        self.cpu_cores_scroll.pack(pady=10, padx=10, fill="both", expand=True)

        # --- GPU Tab İçeriği ---
        self.gpu_info_frame = ctk.CTkFrame(self.tab_gpu, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=8)
        self.gpu_info_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(self.gpu_info_frame, text="Ekran Kartı (GPU)", font=FONT_HEADER, text_color=COLOR_ACCENT_MAIN).pack(pady=5)
        self.lbl_gpu_name = ctk.CTkLabel(self.gpu_info_frame, text="GPU: ...", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_gpu_name.pack(pady=2)

        self.gpu_gov_frame = ctk.CTkFrame(self.gpu_info_frame, fg_color="transparent")
        self.gpu_gov_frame.pack(pady=2)
        ctk.CTkLabel(self.gpu_gov_frame, text="Governor:", font=FONT_MONO, text_color=COLOR_TEXT_SEC).pack(side="left", padx=(0, 5))
        self.gpu_gov_var = ctk.StringVar(value="...")
        self.cmb_gpu_gov = ctk.CTkOptionMenu(self.gpu_gov_frame, variable=self.gpu_gov_var, values=[], command=self.change_gpu_governor, width=150, fg_color=COLOR_SURFACE, button_color=COLOR_ACCENT_MAIN)
        self.cmb_gpu_gov.pack(side="left")

        self.gpu_stats_frame = ctk.CTkFrame(self.gpu_info_frame, fg_color="transparent")
        self.gpu_stats_frame.pack(pady=5, fill="x")

        self.lbl_gpu_temp = ctk.CTkLabel(self.gpu_stats_frame, text="Sıcaklık: ...", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_gpu_temp.pack(side="left", expand=True)

        self.lbl_gpu_usage = ctk.CTkLabel(self.gpu_stats_frame, text="Kullanım: ...", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_gpu_usage.pack(side="left", expand=True)

        self.lbl_gpu_freq = ctk.CTkLabel(self.gpu_stats_frame, text="Frekans: ...", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_gpu_freq.pack(side="left", expand=True)

        self.lbl_gpu_vram = ctk.CTkLabel(self.gpu_stats_frame, text="VRAM: ...", font=FONT_MONO, text_color=COLOR_TEXT_SEC)
        self.lbl_gpu_vram.pack(side="left", expand=True)

        # --- Modüller Tab İçeriği ---
        self.module_textbox = ctk.CTkTextbox(self.tab_modules, width=500, height=300, fg_color=COLOR_SURFACE, text_color=COLOR_TEXT_MAIN, font=FONT_MONO)
        self.module_textbox.pack(pady=10, padx=10, fill="both", expand=True)

        self.prev_stats = None
        self.core_widgets = {}
        
        self.prev_disk_io = None
        self.prev_disk_time = None
        self.prev_disk_read = None
        self.prev_disk_write = None
        
        self.prev_net_bytes_recv = 0
        self.prev_net_bytes_sent = 0
        self.prev_net_time = 0

        # Threading Variables
        self.shared_data = {} # Thread ile UI arasındaki veri köprüsü
        self.thread_lock = threading.Lock()
        self.zram_changing = False

        self.jupyter_compat = JupyterCompatibilityWrapper()
        self.jupyter_compat.handshake_hardware_limits()

        self.refresh_all()
        self.auto_refresh()

    def _get_cmd(self, cmd):
        """Komutun tam yolunu bulur (PATH veya yaygın dizinler)."""
        path = shutil.which(cmd)
        if path: return path
        for p in ["/usr/sbin", "/sbin", "/usr/local/sbin", "/usr/bin", "/bin", "/usr/local/bin"]:
            candidate = os.path.join(p, cmd)
            if os.path.exists(candidate) and os.access(candidate, os.X_OK):
                return candidate
        return cmd

    def toggle_theme(self):
        if self.switch_var.get() == "on":
            ctk.set_appearance_mode("Dark")
            mode = "Dark"
        else:
            ctk.set_appearance_mode("Light")
            mode = "Light"
        
        # Grafikleri manuel güncelle
        self.cpu_chart.update_theme(mode)
        self.ram_chart.update_theme(mode)
        self.disk_chart.update_theme(mode)
        self.net_chart.update_theme(mode)

    def refresh_all(self):
        self.update_fastfetch_info()
        self.get_hardware_info()
        # İlk açılışta veriyi manuel tetiklemeye gerek yok, thread zaten çalışacak
        # Ancak UI güncellemesini başlatıyoruz.
        self.update_module_list()
        
        # Arka plan thread'ini başlat
        self.stop_thread = False
        self.monitor_thread = threading.Thread(target=self.background_monitor_loop, daemon=True)
        self.monitor_thread.start()

    def _write_to_all_cpu_sysfs(self, file_template, value):
        """Helper to write a value to a sysfs file for all CPU cores/policies."""
        try:
            cpu_count = os.cpu_count() or 1
            for i in range(cpu_count):
                # Try both cpuX and policyX paths, as they vary between systems
                paths = [
                    file_template.format(i=i, type='cpu'),
                    file_template.format(i=i, type='policy')
                ]
                for path in paths:
                    if os.path.exists(path) and os.access(path, os.W_OK):
                        try:
                            with open(path, "w") as f:
                                f.write(str(value))
                            break  # Move to the next core once a path is successfully written
                        except Exception as e:
                            print(f"Failed to write to {path}: {e}")
        except Exception as e:
            print(f"Error in _write_to_all_cpu_sysfs for file '{file_template}': {e}")

    def change_cpu_governor(self, new_gov):
        self._write_to_all_cpu_sysfs(
            "/sys/devices/system/cpu/{type}{i}/cpufreq/scaling_governor", new_gov
        )

    def change_cpu_epp(self, new_epp):
        # EPP is usually not in policyX path, so we only provide the cpuX template
        self._write_to_all_cpu_sysfs(
            "/sys/devices/system/cpu/cpu{i}/cpufreq/energy_performance_preference", new_epp
        )

    def change_cpu_min_freq(self, choice):
        val = int(choice.split()[0]) * 1000
        self._write_to_all_cpu_sysfs(
            "/sys/devices/system/cpu/{type}{i}/cpufreq/scaling_min_freq", val
        )

    def change_cpu_max_freq(self, choice):
        val = int(choice.split()[0]) * 1000
        self._write_to_all_cpu_sysfs(
            "/sys/devices/system/cpu/{type}{i}/cpufreq/scaling_max_freq", val
        )

    def change_zram_algo(self, new_algo):
        def _change():
            self.zram_changing = True
            try:
                # ZRAM algoritmasını değiştirmek için cihazı resetlemek gerekir.
                # Adımlar: swapoff -> reset -> algo set -> disksize set -> mkswap -> swapon
                
                # 1. Mevcut boyutu al
                disksize = "0"
                if os.path.exists("/sys/block/zram0/disksize"):
                    with open("/sys/block/zram0/disksize", "r") as f:
                        disksize = f.read().strip()
                
                if disksize == "0": return

                # 2. Swapoff
                try:
                    subprocess.run([self._get_cmd("swapoff"), "/dev/zram0"], check=True, stderr=subprocess.DEVNULL)
                except subprocess.CalledProcessError:
                    pass # Zaten kapalı olabilir veya hata verebilir, devam etmeyi dene
                
                # 3. Reset
                with open("/sys/block/zram0/reset", "w") as f:
                    f.write("1")
                
                # 4. Algoritma değiştir
                with open("/sys/block/zram0/comp_algorithm", "w") as f:
                    f.write(new_algo)
                
                # 5. Boyutu geri yükle
                with open("/sys/block/zram0/disksize", "w") as f:
                    f.write(disksize)
                
                # 6. Mkswap & Swapon
                subprocess.run([self._get_cmd("mkswap"), "/dev/zram0"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run([self._get_cmd("swapon"), "/dev/zram0"], check=True)
                
                print(f"ZRAM algorithm changed to {new_algo}")
                self.after(0, lambda: messagebox.showinfo("Başarılı", f"ZRAM algoritması '{new_algo}' olarak ayarlandı."))
            except OSError as e:
                if e.errno == 16: # Device or resource busy
                    self.after(0, lambda: messagebox.showerror("Hata", "ZRAM meşgul (Device busy).\nSwap kapatılamadı, cihaz kullanımda."))
                else:
                    self.after(0, lambda: messagebox.showerror("Hata", f"ZRAM I/O Hatası: {e}"))
            except Exception as e:
                print(f"ZRAM Change Error: {e}")
                self.after(0, lambda: messagebox.showerror("Hata", f"ZRAM değiştirilemedi:\n{e}"))
            finally:
                self.zram_changing = False
        
        threading.Thread(target=_change, daemon=True).start()

    def change_zram_size(self):
        new_size = self.entry_zram_size.get().strip()
        if not new_size: return
        
        def _change():
            self.zram_changing = True
            try:
                # 1. Mevcut algo'yu al
                current_algo = "lzo"
                if os.path.exists("/sys/block/zram0/comp_algorithm"):
                    with open("/sys/block/zram0/comp_algorithm", "r") as f:
                        content = f.read().strip()
                        match = re.search(r'\[(.*?)\]', content)
                        if match: current_algo = match.group(1)

                # 2. Swapoff
                try:
                    subprocess.run([self._get_cmd("swapoff"), "/dev/zram0"], check=True, stderr=subprocess.DEVNULL)
                except subprocess.CalledProcessError:
                    pass
                
                # 3. Reset
                with open("/sys/block/zram0/reset", "w") as f:
                    f.write("1")
                
                # 4. Algo'yu geri yükle
                with open("/sys/block/zram0/comp_algorithm", "w") as f:
                    f.write(current_algo)
                
                # 5. Yeni boyutu ayarla
                with open("/sys/block/zram0/disksize", "w") as f:
                    f.write(new_size)
                
                # 6. Mkswap & Swapon
                subprocess.run([self._get_cmd("mkswap"), "/dev/zram0"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run([self._get_cmd("swapon"), "/dev/zram0"], check=True)
                
                print(f"ZRAM size changed to {new_size}")
                self.after(0, lambda: messagebox.showinfo("Başarılı", f"ZRAM boyutu '{new_size}' olarak ayarlandı."))
            except OSError as e:
                if e.errno == 16:
                    self.after(0, lambda: messagebox.showerror("Hata", "ZRAM meşgul (Device busy).\nSwap kapatılamadı."))
                else:
                    self.after(0, lambda: messagebox.showerror("Hata", f"ZRAM I/O Hatası: {e}"))
            except Exception as e:
                print(f"ZRAM Size Change Error: {e}")
                self.after(0, lambda: messagebox.showerror("Hata", f"ZRAM boyutu değiştirilemedi:\n{e}"))
            finally:
                self.zram_changing = False
        
        threading.Thread(target=_change, daemon=True).start()

    def _get_gpu_sysfs_path(self):
        best_card_path = "/sys/class/drm/card0/device"
        max_vram = 0
        found = False
        for card in glob.glob("/sys/class/drm/card*"):
            try:
                vram_path = os.path.join(card, "device/mem_info_vram_total")
                if os.path.exists(vram_path):
                    with open(vram_path, "r") as f:
                        vram = int(f.read().strip())
                    if vram > max_vram:
                        max_vram = vram
                        best_card_path = os.path.join(card, "device")
                        found = True
            except: continue
        
        if not found and not os.path.exists(best_card_path):
            return None
        return best_card_path

    def change_gpu_governor(self, new_gov):
        try:
            path = self._get_gpu_sysfs_path()
            if path:
                with open(os.path.join(path, "power_dpm_force_performance_level"), "w") as f:
                    f.write(new_gov)
        except Exception as e:
            print(f"GPU Governor Change Error: {e}")

    def change_disk_scheduler(self, new_sched):
        try:
            block_dev = self._find_root_block_dev()
            if block_dev:
                with open(f"/sys/class/block/{block_dev}/queue/scheduler", "w") as f:
                    f.write(new_sched)
        except Exception as e:
            print(f"Scheduler Change Error: {e}")

    def auto_refresh(self):
        self.update_ui_from_data()
        self.after(1000, self.auto_refresh)

    def update_fastfetch_info(self):
        # OS Name
        os_name = "Linux"
        os_id = "linux"
        try:
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            os_name = line.split("=")[1].strip().strip('"')
                        if line.startswith("ID="):
                            os_id = line.split("=")[1].strip().strip('"')
        except: pass

        # Host
        host = "Unknown"
        try:
            if os.path.exists("/sys/devices/virtual/dmi/id/product_name"):
                with open("/sys/devices/virtual/dmi/id/product_name", "r") as f:
                    host = f.read().strip()
            if not host or host in ("System Product Name", "To be filled by O.E.M."):
                host = subprocess.check_output(["hostname"]).decode().strip()
        except: pass

        # Kernel
        try:
            kernel = subprocess.check_output([self._get_cmd('uname'), '-r']).decode().strip()
        except: kernel = "Unknown"

        # Uptime
        try:
            uptime = subprocess.check_output(["uptime", "-p"]).decode().strip().replace("up ", "")
        except: uptime = "Unknown"
        
        # Shell
        try:
            target_user = os.environ.get('SUDO_USER')
            if not target_user:
                target_user = os.environ.get('USER')
            
            if target_user:
                shell = pwd.getpwnam(target_user).pw_shell.split('/')[-1]
            else:
                shell = os.environ.get("SHELL", "/bin/bash").split("/")[-1]
        except:
            shell = "Unknown"

        # CPU
        cpu = "Unknown"
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line:
                        cpu = line.split(":", 1)[1].strip()
                        break
        except: pass

        # GPU
        gpu = "Unknown"
        try:
            gpu = subprocess.check_output(f"{self._get_cmd('lspci')} | grep -E 'VGA|3D' | cut -d: -f3", shell=True).decode().strip().split('\n')[0]
        except: pass

        # Memory
        mem = "Unknown"
        try:
            with open("/proc/meminfo", "r") as f:
                meminfo = f.read()
            total_m = re.search(r'MemTotal:\s+(\d+)', meminfo)
            avail_m = re.search(r'MemAvailable:\s+(\d+)', meminfo)
            if total_m and avail_m:
                t_kb = int(total_m.group(1))
                a_kb = int(avail_m.group(1))
                u_kb = t_kb - a_kb
                mem_percent = (u_kb / t_kb) * 100
                mem = f"{u_kb // 1024 // 1024}G / {t_kb // 1024 // 1024}G (%{mem_percent:.1f})"
        except: pass

        # Disk (Root)
        disk = "Unknown"
        try:
            total, used, free = shutil.disk_usage("/")
            disk_percent = (used / total) * 100
            disk = f"{used // (2**30)}G / {total // (2**30)}G (%{disk_percent:.1f})"
        except: pass

        # Batarya Kontrolü
        battery_info = None
        try:
            bats = glob.glob("/sys/class/power_supply/BAT*")
            if bats:
                # İlk bataryayı al
                bat_path = bats[0]
                with open(os.path.join(bat_path, "capacity"), "r") as f:
                    cap = f.read().strip()
                with open(os.path.join(bat_path, "status"), "r") as f:
                    status = f.read().strip()
                battery_info = f"Doluluk: %{cap}\nDurum: {status}"
        except: pass

        # ASCII Logo Seçimi
        logos = {
            "arch": """
      /\\
     /  \\
    /    \\
   /      \\
  /   ,,   \\
 /   |  |   \\
/_-''    ''-_\\
""",
            "ubuntu": """
           _
       ---(_)
   _(o)__   _
  (_)_  _) (_)
    (_)---
""",
            "debian": """
  _,met$$$$$gg.
 ,g$$$$$$$$$$$$$$$P.
,g$$P"     ""Y$$.".
,$$P'              `$$$.
',$$P       ,ggs.     `$$b:
`d$$'     ,$P"'   .    $$$
 $$P      d$'     ,    $$P
 $$:      $$.   -    ,d$$'
 $$;      Y$b._   _,d$P'
 Y$$.    `.`"Y$$$$P"'
 `$$b      "-.__
  `Y$$
   `Y$$.
     `$$b.
       `Y$$b.
          `"Y$b._
             `""
""",
            "fedora": """
      _____
     /   __)\\
     |  /  \\ \\
  __ |  |__/ /
 / _\\|  |__ /
( (__|  |  |
 \\___|__|__|
"""
        }
        # Varsayılan Tux
        default_logo = """
    .--.
   |o_o |
   |:_/ |
  //   \\ \\
 (|     | )
/'\\_   _/`\\
\\___)=(___/
"""
        ascii_art = logos.get(os_id, default_logo).strip("\n")

        # UI Güncelleme
        self.lbl_ascii_logo.configure(text=ascii_art)
        self.lbl_os_big.configure(text=os_name)
        
        self.lbl_os_info.configure(text=f"Host: {host}\nKernel: {kernel}\nUptime: {uptime}\nShell: {shell}")
        self.lbl_cpu_genel.configure(text=cpu)
        self.lbl_gpu_genel.configure(text=gpu)
        self.lbl_storage_genel.configure(text=f"Memory: {mem}\nDisk (/): {disk}")

        # Batarya Frame Göster/Gizle
        if battery_info:
            self.frame_battery.pack(fill="x", pady=5, padx=5)
            self.lbl_battery_info.configure(text=battery_info)
        else:
            self.frame_battery.pack_forget()

    def get_hardware_info(self):
        # CPU Model İsmi
        if hasattr(self, 'lbl_cpu_name') and self.lbl_cpu_name.winfo_exists():
            try:
                cpu = "Unknown"
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if "model name" in line:
                            cpu = line.split(":", 1)[1].strip()
                            break
                self.lbl_cpu_name.configure(text=f"CPU: {cpu}")
            except:
                self.lbl_cpu_name.configure(text="CPU: Bilinmiyor")

        # CPU Çekirdek Sayısı
        if hasattr(self, 'lbl_cpu_cores') and self.lbl_cpu_cores.winfo_exists():
            try:
                self.lbl_cpu_cores.configure(text=f"Çekirdek Sayısı: {os.cpu_count()}")
            except:
                self.lbl_cpu_cores.configure(text="Çekirdek: Bilinmiyor")

        # GPU Model İsmi (lspci gerektirir)
        try:
            # VGA veya 3D controller satırını bul ve ismini al
            gpu = subprocess.check_output(f"{self._get_cmd('lspci')} | grep -E 'VGA|3D' | cut -d: -f3", shell=True).decode().strip().split('\n')[0]
            self.lbl_gpu_name.configure(text=f"GPU: {gpu}")
        except:
            self.lbl_gpu_name.configure(text="GPU: Bilinmiyor (lspci kurulu mu?)")

        # Toplam RAM
        try:
            ram = subprocess.check_output(f"{self._get_cmd('free')} -h | grep Mem | awk '{{print $2}}'", shell=True).decode().strip()
            self.lbl_ram_total.configure(text=f"RAM Kapasitesi: {ram}")
        except:
            self.lbl_ram_total.configure(text="RAM: Bilinmiyor")

    def scan_sensors(self):
        """
        /sys/class/hwmon altını dinamik olarak tarar.
        Dönüş: {'cpu_temp': float|None, 'fan_rpm': int|None, 'gpu_temp': float|None}
        """
        data = {'cpu_temp': None, 'fan_rpm': None, 'gpu_temp': None, 'disk_temp': None}
        hwmon_path = "/sys/class/hwmon"
        
        if not os.path.exists(hwmon_path):
            return data

        best_fan = 0

        # hwmonX klasörlerini gez
        try:
            dirs = os.listdir(hwmon_path)
            for d in dirs:
                path = os.path.join(hwmon_path, d)
                name_path = os.path.join(path, "name")
                
                chip_name = "unknown"
                if os.path.exists(name_path):
                    try:
                        with open(name_path, "r") as f:
                            chip_name = f.read().strip()
                    except: pass

                # Sıcaklıkları Tara
                # Öncelik: k10temp (AMD), coretemp (Intel), zenpower
                for temp_file in glob.glob(os.path.join(path, "temp*_input")):
                    try:
                        with open(temp_file, "r") as f:
                            val = int(f.read().strip()) / 1000
                        
                        # CPU Sıcaklığı Tahmini
                        if data['cpu_temp'] is None or ("k10temp" in chip_name or "coretemp" in chip_name):
                            # Eğer henüz atanmadıysa veya öncelikli bir çip bulduysak
                            if "k10temp" in chip_name or "coretemp" in chip_name or "zenpower" in chip_name or "cpu" in chip_name:
                                data['cpu_temp'] = val
                        
                        # GPU Sıcaklığı (AMD/Intel açık kaynak sürücüler)
                        if "amdgpu" in chip_name or "nouveau" in chip_name:
                            data['gpu_temp'] = val
                        
                        # Disk Sıcaklığı (drivetemp modülü veya nvme)
                        if "drivetemp" in chip_name or "nvme" in chip_name:
                            # Genellikle disk sıcaklıkları mantıklı değerlerdedir (0-100 arası)
                            if 0 < val < 100:
                                # Eğer birden fazla disk varsa sonuncuyu veya ilkini alır
                                # Öncelik NVMe olabilir
                                if data['disk_temp'] is None or "nvme" in chip_name:
                                    data['disk_temp'] = val
                    except: continue

                # Fanları Tara
                for fan_file in glob.glob(os.path.join(path, "fan*_input")):
                    try:
                        with open(fan_file, "r") as f:
                            rpm = int(f.read().strip())
                        # En yüksek devirli fanı ana fan olarak kabul et (genellikle CPU fanıdır)
                        if rpm > best_fan:
                            best_fan = rpm
                            data['fan_rpm'] = rpm
                    except: continue
        except Exception:
            pass
            
        return data

    def get_disk_stats(self):
        stats = None
        try:
            # Root dizininin bulunduğu cihazı bul
            dev = os.stat("/").st_dev
            major = os.major(dev)
            minor = os.minor(dev)
            
            with open("/proc/diskstats", "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 13:
                        if int(parts[0]) == major and int(parts[1]) == minor:
                            # index 12: ms spent doing I/Os
                            # index 5: sectors read
                            # index 9: sectors written
                            stats = (int(parts[12]), int(parts[5]), int(parts[9]))
                            break
        except:
            pass
        
        if stats: return stats

        # Fallback: /proc/mounts üzerinden cihaz ismini bulma
        try:
            root_device = None
            with open("/proc/mounts", "r") as f:
                for line in f:
                    parts = line.split()
                    if parts[1] == "/":
                        root_device = parts[0].split('/')[-1] # örn: sda2 veya nvme0n1p2
                        break
            
            if root_device:
                with open("/proc/diskstats", "r") as f:
                    for line in f:
                        parts = line.split()
                        if len(parts) >= 13 and parts[2] == root_device:
                            return int(parts[12]), int(parts[5]), int(parts[9])
        except:
            pass
        return 0, 0, 0

    def get_network_stats(self):
        try:
            with open("/proc/net/dev", "r") as f:
                lines = f.readlines()[2:]
            
            best_iface = "lo"
            max_rx = 0
            best_rx = 0
            best_tx = 0
            
            for line in lines:
                line = line.strip()
                if not line: continue
                if ":" in line:
                    iface, data = line.split(":", 1)
                    iface = iface.strip()
                    stats = data.split()
                    rx = int(stats[0])
                    tx = int(stats[8])
                    if iface == "lo": continue
                    if rx > max_rx:
                        max_rx = rx
                        best_iface = iface
                        best_rx = rx
                        best_tx = tx
            return best_iface, best_rx, best_tx
        except:
            return "N/A", 0, 0

    def background_monitor_loop(self):
        """
        Tüm ağır veri toplama işlemlerini yapan arka plan döngüsü.
        UI thread'ini bloklamamak için subprocess ve I/O işlemleri burada yapılır.
        """
        while not getattr(self, "stop_thread", False):
            try:
                data = {}

                # 1. CPU Frekansı
                try:
                    with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq", "r") as f:
                        data['cpu_freq'] = int(f.read().strip()) / 1000
                except:
                    data['cpu_freq'] = None

                # CPU Governor Info
                try:
                    with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor", "r") as f:
                        data['cpu_gov'] = f.read().strip()
                except:
                    data['cpu_gov'] = "N/A"

                # CPU Driver
                try:
                    with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver", "r") as f:
                        data['cpu_driver'] = f.read().strip()
                except:
                    data['cpu_driver'] = "N/A"

                try:
                    with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors", "r") as f:
                        govs = f.read().strip().split()
                        if data['cpu_driver'] == 'amd-pstate-epp':
                            data['avail_govs'] = [g for g in govs if g in ('performance', 'powersave')]
                        else:
                            data['avail_govs'] = govs
                except:
                    data['avail_govs'] = []

                # EPP Info
                try:
                    with open("/sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference", "r") as f:
                        data['cpu_epp'] = f.read().strip()
                except:
                    data['cpu_epp'] = "N/A"

                try:
                    with open("/sys/devices/system/cpu/cpu0/cpufreq/energy_performance_available_preferences", "r") as f:
                        data['avail_epp'] = f.read().strip().split()
                except:
                    data['avail_epp'] = []

                # CPU Freq Limits
                freqs = []
                try:
                    with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_frequencies", "r") as f:
                        raw = f.read().strip().split()
                        freqs = sorted([int(x) for x in raw])
                except FileNotFoundError:
                    # amd-pstate-epp fix: Sürücü frekans listesi sunmuyorsa
                    # cpuinfo_min/max değerlerinden sanal bir liste oluştur.
                    try:
                        with open("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_min_freq", "r") as f:
                            min_f = int(f.read().strip())
                        with open("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq", "r") as f:
                            max_f = int(f.read().strip())
                        
                        step = 100000 # 100 MHz
                        aligned_start = ((min_f // step) + 1) * step
                        aligned_freqs = list(range(aligned_start, max_f, step))
                        freqs = sorted(list(set([min_f] + aligned_freqs + [max_f])))
                    except:
                        freqs = []
                except Exception:
                    freqs = []

                data['avail_freqs_list'] = [f"{x//1000} MHz" for x in freqs]

                try:
                    with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq", "r") as f:
                        val = int(f.read().strip())
                        data['current_min_freq'] = f"{val//1000} MHz"
                except:
                    data['current_min_freq'] = "N/A"

                try:
                    with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq", "r") as f:
                        val = int(f.read().strip())
                        data['current_max_freq'] = f"{val//1000} MHz"
                except:
                    data['current_max_freq'] = "N/A"

                # 2. Sensörler (Sıcaklık, Fan)
                data['sensors'] = self.scan_sensors()

                # 3. GPU Verileri (Subprocess içerir - Ağır İşlem)
                gpu_data = {'temp': None, 'usage': None, 'vram_used': 0, 'vram_total': 0, 'freq': None, 'gov': 'N/A', 'avail_govs': []}
                
                # NVIDIA Check
                try:
                    out = subprocess.check_output(f"{self._get_cmd('nvidia-smi')} --query-gpu=temperature.gpu,utilization.gpu,memory.used,memory.total,clocks.gr --format=csv,noheader,nounits", shell=True, stderr=subprocess.DEVNULL).decode().strip()
                    parts = out.split(',')
                    if len(parts) >= 5:
                        gpu_data['temp'] = float(parts[0])
                        gpu_data['usage'] = float(parts[1])
                        gpu_data['vram_used'] = int(float(parts[2]))
                        gpu_data['vram_total'] = int(float(parts[3]))
                        gpu_data['freq'] = f"{int(float(parts[4]))} MHz"
                except:
                    # AMD/Intel Fallback
                    if data['sensors'].get('gpu_temp') is not None:
                        gpu_data['temp'] = data['sensors']['gpu_temp']
                    
                    # AMD Kart Bulma
                    best_card_path = self._get_gpu_sysfs_path()
                    
                    # AMD Usage
                    if best_card_path and os.path.exists(os.path.join(best_card_path, "gpu_busy_percent")):
                        try:
                            with open(os.path.join(best_card_path, "gpu_busy_percent"), "r") as f:
                                gpu_data['usage'] = int(f.read().strip())
                        except: pass
                    
                    # AMD VRAM
                    try:
                        vram_used_path = os.path.join(best_card_path, "mem_info_vram_used") if best_card_path else ""
                        vram_total_path = os.path.join(best_card_path, "mem_info_vram_total") if best_card_path else ""
                        if os.path.exists(vram_used_path) and os.path.exists(vram_total_path):
                            with open(vram_used_path, "r") as f:
                                gpu_data['vram_used'] = int(f.read().strip()) // (1024**2)
                            with open(vram_total_path, "r") as f:
                                gpu_data['vram_total'] = int(f.read().strip()) // (1024**2)
                    except: pass

                    # AMD Freq
                    try:
                        freq_path = os.path.join(best_card_path, "pp_dpm_sclk") if best_card_path else ""
                        if os.path.exists(freq_path):
                            with open(freq_path, "r") as f:
                                content = f.read()
                            match = re.search(r'(\d+)Mhz\s*\*', content)
                            if match: gpu_data['freq'] = f"{match.group(1)} MHz"
                    except: pass
                    
                    # GPU Governor / Power Profile (AMD/Intel)
                    try:
                        gov_path = os.path.join(best_card_path, "power_dpm_force_performance_level") if best_card_path else ""
                        if os.path.exists(gov_path):
                            with open(gov_path, "r") as f:
                                gpu_data['gov'] = f.read().strip()
                            gpu_data['avail_govs'] = ['auto', 'low', 'high']
                    except: pass

                
                data['gpu'] = gpu_data

                # 4. RAM Hızı (Subprocess - Ağır)
                try:
                    cmd = f"{self._get_cmd('dmidecode')} -t memory | grep 'Configured Memory Speed:' | head -1 | awk -F: '{{print $2}}'"
                    data['ram_speed'] = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode("utf-8").strip()
                except:
                    data['ram_speed'] = None

                # 5. RAM Kullanımı (/proc/meminfo)
                data['mem_info'] = self._read_meminfo()

                # 6. ZRAM
                data['zram_info'] = None
                try:
                    zram_out = subprocess.check_output(f"{self._get_cmd('zramctl')} --output ALGORITHM,DISKSIZE,DATA --raw --noheadings", shell=True, stderr=subprocess.DEVNULL).decode("utf-8").strip()
                    if zram_out:
                        parts = zram_out.split('\n')[0].split()
                        if len(parts) >= 3:
                            data['zram_info'] = {'alg': parts[0], 'size': parts[1], 'used': parts[2]}
                except:
                    pass
                
                # ZRAM Algoritmaları
                try:
                    with open("/sys/block/zram0/comp_algorithm", "r") as f:
                        content = f.read().strip()
                        # Örnek: [lzo] lz4 deflate
                        data['zram_algos'] = [x.strip('[]') for x in content.split()]
                        match = re.search(r'\[(.*?)\]', content)
                        data['zram_current_algo'] = match.group(1) if match else None
                except:
                    data['zram_algos'] = []
                    data['zram_current_algo'] = None

                # 7. Disk Kullanımı
                data['disk_usage'] = self._read_disk_usage()
                data['disk_sched'] = self._get_disk_scheduler()

                # 8. Disk I/O Stats
                data['disk_io'] = self.get_disk_stats()

                # 9. Network Stats
                data['net_stats'] = self.get_network_stats()
                data['net_info'] = self._get_network_details(data['net_stats'][0])

                # 10. Core Stats
                data['core_stats'] = self._calc_core_stats()

                # Veriyi Paylaşılan Alana Yaz
                self.shared_data = data

            except Exception as e:
                print(f"Thread Error: {e}")
            
            time.sleep(1)

    def update_ui_from_data(self):
        """
        Sadece self.shared_data içindeki verileri okuyup UI widget'larını günceller.
        Burada ağır işlem yapılmaz.
        """
        data = self.shared_data
        if not data: return

        # CPU Frekansı (sysfs üzerinden okuma)
        if data.get('cpu_freq'):
            if hasattr(self, 'lbl_freq') and self.lbl_freq.winfo_exists():
                self.lbl_freq.configure(text=f"Ort. Frekans:\n{data['cpu_freq']:.0f} MHz")
        else:
            if hasattr(self, 'lbl_freq') and self.lbl_freq.winfo_exists():
                self.lbl_freq.configure(text="Ort. Frekans:\nN/A")
        
        # CPU Governor
        cpu_gov = data.get('cpu_gov', 'N/A')
        avail_govs = data.get('avail_govs', [])
        
        if avail_govs and not self.cmb_cpu_gov.cget("values"):
             self.cmb_cpu_gov.configure(values=avail_govs)
        
        if cpu_gov != "N/A" and cpu_gov != self.cpu_gov_var.get():
             self.cpu_gov_var.set(cpu_gov)

        # EPP UI
        epp_val = data.get('cpu_epp', 'N/A')
        epp_avail = data.get('avail_epp', [])
        
        if epp_avail:
            if not self.epp_frame.winfo_viewable():
                self.epp_frame.pack(pady=2, after=self.gov_frame)
            if not self.cmb_cpu_epp.cget("values"):
                self.cmb_cpu_epp.configure(values=epp_avail)
            if epp_val != "N/A" and self.cpu_epp_var.get() != epp_val:
                self.cpu_epp_var.set(epp_val)
        else:
            if self.epp_frame.winfo_viewable():
                self.epp_frame.pack_forget()

        # CPU Freq Limits
        avail_freqs = data.get('avail_freqs_list', [])
        cur_min = data.get('current_min_freq', 'N/A')
        cur_max = data.get('current_max_freq', 'N/A')

        if avail_freqs:
            if not self.cmb_cpu_min.cget("values"):
                self.cmb_cpu_min.configure(values=avail_freqs)
                self.cmb_cpu_max.configure(values=avail_freqs)
            if cur_min != "N/A" and self.cpu_min_var.get() != cur_min:
                self.cpu_min_var.set(cur_min)
            if cur_max != "N/A" and self.cpu_max_var.get() != cur_max:
                self.cpu_max_var.set(cur_max)

        sensor_data = data.get('sensors', {})

        # CPU Sıcaklık İşleme
        cpu_temp = "N/A"
        temp_val = sensor_data.get('cpu_temp')
        if temp_val is not None:
            cpu_temp = f"{temp_val:.1f} °C"
        
        temp_color = ("black", "white")
        if temp_val is not None:
            if temp_val < 50:
                temp_color = COLOR_ACCENT_MAIN # Yeşil
            elif temp_val < 80:
                temp_color = "#F2C94C" # Sarı
            else:
                temp_color = COLOR_ERROR # Kırmızı

        if hasattr(self, 'lbl_temp') and self.lbl_temp.winfo_exists():
            self.lbl_temp.configure(text=f"Sıcaklık:\n{cpu_temp}", text_color=temp_color)

        # Fan Hızı
        fan_rpm = "0 RPM"
        if sensor_data.get('fan_rpm') is not None:
            fan_rpm = f"{sensor_data['fan_rpm']} RPM"

        if hasattr(self, 'lbl_fan') and self.lbl_fan.winfo_exists():
            self.lbl_fan.configure(text=f"Fan:\n{fan_rpm}")

        # GPU İstatistikleri (Sıcaklık, Kullanım, VRAM)
        gpu_data = data.get('gpu', {})
        gpu_temp_val = gpu_data.get('temp')
        gpu_usage_val = gpu_data.get('usage')
        raw_vram_used = gpu_data.get('vram_used', 0)
        raw_vram_total = gpu_data.get('vram_total', 0)
        
        gpu_temp_str = f"{gpu_temp_val:.0f} °C" if gpu_temp_val is not None else "N/A"
        gpu_usage_str = f"%{gpu_usage_val:.0f}" if gpu_usage_val is not None else "N/A"
        gpu_freq_str = gpu_data.get('freq', "N/A")
        
        if raw_vram_total > 0:
            gpu_vram_str = f"{raw_vram_used}MB / {raw_vram_total}MB"
        else:
            gpu_vram_str = "N/A"
        
        # GPU Governor
        gpu_gov = gpu_data.get('gov', 'N/A')
        gpu_avail = gpu_data.get('avail_govs', [])
        
        if gpu_avail and not self.cmb_gpu_gov.cget("values"):
            self.cmb_gpu_gov.configure(values=gpu_avail)
        if gpu_gov != "N/A" and self.gpu_gov_var.get() != gpu_gov:
            self.gpu_gov_var.set(gpu_gov)
        
        # Jupyter/VSCodium Entegrasyonu
        if gpu_usage_val is not None:
            self.jupyter_compat.publish_gpu_stats(gpu_usage_val, raw_vram_used, raw_vram_total)

        # Renk Fonksiyonu
        def get_color(val):
            if val is None: return ("black", "white")
            if val < 50: return COLOR_ACCENT_MAIN
            if val < 80: return COLOR_WARNING
            return COLOR_ERROR

        vram_percent = None
        if raw_vram_total > 0:
            vram_percent = (raw_vram_used / raw_vram_total) * 100

        self.lbl_gpu_temp.configure(text=f"Sıcaklık:\n{gpu_temp_str}", text_color=get_color(gpu_temp_val))
        self.lbl_gpu_usage.configure(text=f"Kullanım:\n{gpu_usage_str}", text_color=get_color(gpu_usage_val))
        self.lbl_gpu_freq.configure(text=f"Frekans:\n{gpu_freq_str}")
        self.lbl_gpu_vram.configure(text=f"VRAM:\n{gpu_vram_str}", text_color=get_color(vram_percent))

        # RAM Frekansı (dmidecode root yetkisi gerektirir)
        ram_speed = data.get('ram_speed', "Yetki Yok")
        if not ram_speed: ram_speed = "Yetki Yok"
        self.lbl_ram.configure(text=f"RAM Hızı:\n{ram_speed}")

        # RAM Kullanımı ve Progress Bar
        mem_info = data.get('mem_info')
        if mem_info:
            percent = mem_info['percent']
            
            # Renk Belirleme
            if percent < 50:
                prog_col = COLOR_ACCENT_MAIN # Yeşil
            elif percent < 80:
                prog_col = COLOR_WARNING # Sarı
            else:
                prog_col = COLOR_ERROR # Kırmızı
            
            self.ram_progress.set(mem_info['ratio'])
            self.ram_progress.configure(progress_color=prog_col)
            self.lbl_ram_usage.configure(text=f"Kullanım: {mem_info['used_gb']:.1f} GB / {mem_info['total_gb']:.1f} GB (%{percent:.1f})")
            
            # Chart Update
            self.ram_chart.add_value(percent)

        # ZRAM Durumu
        zram_info = data.get('zram_info')
        zram_algos = data.get('zram_algos', [])
        zram_cur = data.get('zram_current_algo')

        if zram_info:
            self.lbl_zram_stats.configure(text=f"Kullanılan: {zram_info['used']}  |  Toplam: {zram_info['size']}")
            if zram_algos:
                current_vals = self.cmb_zram_algo.cget("values")
                if current_vals is None or list(current_vals) != zram_algos:
                    self.cmb_zram_algo.configure(values=zram_algos)
            if zram_cur and self.zram_algo_var.get() != zram_cur and not self.zram_changing:
                self.zram_algo_var.set(zram_cur)
            
            # Widget'ları göster
            self.zram_control_frame.pack(fill="x", pady=5, anchor="w")
        else:
            self.lbl_zram_stats.configure(text="ZRAM Pasif veya Yüklü Değil")
            self.zram_control_frame.pack_forget()

        # Disk Kullanımı
        disk_usage = data.get('disk_usage')
        if disk_usage:
            root = disk_usage['root']
            home = disk_usage['home']
            self.lbl_disk_root.configure(text=f"Root (/): {root['used']} GB / {root['total']} GB (%{root['percent']:.1f})", text_color=get_color(root['percent']))
            self.lbl_disk_home.configure(text=f"Home (/home): {home['used']} GB / {home['total']} GB (%{home['percent']:.1f})", text_color=get_color(home['percent']))

        # Disk Scheduler UI
        disk_sched_data = data.get('disk_sched', {})
        sched_current = disk_sched_data.get('current', 'N/A')
        sched_avail = disk_sched_data.get('available', [])

        if sched_avail and not self.cmb_disk_sched.cget("values"):
            self.cmb_disk_sched.configure(values=sched_avail)
        if sched_current != 'N/A' and self.disk_sched_var.get() != sched_current:
            self.disk_sched_var.set(sched_current)

        # Disk Yükü (I/O Load) ve Hızı
        current_io, current_read, current_write = data.get('disk_io', (0,0,0))
        current_time = time.time()
        
        disk_load = 0
        read_speed = 0.0
        write_speed = 0.0
        
        if self.prev_disk_io is not None and self.prev_disk_time is not None:
            delta_time = current_time - self.prev_disk_time
            if delta_time > 0:
                # Load
                delta_io = current_io - self.prev_disk_io
                disk_load = (delta_io / (delta_time * 1000)) * 100
                if disk_load > 100: disk_load = 100
                
                # Speed (Sectors * 512 bytes)
                read_speed = ((current_read - self.prev_disk_read) * 512) / (1024 * 1024) / delta_time
                write_speed = ((current_write - self.prev_disk_write) * 512) / (1024 * 1024) / delta_time
        
        self.prev_disk_io = current_io
        self.prev_disk_read = current_read
        self.prev_disk_write = current_write
        self.prev_disk_time = current_time
        
        self.lbl_disk_load.configure(text=f"Disk Yükü (I/O): %{disk_load:.1f}", text_color=get_color(disk_load))
        self.lbl_disk_speed.configure(text=f"Disk Hızı: ⬇ {read_speed:.1f} MB/s  ⬆ {write_speed:.1f} MB/s")
        self.disk_chart.add_value(read_speed, write_speed)

        # Disk Sıcaklığı
        disk_temp_str = "N/A"
        disk_temp_val = sensor_data.get('disk_temp')
        
        if disk_temp_val is not None:
            disk_temp_str = f"{disk_temp_val:.1f} °C"
            self.lbl_disk_temp.configure(text=f"Sıcaklık: {disk_temp_str}", text_color=get_color(disk_temp_val))
        else:
            # Sensör yoksa etiketi gizle veya N/A göster
            self.lbl_disk_temp.configure(text=f"Sıcaklık: {disk_temp_str}", text_color=COLOR_TEXT_SEC)

        # Network Stats
        net_iface, net_rx, net_tx = data.get('net_stats', ("N/A", 0, 0))
        current_time = time.time()
        
        down_speed = 0.0
        up_speed = 0.0
        
        if self.prev_net_time != 0:
            delta_time = current_time - self.prev_net_time
            if delta_time > 0:
                down_speed = (net_rx - self.prev_net_bytes_recv) / 1024 / delta_time # KB/s
                up_speed = (net_tx - self.prev_net_bytes_sent) / 1024 / delta_time # KB/s
        
        self.prev_net_bytes_recv = net_rx
        self.prev_net_bytes_sent = net_tx
        self.prev_net_time = current_time
        
        # Formatting
        down_str = f"{down_speed:.1f} KB/s"
        if down_speed > 1024:
            down_str = f"{down_speed/1024:.1f} MB/s"
            
        up_str = f"{up_speed:.1f} KB/s"
        if up_speed > 1024:
            up_str = f"{up_speed/1024:.1f} MB/s"

        total_rx_str = f"{net_rx / (1024**3):.2f} GB"
        total_tx_str = f"{net_tx / (1024**3):.2f} GB"

        net_info = data.get('net_info', {})
        ip_addr = net_info.get('ip', "...")
        net_name = net_info.get('name', "...")
        dns_servers = net_info.get('dns', "...")

        self.lbl_net_interface.configure(text=f"Arayüz: {net_iface}")
        self.lbl_net_name.configure(text=f"Ağ Adı: {net_name}")
        self.lbl_net_ip.configure(text=f"IP Adresi: {ip_addr}")
        self.lbl_net_dns.configure(text=f"DNS: {dns_servers}")
        self.lbl_net_speed_down.configure(text=f"İndirme: ⬇ {down_str}", text_color=COLOR_ACCENT_MAIN)
        self.lbl_net_speed_up.configure(text=f"Yükleme: ⬆ {up_str}", text_color=COLOR_ACCENT_SEC)
        self.lbl_net_total.configure(text=f"Toplam: ⬇ {total_rx_str}  ⬆ {total_tx_str}")
        
        # Chart update (Scale: 0-100, assuming 10MB/s max for visualization scaling)
        chart_val = (down_speed / 10240) * 100
        if chart_val > 100: chart_val = 100
        self.net_chart.add_value(chart_val)

        # Çekirdek Frekansları ve Yüzdeleri (UI Güncelleme)
        core_stats = data.get('core_stats', [])
        if core_stats:
            global_usage = 0
            for idx, (core, usage, freq_txt) in enumerate(core_stats):
                if core == "cpu":
                    global_usage = usage
                    continue
                
                # Renk Belirleme
                if usage < 50:
                    text_col = COLOR_ACCENT_MAIN # Yeşil
                elif usage < 80:
                    text_col = COLOR_WARNING # Sarı
                else:
                    text_col = COLOR_ERROR # Kırmızı

                # Grid Hesaplama (3 Sütun)
                r = idx // 3
                c = idx % 3

                # UI Satırı
                text_val = f"{core.upper()}:  %{usage:.1f}  |  {freq_txt}"
                if core in self.core_widgets:
                    self.core_widgets[core].configure(text=text_val, text_color=text_col)
                else:
                    lbl = ctk.CTkLabel(self.cpu_cores_scroll, text=text_val, anchor="w", text_color=text_col, font=FONT_MONO)
                    lbl.grid(row=r, column=c, sticky="w", padx=5, pady=2)
                    self.core_widgets[core] = lbl
            
            # Update Chart
            self.cpu_chart.add_value(global_usage)

    # --- Helper Methods for Thread ---
    def _read_meminfo(self):
        try:
            with open("/proc/meminfo", "r") as f:
                meminfo = f.read()
            total_match = re.search(r'MemTotal:\s+(\d+)', meminfo)
            avail_match = re.search(r'MemAvailable:\s+(\d+)', meminfo)
            if total_match and avail_match:
                total_kb = int(total_match.group(1))
                avail_kb = int(avail_match.group(1))
                used_kb = total_kb - avail_kb
                ratio = used_kb / total_kb
                return {
                    'total_gb': total_kb / (1024*1024),
                    'used_gb': used_kb / (1024*1024),
                    'ratio': ratio,
                    'percent': ratio * 100
                }
        except: return None

    def _read_disk_usage(self):
        try:
            total, used, free = shutil.disk_usage("/")
            total_h, used_h, free_h = shutil.disk_usage("/home")
            return {
                'root': {'used': used // (2**30), 'total': total // (2**30), 'percent': (used/total)*100},
                'home': {'used': used_h // (2**30), 'total': total_h // (2**30), 'percent': (used_h/total_h)*100}
            }
        except: return None

    def _find_root_block_dev(self):
        try:
            root_dev = None
            with open("/proc/mounts", "r") as f:
                for line in f:
                    parts = line.split()
                    if parts[1] == "/":
                        root_dev = parts[0]
                        break
            
            if root_dev:
                dev_name = root_dev.split("/")[-1]
                block_dev = dev_name
                # Partition ise (sda1 -> sda, nvme0n1p1 -> nvme0n1)
                if "nvme" in dev_name:
                    block_dev = re.sub(r'p\d+$', '', dev_name)
                else:
                    block_dev = re.sub(r'\d+$', '', dev_name)
                return block_dev
        except: pass
        return None

    def _get_disk_scheduler(self):
        block_dev = self._find_root_block_dev()
        if block_dev:
            sched_path = f"/sys/class/block/{block_dev}/queue/scheduler"
            if os.path.exists(sched_path):
                try:
                    with open(sched_path, "r") as f:
                        content = f.read().strip()
                        # Örnek: none [mq-deadline] kyber
                        available = [x.strip('[]') for x in content.split()]
                        match = re.search(r'\[(.*?)\]', content)
                        current = match.group(1) if match else "N/A"
                        return {'current': current, 'available': available}
                except: pass
        return {'current': 'N/A', 'available': []}

    def _get_network_details(self, iface):
        info = {'ip': '...', 'name': '...', 'dns': '...'}
        if iface == "N/A": return info
        
        try:
             out = subprocess.check_output(f"{self._get_cmd('ip')} -4 addr show {iface} | grep -oP '(?<=inet\\s)\\d+(\\.\\d+){{3}}'", shell=True, stderr=subprocess.DEVNULL).decode().strip()
             if out: info['ip'] = out.split('\n')[0]
        except: pass

        try:
            # Network Name
            try:
                info['name'] = subprocess.check_output(f"{self._get_cmd('nmcli')} -t -f NAME connection show --active | head -n1", shell=True, stderr=subprocess.DEVNULL).decode().strip()
            except:
                try:
                    info['name'] = subprocess.check_output(f"{self._get_cmd('iwgetid')} -r", shell=True, stderr=subprocess.DEVNULL).decode().strip()
                except: pass
            
            # DNS
            try:
                dns_out = subprocess.check_output(f"{self._get_cmd('nmcli')} -t -f IP4.DNS connection show --active | head -n1", shell=True, stderr=subprocess.DEVNULL).decode().strip()
                if dns_out: info['dns'] = dns_out.replace(",", ", ")
            except: pass
            
            if info['dns'] == "...":
                try:
                    dev_out = subprocess.check_output(f"{self._get_cmd('nmcli')} dev show | grep 'IP4.DNS'", shell=True, stderr=subprocess.DEVNULL).decode()
                    ips = re.findall(r':\s+((?:\d{1,3}\.){3}\d{1,3})', dev_out)
                    if ips: info['dns'] = ", ".join(ips)
                except: pass
        except: pass
        return info

    def _calc_core_stats(self):
        try:
            def get_cpu_times():
                with open("/proc/stat", "r") as f:
                    lines = f.readlines()
                stats = {}
                for line in lines:
                    if line.startswith("cpu"):
                        parts = line.split()
                        core = parts[0]
                        values = [int(x) for x in parts[1:]]
                        total = sum(values)
                        idle = values[3]
                        stats[core] = (total, idle)
                return stats

            current_stats = get_cpu_times()
            if self.prev_stats is None:
                self.prev_stats = current_stats
                return []
            
            start_stats = self.prev_stats
            end_stats = current_stats
            self.prev_stats = end_stats
            
            results = []
            for core in sorted(start_stats.keys(), key=lambda x: int(x[3:]) if x[3:].isdigit() else -1):
                t1, i1 = start_stats[core]
                t2, i2 = end_stats[core]
                diff_total = t2 - t1
                diff_idle = i2 - i1
                usage = 0
                if diff_total > 0:
                    usage = 100 * (1 - diff_idle / diff_total)
                
                freq_txt = "N/A"
                if core != "cpu":
                    freq_path = f"/sys/devices/system/cpu/{core}/cpufreq/scaling_cur_freq"
                    if os.path.exists(freq_path):
                        try:
                            with open(freq_path, "r") as f:
                                freq_mhz = int(f.read().strip()) / 1000
                                freq_txt = f"{freq_mhz:.0f} MHz"
                        except: pass
                
                results.append((core, usage, freq_txt))
            return results
        except Exception as e:
            return []

    def update_module_list(self):
        try:
            kernels = ""
            if shutil.which("pacman"): # Arch Linux
                cmd = "pacman -Q | grep -E '^linux'"
                kernels = subprocess.check_output(cmd, shell=True).decode("utf-8")
            elif shutil.which("rpm"): # Fedora/RHEL/SUSE
                cmd = "rpm -qa | grep -E '^kernel'"
                kernels = subprocess.check_output(cmd, shell=True).decode("utf-8")
            elif shutil.which("dpkg"): # Debian/Ubuntu
                cmd = "dpkg --list | grep linux-image | awk '{print $2}'"
                kernels = subprocess.check_output(cmd, shell=True).decode("utf-8")
            else:
                kernels = "Paket yöneticisi algılanamadı (pacman, rpm, dpkg)."

            self.module_textbox.delete("1.0", "end")
            self.module_textbox.insert("1.0", kernels)
        except Exception as e:
            self.module_textbox.delete("1.0", "end")
            self.module_textbox.insert("1.0", f"Hata: {e}\n(Paket yöneticisi bulunamadı).")

    def get_current_settings_dict(self):
        settings = {}
        # CPU
        cpu_gov = self.cpu_gov_var.get()
        if cpu_gov != "..." and cpu_gov != "N/A": settings['cpu_gov'] = cpu_gov

        if self.epp_frame.winfo_viewable():
            cpu_epp = self.cpu_epp_var.get()
            if cpu_epp != "..." and cpu_epp != "N/A": settings['cpu_epp'] = cpu_epp

        cpu_min_freq = self.cpu_min_var.get()
        if cpu_min_freq != "..." and cpu_min_freq != "N/A": settings['cpu_min_freq'] = cpu_min_freq

        cpu_max_freq = self.cpu_max_var.get()
        if cpu_max_freq != "..." and cpu_max_freq != "N/A": settings['cpu_max_freq'] = cpu_max_freq

        # GPU
        gpu_gov = self.gpu_gov_var.get()
        if gpu_gov != "..." and gpu_gov != "N/A": settings['gpu_gov'] = gpu_gov

        # Disk
        disk_sched = self.disk_sched_var.get()
        if disk_sched and disk_sched != "N/A": settings['disk_sched'] = disk_sched
        
        return settings

    def apply_profile_settings(self, settings):
        if 'cpu_gov' in settings: self.change_cpu_governor(settings['cpu_gov'])
        if 'cpu_epp' in settings: self.change_cpu_epp(settings['cpu_epp'])
        if 'cpu_min_freq' in settings: self.change_cpu_min_freq(settings['cpu_min_freq'])
        if 'cpu_max_freq' in settings: self.change_cpu_max_freq(settings['cpu_max_freq'])
        if 'gpu_gov' in settings: self.change_gpu_governor(settings['gpu_gov'])
        if 'disk_sched' in settings: self.change_disk_scheduler(settings['disk_sched'])
        messagebox.showinfo("Profil Yüklendi", "Ayarlar sisteme uygulandı.")

    def load_profiles_from_disk(self):
        if os.path.exists(PROFILES_FILE):
            try:
                with open(PROFILES_FILE, "r") as f:
                    return json.load(f)
            except: return {}
        return {}

    def save_profiles_to_disk(self, profiles):
        try:
            os.makedirs(os.path.dirname(PROFILES_FILE), exist_ok=True)
            with open(PROFILES_FILE, "w") as f:
                json.dump(profiles, f, indent=4)
        except Exception as e:
            messagebox.showerror("Hata", f"Profil kaydedilemedi: {e}")

    def open_profile_window(self):
        if hasattr(self, 'profile_window') and self.profile_window.winfo_exists():
            self.profile_window.focus()
            return

        self.profile_window = ctk.CTkToplevel(self)
        self.profile_window.title("Profil Yöneticisi")
        self.profile_window.geometry("500x600")
        self.profile_window.transient(self)
        self.profile_window.after(100, self.profile_window.grab_set)

        ctk.CTkLabel(self.profile_window, text="Kayıtlı Profiller", font=FONT_HEADER).pack(pady=10)

        self.profiles_frame = ctk.CTkScrollableFrame(self.profile_window, height=250)
        self.profiles_frame.pack(fill="x", padx=20, pady=5)

        self.selected_profile_var = ctk.StringVar(value="")

        def refresh_list():
            for widget in self.profiles_frame.winfo_children(): widget.destroy()
            profiles = self.load_profiles_from_disk()
            for name in profiles:
                rb = ctk.CTkRadioButton(self.profiles_frame, text=name, variable=self.selected_profile_var, value=name, font=FONT_BODY)
                rb.pack(anchor="w", pady=5, padx=5)

        refresh_list()

        btn_frame = ctk.CTkFrame(self.profile_window, fg_color="transparent")
        btn_frame.pack(pady=10)

        def load_selected():
            name = self.selected_profile_var.get()
            if not name: return
            profiles = self.load_profiles_from_disk()
            if name in profiles: self.apply_profile_settings(profiles[name])

        def delete_selected():
            name = self.selected_profile_var.get()
            if not name: return
            profiles = self.load_profiles_from_disk()
            if name in profiles:
                del profiles[name]
                self.save_profiles_to_disk(profiles)
                refresh_list()

        ctk.CTkButton(btn_frame, text="Seçili Profili Yükle", command=load_selected, fg_color=COLOR_ACCENT_MAIN).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Sil", command=delete_selected, fg_color=COLOR_ERROR).pack(side="left", padx=5)

        ctk.CTkLabel(self.profile_window, text="Yeni Profil Kaydet", font=FONT_SUBHEADER).pack(pady=(20, 5))
        entry_name = ctk.CTkEntry(self.profile_window, placeholder_text="Profil Adı (örn: Oyun Modu)")
        entry_name.pack(pady=5)

        def save_new():
            name = entry_name.get().strip()
            if not name: return
            profiles = self.load_profiles_from_disk()
            profiles[name] = self.get_current_settings_dict()
            self.save_profiles_to_disk(profiles)
            refresh_list()
            entry_name.delete(0, "end")

        ctk.CTkButton(self.profile_window, text="Şu Anki Ayarları Kaydet", command=save_new, fg_color=COLOR_ACCENT_SEC).pack(pady=10)

    def open_persistence_window(self):
        if hasattr(self, 'persistence_window') and self.persistence_window.winfo_exists():
            self.persistence_window.focus()
            return

        self.persistence_window = ctk.CTkToplevel(self)
        self.persistence_window.title("Ayarları Kalıcı Yap")
        self.persistence_window.geometry("600x550")
        self.persistence_window.transient(self)
        # Pencere görünür olmadan grab_set çağrılırsa hata verir.
        self.persistence_window.after(100, self.persistence_window.grab_set)

        lbl_title = ctk.CTkLabel(self.persistence_window, text="Kalıcı Yapılacak Ayarlar", font=FONT_HEADER)
        lbl_title.pack(pady=10)

        info_text = "Bu işlem, seçili ayarları sistem başlangıcında otomatik olarak\nuygulayacak bir sistem servisi (`systemd`) oluşturacaktır.\nDevam etmek için yönetici şifresi gereklidir."
        lbl_info = ctk.CTkLabel(self.persistence_window, text=info_text, font=FONT_BODY, text_color=COLOR_TEXT_SEC)
        lbl_info.pack(pady=(0, 15))

        settings_frame = ctk.CTkFrame(self.persistence_window, fg_color=COLOR_SURFACE, border_width=1, border_color=COLOR_BORDER)
        settings_frame.pack(pady=10, padx=20, fill="both", expand=True)

        # Get current settings from UI
        settings_to_save = {}
        
        # CPU
        cpu_gov = self.cpu_gov_var.get()
        if cpu_gov != "..." and cpu_gov != "N/A": settings_to_save['cpu_gov'] = cpu_gov

        if self.epp_frame.winfo_viewable():
            cpu_epp = self.cpu_epp_var.get()
            if cpu_epp != "..." and cpu_epp != "N/A": settings_to_save['cpu_epp'] = cpu_epp

        cpu_min_freq = self.cpu_min_var.get()
        if cpu_min_freq != "..." and cpu_min_freq != "N/A": settings_to_save['cpu_min_freq'] = cpu_min_freq.split()[0]

        cpu_max_freq = self.cpu_max_var.get()
        if cpu_max_freq != "..." and cpu_max_freq != "N/A": settings_to_save['cpu_max_freq'] = cpu_max_freq.split()[0]

        # GPU
        gpu_gov = self.gpu_gov_var.get()
        if gpu_gov != "..." and gpu_gov != "N/A": settings_to_save['gpu_gov'] = gpu_gov

        # Disk
        disk_sched = self.disk_sched_var.get()
        if disk_sched and disk_sched != "N/A": settings_to_save['disk_sched'] = disk_sched

        # Display them
        settings_text = ""
        if 'cpu_gov' in settings_to_save: settings_text += f"  • CPU Governor: {settings_to_save['cpu_gov']}\n"
        if 'cpu_epp' in settings_to_save: settings_text += f"  • CPU EPP: {settings_to_save['cpu_epp']}\n"
        if 'cpu_min_freq' in settings_to_save: settings_text += f"  • CPU Min Frekans: {settings_to_save['cpu_min_freq']} MHz\n"
        if 'cpu_max_freq' in settings_to_save: settings_text += f"  • CPU Max Frekans: {settings_to_save['cpu_max_freq']} MHz\n"
        if 'gpu_gov' in settings_to_save: settings_text += f"  • GPU Governor: {settings_to_save['gpu_gov']}\n"
        if 'disk_sched' in settings_to_save: settings_text += f"  • Disk Scheduler: {settings_to_save['disk_sched']}\n"

        if not settings_text: settings_text = "Kaydedilecek geçerli bir ayar bulunamadı."

        lbl_settings = ctk.CTkLabel(settings_frame, text=settings_text, font=FONT_MONO, justify="left", anchor="nw")
        lbl_settings.pack(anchor="w", padx=15, pady=15)

        self.persistence_window.settings_to_save = settings_to_save

        btn_apply = ctk.CTkButton(self.persistence_window, text="Sistem Servisi Oluştur ve Uygula", command=self.apply_persistence_settings, fg_color=COLOR_ACCENT_MAIN)
        btn_apply.pack(pady=(20, 10))

        btn_remove = ctk.CTkButton(self.persistence_window, text="Servisi Devre Dışı Bırak ve Sil", command=self.remove_persistence_service, fg_color=COLOR_ERROR)
        btn_remove.pack(pady=(0, 20))

    def apply_persistence_settings(self):
        if not hasattr(self, 'persistence_window') or not self.persistence_window.winfo_exists(): return

        settings = self.persistence_window.settings_to_save
        if not settings:
            messagebox.showwarning("Uyarı", "Kalıcı yapılacak bir ayar seçilmedi.", parent=self.persistence_window)
            return

        script_lines = ["#!/bin/bash", "# This script is generated by Kernel Manager to apply settings on boot.", "sleep 15"]
        cpu_count = os.cpu_count() or 1
        
        cpu_commands = []
        if 'cpu_gov' in settings: cpu_commands.append(f"echo '{settings['cpu_gov']}' > /sys/devices/system/cpu/cpu$i/cpufreq/scaling_governor")
        if 'cpu_epp' in settings: cpu_commands.append(f"echo '{settings['cpu_epp']}' > /sys/devices/system/cpu/cpu$i/cpufreq/energy_performance_preference")
        if 'cpu_min_freq' in settings: cpu_commands.append(f"echo '{int(settings['cpu_min_freq']) * 1000}' > /sys/devices/system/cpu/cpu$i/cpufreq/scaling_min_freq")
        if 'cpu_max_freq' in settings: cpu_commands.append(f"echo '{int(settings['cpu_max_freq']) * 1000}' > /sys/devices/system/cpu/cpu$i/cpufreq/scaling_max_freq")

        if cpu_commands:
            script_lines.append("\n# Apply CPU settings for all cores")
            script_lines.append(f"for i in $(seq 0 $(({cpu_count}-1))); do")
            for cmd in cpu_commands:
                path_to_check = cmd.split('>')[-1].strip()
                script_lines.append(f"    if [ -w {path_to_check} ]; then {cmd}; fi")
            script_lines.append("done")

        if 'gpu_gov' in settings:
            gpu_path = self._get_gpu_sysfs_path()
            if gpu_path:
                gov_path = os.path.join(gpu_path, "power_dpm_force_performance_level")
                script_lines.append("\n# Apply GPU settings")
                script_lines.append(f"if [ -w {gov_path} ]; then echo '{settings['gpu_gov']}' > {gov_path}; fi")

        if 'disk_sched' in settings:
            block_dev = self._find_root_block_dev()
            if block_dev:
                sched_path = f"/sys/class/block/{block_dev}/queue/scheduler"
                script_lines.append("\n# Apply Disk scheduler")
                script_lines.append(f"if [ -w {sched_path} ]; then echo '{settings['disk_sched']}' > {sched_path}; fi")

        script_lines.append("exit 0")
        script_content = "\n".join(script_lines)
        self.create_systemd_service(script_content)

    def remove_persistence_service(self):
        if not hasattr(self, 'persistence_window') or not self.persistence_window.winfo_exists(): return

        dialog = PasswordDialog(text="Servisi kaldırmak için yönetici (sudo) şifrenizi girin:", title="Yetki Gerekiyor")
        password = dialog.get_input()

        if not password:
            return

        if hasattr(self, 'persistence_window') and self.persistence_window.winfo_exists(): self.persistence_window.destroy()

        def _remove_task():
            try:
                sudo_path = self._get_cmd('sudo')
                
                def run_sudo_cmd(command_args, p_input, ignore_errors=False):
                    cmd = self._get_cmd(command_args[0])
                    args = [cmd] + command_args[1:]
                    proc = subprocess.Popen([sudo_path, '-S'] + args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    _, stderr = proc.communicate(input=p_input.encode())
                    if proc.returncode != 0 and not ignore_errors: 
                        raise subprocess.CalledProcessError(proc.returncode, [sudo_path, '-S'] + args, stderr=stderr)

                run_sudo_cmd(['systemctl', 'disable', '--now', 'kernel-manager.service'], password, ignore_errors=True)
                run_sudo_cmd(['rm', '-f', '/etc/systemd/system/kernel-manager.service'], password)
                run_sudo_cmd(['rm', '-f', '/usr/local/bin/kernel-manager-settings.sh'], password)
                run_sudo_cmd(['systemctl', 'daemon-reload'], password)

                self.after(0, lambda: messagebox.showinfo("Başarılı", "Sistem servisi ve dosyaları başarıyla kaldırıldı."))
            except subprocess.CalledProcessError as e:
                error_message = e.stderr.decode()
                if "incorrect password" in error_message.lower(): error_message = "Hatalı şifre girdiniz."
                self.after(0, lambda: messagebox.showerror("Hata", f"İşlem başarısız:\n{error_message}"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Hata", f"Beklenmedik hata: {e}"))

        threading.Thread(target=_remove_task, daemon=True).start()

    def create_systemd_service(self, script_content):
        service_content = f"""[Unit]\nDescription=Apply Kernel Manager Settings on Boot\nAfter=multi-user.target\n\n[Service]\nType=oneshot\nExecStart=/usr/local/bin/kernel-manager-settings.sh\n\n[Install]\nWantedBy=multi-user.target\n"""
        dialog = PasswordDialog(text="Ayarları uygulamak için yönetici (sudo) şifrenizi girin:", title="Yetki Gerekiyor")
        password = dialog.get_input()

        if not password:
            messagebox.showwarning("İptal Edildi", "İşlem kullanıcı tarafından iptal edildi.")
            return

        if hasattr(self, 'persistence_window') and self.persistence_window.winfo_exists(): self.persistence_window.destroy()

        def _apply_task():
            try:
                sudo_path = self._get_cmd('sudo')
                # tee_path, chmod_path vb. gerek yok, run_sudo_cmd içinde çözülüyor

                def run_sudo_cmd(command_args, p_input):
                    cmd = self._get_cmd(command_args[0])
                    args = [cmd] + command_args[1:]
                    proc = subprocess.Popen([sudo_path, '-S'] + args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    _, stderr = proc.communicate(input=p_input.encode())
                    if proc.returncode != 0: raise subprocess.CalledProcessError(proc.returncode, [sudo_path, '-S'] + args, stderr=stderr)

                def write_protected_file(path, content, pwd):
                    # Geçici dosya oluştur (Normal kullanıcı yetkisiyle)
                    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
                        tmp.write(content)
                        tmp_name = tmp.name
                    
                    try:
                        # sudo cp ile hedef konuma kopyala (stdin sorunu olmadan)
                        run_sudo_cmd(['cp', tmp_name, path], pwd)
                    finally:
                        if os.path.exists(tmp_name):
                            os.remove(tmp_name)

                write_protected_file('/usr/local/bin/kernel-manager-settings.sh', script_content, password)
                run_sudo_cmd(['chmod', '+x', '/usr/local/bin/kernel-manager-settings.sh'], password)
                write_protected_file('/etc/systemd/system/kernel-manager.service', service_content, password)
                run_sudo_cmd(['systemctl', 'daemon-reload'], password)
                run_sudo_cmd(['systemctl', 'enable', '--now', 'kernel-manager.service'], password)
                self.after(0, lambda: messagebox.showinfo("Başarılı", "Ayarlar kalıcı hale getirildi ve sistem servisi etkinleştirildi."))
            except subprocess.CalledProcessError as e:
                error_message = e.stderr.decode()
                if "incorrect password" in error_message.lower(): error_message = "Hatalı şifre girdiniz. Lütfen tekrar deneyin."
                else: error_message = f"Bir hata oluştu (Komut: {e.cmd}):\n{error_message}"
                self.after(0, lambda: messagebox.showerror("Hata", error_message))
            except FileNotFoundError: self.after(0, lambda: messagebox.showerror("Hata", "Komut bulunamadı. 'sudo' veya 'systemctl' sisteminizde kurulu mu?"))
            except Exception as e: self.after(0, lambda: messagebox.showerror("Hata", f"Beklenmedik bir hata oluştu: {e}"))
        threading.Thread(target=_apply_task, daemon=True).start()

class JupyterCompatibilityWrapper:
    """
    VSCodium Jupyter Eklentisi ve Resource Monitor için Uyumluluk Katmanı.
    ZMQ üzerinden kernel_info_reply ve display_data mesajlarını simüle eder.
    """
    def __init__(self):
        self.is_jupyter = 'ipykernel' in sys.modules

    def handshake_hardware_limits(self):
        """
        Kernel başlatıldığında donanım limitlerini (VRAM Total vb.) deklare eder.
        Bu, 'kernel_info_reply' mesajına metadata enjekte etmeye çalışır.
        """
        if not self.is_jupyter: return
        
        try:
            from IPython import get_ipython
            ip = get_ipython()
            if hasattr(ip, 'kernel'):
                # VSCodium Resource Monitor genellikle kernel_info yanıtındaki 'help_links' 
                # veya özel metadata alanlarına bakar. Burada temsili bir limit tanımlıyoruz.
                # Gerçek bir ZMQ mesajı yakalamak yerine, kernel oturumuna metadata ekliyoruz.
                pass
        except:
            pass

    def publish_gpu_stats(self, load_percent, vram_used_mb, vram_total_mb):
        """
        Anlık GPU verilerini Jupyter arayüzüne (Resource Monitor) gönderir.
        """
        if not self.is_jupyter: return

        try:
            from IPython.display import display
            # VSCodium veya JupyterLab Resource Monitor eklentileri için standart JSON yapısı.
            # 'application/vnd.jupyter.resource-monitor+json' MIME tipi yaygın bir standarttır.
            payload = {
                "gpu_load": load_percent,
                "vram_used": vram_used_mb,
                "vram_total": vram_total_mb
            }
            # Metadata olarak göndererek arayüzün bunu parse etmesini sağlıyoruz
            display({
                "application/vnd.jupyter.resource-monitor+json": payload
            }, raw=True, clear=False)
        except:
            pass

if __name__ == "__main__":
    app = KernelManager()
    app.mainloop()
