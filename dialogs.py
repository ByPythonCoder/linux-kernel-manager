import customtkinter as ctk
from config import FONT_BODY, COLOR_ACCENT_MAIN, COLOR_ERROR
from translations import TRANSLATIONS

class PasswordDialog(ctk.CTkToplevel):
    def __init__(self, lang="tr", title=None, text=None):
        super().__init__()
        
        # Dil desteği için varsayılanları ayarla
        tr_data = TRANSLATIONS.get(lang, TRANSLATIONS.get("tr", {}))
        if title is None: title = tr_data.get("password_required", "Password Required")
        if text is None: text = tr_data.get("enter_password", "Please enter password:")

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

        self.btn_ok = ctk.CTkButton(self.btn_frame, text=tr_data.get("ok", "OK"), command=self._on_ok, width=100, fg_color=COLOR_ACCENT_MAIN)
        self.btn_ok.pack(side="left", padx=10)

        self.btn_cancel = ctk.CTkButton(self.btn_frame, text=tr_data.get("cancel", "Cancel"), command=self._on_cancel, width=100, fg_color=COLOR_ERROR)
        self.btn_cancel.pack(side="left", padx=10)

    def _on_ok(self, event=None):
        self.password = self.entry.get()
        self.destroy()

    def _on_cancel(self):
        self.destroy()

    def get_input(self):
        self.wait_window()
        return self.password