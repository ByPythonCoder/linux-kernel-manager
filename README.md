Linux Kernel Manager Pro

Linux Kernel Manager Pro is a modern, Cyberpunk-themed Graphical User Interface (GUI) tool designed to monitor and manage Linux kernel parameters, CPU/GPU performance, and system resources in real-time. Built with Python and customtkinter, it provides a powerful yet user-friendly dashboard for Linux enthusiasts and power users.
🚀 Features

    CPU Management:

        Change Frequency Scaling Governors (performance, powersave, schedutil, etc.).

        Fine-tune EPP (Energy Performance Preference) settings.

        Set Min/Max frequency limits.

        Real-time per-core usage and frequency monitoring.

    GPU Management:

        Live tracking of usage, temperature, and VRAM.

        Power profile management for NVIDIA, AMD, and Intel GPUs.

    Memory & Disk Optimization:

        ZRAM management (Algorithm and size configuration).

        Disk I/O scheduler switching (bfq, kyber, mq-deadline, etc.).

        Real-time RAM and Disk I/O monitoring.

    System Persistence:

        Save your optimized settings as a systemd service to apply them automatically on every boot.

    Modern UI/UX:

        Cyberpunk aesthetic with Dark and Light mode support.

        Multilingual support (English & Turkish) via translate.json.

📦 Installation & Usage
Method 1: Docker (Recommended)

This is the safest way to run the application without messing with system dependencies. It uses privileged mode to access host hardware.

    Clone the repository:
    Bash

git clone https://github.com/ByPythonCoder/linux-kernel-manager.git
cd linux-kernel-manager

Run with Docker Compose:
Bash

    docker compose up --build

Method 2: Create a Standalone Binary

You can compile the application into a single portable binary using the provided Nuitka-based script (requires Docker):
Bash

chmod +x compile.sh
./compile.sh

The resulting executable will be named KernelManager.
Method 3: Manual Installation

If you prefer to run it locally, ensure you have the system dependencies (Python, Tkinter, pciutils, etc.) installed:
Bash

pip install -r requirements.txt
python3 main.py

🛠️ Tech Stack

    Language: Python 3

    GUI Framework: customtkinter (based on Tkinter)

    Compilation: Nuitka

    Containerization: Docker & Docker Compose

    System Tools used: pciutils, dmidecode, util-linux, kmod, network-manager

📜 License

This project is licensed under the MIT License. See the LICENSE file for details.

Note: This application requires root/sudo privileges to modify kernel parameters and hardware settings.
