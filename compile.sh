#!/bin/bash

# Hata durumunda işlemi durdur
set -e

# Scriptin bulunduğu dizine geç
cd "$(dirname "$0")"

APP_NAME="Linux_Kernel_Manager"
MAIN_SCRIPT="main.py"

echo "=========================================="
echo "   $APP_NAME Derleme Aracı"
echo "=========================================="

# 1. Sistem Kontrolleri
echo "[1/4] Sistem gereksinimleri kontrol ediliyor..."

PYTHON_CMD=""
# Nuitka kararlılığı için öncelikle desteklenen sürümleri ara (3.13, 3.12, 3.11)
for ver in python3.13 python3.12 python3.11 python3; do
    if command -v $ver &> /dev/null; then
        PYTHON_CMD=$ver
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "Hata: Python 3 yüklü değil."
    exit 1
fi
echo "Kullanılan Python: $PYTHON_CMD"

# Python 3.14 uyarısı
PY_VER=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [ "$PY_VER" == "3.14" ]; then
    echo "⚠️  UYARI: Python 3.14 (Deneysel) tespit edildi."
    echo "   Nuitka bu sürümle kararsız çalışabilir ve 'Segmentation fault' hatası verebilir."
    echo "   Çözüm: 'sudo pacman -S python311' (veya AUR'dan) kurup tekrar deneyin."
fi

# Nuitka Linux standalone build için patchelf gerektirir
if ! command -v patchelf &> /dev/null; then
    echo "Uyarı: 'patchelf' bulunamadı. Bu araç Nuitka standalone derlemesi için gereklidir."
    echo "Lütfen yükleyin: sudo apt install patchelf (Debian/Ubuntu) veya sudo pacman -S patchelf (Arch)"
    read -p "Yine de devam edilsin mi? (e/h): " choice
    [[ "$choice" != "e" && "$choice" != "E" ]] && exit 1
fi

# 2. Sanal Ortam Hazırlığı
echo "[2/4] Sanal ortam (build_venv) hazırlanıyor..."
if [ ! -d "build_venv" ]; then
    $PYTHON_CMD -m venv build_venv
fi

source build_venv/bin/activate

# 3. Bağımlılıkların Yüklenmesi
echo "[3/4] Bağımlılıklar yükleniyor..."
python -m pip install --upgrade pip wheel setuptools packaging
# Proje gereksinimleri
python -m pip install customtkinter pillow
# Derleme aracı
python -m pip install nuitka

# 4. Derleme İşlemi
echo "[4/4] Nuitka ile derleme başlatılıyor..."

# Komut oluşturma
CMD="python -m nuitka"
CMD="$CMD --standalone"              # Bağımsız klasör yapısı
CMD="$CMD --onefile"                 # Tek dosya çıktısı
CMD="$CMD --enable-plugin=tk-inter"  # Tkinter desteği
CMD="$CMD --include-package-data=customtkinter" # CustomTkinter temaları
CMD="$CMD --output-filename=$APP_NAME"
CMD="$CMD --lto=no"                  # Segfault önlemek için LTO kapalı

# Veri dosyalarını ekle
if [ -f "translate.json" ]; then
    CMD="$CMD --include-data-file=translate.json=translate.json"
else
    echo "Hata: translate.json bulunamadı! Dil dosyası eksik."
    exit 1
fi

if [ -f "icon.png" ]; then
    CMD="$CMD --include-data-file=icon.png=icon.png"
else
    echo "Bilgi: icon.png bulunamadı, varsayılan ikon kullanılacak."
fi

# Ana scripti ekle ve çalıştır
$CMD $MAIN_SCRIPT

echo ""
echo "✅ İşlem Tamamlandı!"
echo "Çıktı dosyası: $(pwd)/$APP_NAME"

deactivate