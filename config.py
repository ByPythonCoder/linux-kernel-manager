import os

# --- Cyberpunk Theme Constants ---
COLOR_BG = ("#F0F2F5", "#121212")
COLOR_SURFACE = ("#FFFFFF", "#1E1E1E")
COLOR_BORDER = ("#D1D5DB", "#333333")
COLOR_ACCENT_MAIN = ("#0056b3", "#00FF41")
COLOR_ACCENT_SEC = ("#0EA5E9", "#00D4FF")
COLOR_ERROR = ("#EF4444", "#FF5F5F")
COLOR_WARNING = ("#F59E0B", "#F2C94C")
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
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".config", "linux_kernel_manager", "config.json")
