import sys
import os
import json

def load_translations():
    try:
        # Dosya yollarını belirle
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        if hasattr(sys, "frozen"):
            # Derlenmiş halde (Nuitka/PyInstaller)
            # Önce exe'nin yanına bak (harici config için), yoksa temp/bundle dizinine (base_path) bak
            exe_dir = os.path.dirname(os.path.abspath(sys.executable))
            if os.path.exists(os.path.join(exe_dir, "translate.json")):
                base_path = exe_dir
        file_path = os.path.join(base_path, "translate.json")
        
        if not os.path.exists(file_path):
             file_path = "translate.json"

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            print(f"Hata: {file_path} bulunamadı!")
    except Exception as e:
        print(f"Translation load error: {e}")
    return {}

TRANSLATIONS = load_translations()