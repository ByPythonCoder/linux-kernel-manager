Linux Kernel Manager Pro

Linux Kernel Manager Pro is a modern Graphical User Interface (GUI) tool developed to manage Linux kernel parameters, CPU/GPU frequencies, and power profiles. It is written in Python using the customtkinter library.
🚀 Features

    CPU Management:

        Change frequency scaling governors (performance, powersave, schedutil, etc.).

        Configure EPP (Energy Performance Preference) settings.

        Set Min/Max frequency limits.

        Core-specific usage and frequency monitoring.

    GPU Management:

        Real-time usage, temperature, and VRAM tracking.

        Power profile (Governor) switching (Supports NVIDIA, AMD, and Intel).

    Memory and Disk:

        RAM usage monitoring and ZRAM management (Change algorithm and size).

        Disk I/O scheduler switching (bfq, kyber, mq-deadline, etc.).

    Persistence:

        Save settings as a systemd service to apply them automatically at every boot.

    Modern Interface:

        User-friendly interface with a Cyberpunk theme and support for dark/light modes.

📦 Installation and Execution
Method 1: Docker (Recommended)

The safest way to run the application without cluttering your system.

    Clone the repository:
    Bash

git clone https://github.com/ByPythonCoder/linux-kernel-manager.git
cd linux-kernel-manager

Launch the application:
Bash

    # If the docker-compose plugin is installed:
    docker compose up --build

Method 2: Create a Single Binary File

You can use the compile.sh script to turn the application into a single portable executable (requires Docker):
Bash

chmod +x compile.sh
./compile.sh

After completion, an executable file named KernelManager will be created in the directory.
Method 3: Manual Installation (For Developers)

Required system packages: python3-tk, dmidecode, pciutils, util-linux.
Bash

pip install -r requirements.txt
python main.py
