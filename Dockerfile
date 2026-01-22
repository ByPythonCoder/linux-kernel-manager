FROM debian:bookworm-slim

# Gerekli sistem araçlarını kur
# python3-full: Python ve venv/pip
# python3-tk: Arayüz kütüphanesi
RUN apt-get update && apt-get install -y \
    python3-full python3-pip python3-tk tk-dev libx11-6 binutils zlib1g-dev \
    libjpeg-dev patchelf gcc g++ make \
    pciutils dmidecode util-linux network-manager iproute2 procps kmod sudo x11-apps \
    && rm -rf /var/lib/apt/lists/*

# Root şifresi (sudo işlemleri için)
RUN echo "root:root" | chpasswd

WORKDIR /app

# Bağımlılıkları kur
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages nuitka ordered-set zstandard

COPY . .

# Uygulamayı doğrudan başlat
CMD ["python3", "main.py"]
