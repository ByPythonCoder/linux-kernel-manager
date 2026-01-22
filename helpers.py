import shutil
import os

def get_cmd(cmd):
    """Komutun tam yolunu bulur (PATH veya yaygın dizinler)."""
    path = shutil.which(cmd)
    if path: return path
    for p in ["/usr/sbin", "/sbin", "/usr/local/sbin", "/usr/bin", "/bin", "/usr/local/bin"]:
        candidate = os.path.join(p, cmd)
        if os.path.exists(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return cmd