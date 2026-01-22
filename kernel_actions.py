import os
from system_info import find_root_block_dev, get_gpu_sysfs_path

def write_to_all_cpu_sysfs(file_template, value):
    try:
        cpu_count = os.cpu_count() or 1
        for i in range(cpu_count):
            paths = [
                file_template.format(i=i, type='cpu'),
                file_template.format(i=i, type='policy')
            ]
            for path in paths:
                if os.path.exists(path) and os.access(path, os.W_OK):
                    try:
                        with open(path, "w") as f:
                            f.write(str(value))
                        break
                    except Exception as e:
                        print(f"Failed to write to {path}: {e}")
    except Exception as e:
        print(f"Error in write_to_all_cpu_sysfs: {e}")

def set_cpu_governor(new_gov):
    write_to_all_cpu_sysfs("/sys/devices/system/cpu/{type}{i}/cpufreq/scaling_governor", new_gov)

def set_cpu_epp(new_epp):
    write_to_all_cpu_sysfs("/sys/devices/system/cpu/cpu{i}/cpufreq/energy_performance_preference", new_epp)

def set_cpu_min_freq(choice):
    val = int(choice.split()[0]) * 1000
    write_to_all_cpu_sysfs("/sys/devices/system/cpu/{type}{i}/cpufreq/scaling_min_freq", val)

def set_cpu_max_freq(choice):
    val = int(choice.split()[0]) * 1000
    write_to_all_cpu_sysfs("/sys/devices/system/cpu/{type}{i}/cpufreq/scaling_max_freq", val)

def set_gpu_governor(new_gov):
    try:
        path = get_gpu_sysfs_path()
        if path:
            with open(os.path.join(path, "power_dpm_force_performance_level"), "w") as f:
                f.write(new_gov)
    except Exception as e:
        print(f"GPU Governor Change Error: {e}")

def set_disk_scheduler(new_sched):
    try:
        block_dev = find_root_block_dev()
        if block_dev:
            with open(f"/sys/class/block/{block_dev}/queue/scheduler", "w") as f:
                f.write(new_sched)
    except Exception as e:
        print(f"Scheduler Change Error: {e}")