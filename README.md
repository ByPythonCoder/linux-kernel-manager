# Linux Kernel Manager Pro

**Linux Kernel Manager Pro**, Linux çekirdek parametrelerini, CPU/GPU frekanslarını ve güç profillerini yönetmek için geliştirilmiş modern bir grafik arayüz (GUI) aracıdır. `customtkinter` kullanılarak Python ile yazılmıştır.

## 🚀 Özellikler

*   **CPU Yönetimi:**
    *   Frekans ölçekleme (Governor) değiştirme (performance, powersave, schedutil vb.).
    *   EPP (Energy Performance Preference) ayarları.
    *   Min/Max frekans limitlerini belirleme.
    *   Çekirdek bazlı kullanım ve frekans izleme.
*   **GPU Yönetimi:**
    *   Anlık kullanım, sıcaklık ve VRAM takibi.
    *   Güç profili (Governor) değiştirme (NVIDIA, AMD, Intel destekli).
*   **Bellek ve Disk:**
    *   RAM kullanımı ve ZRAM yönetimi (Algoritma ve boyut değiştirme).
    *   Disk I/O scheduler değiştirme (bfq, kyber, mq-deadline vb.).
*   **Kalıcılık:**
    *   Ayarları `systemd` servisi olarak kaydedip her açılışta otomatik uygulama.
*   **Modern Arayüz:**
    *   Cyberpunk temalı, karanlık/aydınlık mod destekli kullanıcı dostu arayüz.

## 📦 Kurulum ve Çalıştırma

### Yöntem 1: Docker (Önerilen)

Sisteminizi kirletmeden en güvenli çalıştırma yöntemidir.

1.  Depoyu klonlayın:
    ```bash
    git clone https://github.com/ByPythonCoder/linux-kernel-manager.git
    cd linux-kernel-manager
    ```

2.  Uygulamayı başlatın:
    ```bash
    # Eğer docker-compose eklentisi yüklüyse:
    docker compose up --build
    ```

### Yöntem 2: Tek Dosya (Binary) Oluşturma

Uygulamayı taşınabilir tek bir dosya haline getirmek için `compile.sh` scriptini kullanabilirsiniz (Docker gerektirir):

```bash
chmod +x compile.sh
./compile.sh
```
Bu işlem sonucunda klasörde `KernelManager` adında çalıştırılabilir bir dosya oluşacaktır.

### Yöntem 3: Manuel Kurulum (Geliştiriciler İçin)

Gerekli sistem paketleri: `python3-tk`, `dmidecode`, `pciutils`, `util-linux`.

```bash
pip install -r requirements.txt
python main.py
```