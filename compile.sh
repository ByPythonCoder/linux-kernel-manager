#!/bin/bash

# Hata oluşursa işlemi durdur
set -e

echo "🚀 [1/4] Docker imajı güncelleniyor (Yeni kodlar yükleniyor)..."
docker compose build

echo "🔨 [2/4] Derleme işlemi başlatılıyor (Bu işlem biraz sürebilir)..."
# Docker Compose servisinden doğru imaj ID'sini al
IMAGE_ID=$(docker compose images -q kernel-manager)

if [ -z "$IMAGE_ID" ]; then
    echo "❌ Hata: İmaj bulunamadı. Önce 'docker compose build' çalıştırın."
    exit 1
fi

docker run --rm -v "$PWD:/app/output" $IMAGE_ID python3 -m nuitka \
    --standalone --onefile \
    --enable-plugin=tk-inter \
    --include-package=customtkinter \
    --include-package=PIL \
    --include-data-file=icon.png=icon.png \
    --output-dir=/app/output \
    main.py

echo "📦 [3/4] Dosya izinleri düzenleniyor..."
# Root olarak oluşan dosyanın sahipliğini kullanıcıya ver
sudo chown $USER:$USER main.bin 2>/dev/null || true

# Eski dosyayı sil ve yenisini adlandır
[ -f KernelManager ] && rm KernelManager
[ -f main.bin ] && mv main.bin KernelManager
chmod +x KernelManager

echo "🧹 [4/4] Temizlik yapılıyor..."
sudo rm -rf main.build main.dist main.onefile-build

echo "✅ İşlem tamamlandı! Yeni sürüm hazır: ./KernelManager"