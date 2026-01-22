import os
import glob
import re
import shutil
import subprocess
from helpers import get_cmd

def get_gpu_sysfs_path():
    try:
        best_card_path = "/sys/class/drm/card0/device"
        max_vram = 0
        found = False
        for card in glob.glob("/sys/class/drm/card*"):
            try:
                vram_path = os.path.join(card, "device/mem_info_vram_total")
                if os.path.exists(vram_path):
                    with open(vram_path, "r") as f:
                        vram = int(f.read().strip())
                    if vram > max_vram:
                        max_vram = vram
                        best_card_path = os.path.join(card, "device")
                        found = True
            except: continue
        
        if not found and not os.path.exists(best_card_path):
            return None
        return best_card_path
    except Exception:
        return None

def scan_sensors():
    data = {'cpu_temp': None, 'fan_rpm': None, 'gpu_temp': None, 'disk_temp': None}
    hwmon_path = "/sys/class/hwmon"
    
    if not os.path.exists(hwmon_path):
        return data

    best_fan = 0
    try:
        dirs = os.listdir(hwmon_path)
        for d in dirs:
            path = os.path.join(hwmon_path, d)
            name_path = os.path.join(path, "name")
            
            chip_name = "unknown"
            if os.path.exists(name_path):
                try:
                    with open(name_path, "r") as f:
                        chip_name = f.read().strip()
                except: pass

            for temp_file in glob.glob(os.path.join(path, "temp*_input")):
                try:
                    with open(temp_file, "r") as f:
                        val = int(f.read().strip()) / 1000
                    
                    if data['cpu_temp'] is None or ("k10temp" in chip_name or "coretemp" in chip_name):
                        if "k10temp" in chip_name or "coretemp" in chip_name or "zenpower" in chip_name or "cpu" in chip_name:
                            data['cpu_temp'] = val
                    
                    if "amdgpu" in chip_name or "nouveau" in chip_name:
                        data['gpu_temp'] = val
                    
                    if "drivetemp" in chip_name or "nvme" in chip_name:
                        if 0 < val < 100:
                            if data['disk_temp'] is None or "nvme" in chip_name:
                                data['disk_temp'] = val
                except: continue

            for fan_file in glob.glob(os.path.join(path, "fan*_input")):
                try:
                    with open(fan_file, "r") as f:
                        rpm = int(f.read().strip())
                    if rpm > best_fan:
                        best_fan = rpm
                        data['fan_rpm'] = rpm
                except: continue
    except Exception:
        pass
    return data

def get_disk_stats():
    stats = None
    try:
        dev = os.stat("/").st_dev
        major = os.major(dev)
        minor = os.minor(dev)
        
        with open("/proc/diskstats", "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 13:
                    if int(parts[0]) == major and int(parts[1]) == minor:
                        stats = (int(parts[12]), int(parts[5]), int(parts[9]))
                        break
    except: pass
    
    if stats: return stats

    try:
        root_device = None
        with open("/proc/mounts", "r") as f:
            for line in f:
                parts = line.split()
                if parts[1] == "/":
                    root_device = parts[0].split('/')[-1]
                    break
        
        if root_device:
            with open("/proc/diskstats", "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 13 and parts[2] == root_device:
                        return int(parts[12]), int(parts[5]), int(parts[9])
    except: pass
    return 0, 0, 0

def get_network_stats():
    try:
        with open("/proc/net/dev", "r") as f:
            lines = f.readlines()[2:]
        
        best_iface = "lo"
        max_rx = 0
        best_rx = 0
        best_tx = 0
        
        for line in lines:
            line = line.strip()
            if not line: continue
            if ":" in line:
                iface, data = line.split(":", 1)
                iface = iface.strip()
                stats = data.split()
                rx = int(stats[0])
                tx = int(stats[8])
                if iface == "lo": continue
                if rx > max_rx:
                    max_rx = rx
                    best_iface = iface
                    best_rx = rx
                    best_tx = tx
        return best_iface, best_rx, best_tx
    except:
        return "N/A", 0, 0

def read_meminfo():
    try:
        with open("/proc/meminfo", "r") as f:
            meminfo = f.read()
        total_match = re.search(r'MemTotal:\s+(\d+)', meminfo)
        avail_match = re.search(r'MemAvailable:\s+(\d+)', meminfo)
        if total_match and avail_match:
            total_kb = int(total_match.group(1))
            avail_kb = int(avail_match.group(1))
            used_kb = total_kb - avail_kb
            ratio = used_kb / total_kb
            return {
                'total_gb': total_kb / (1024*1024),
                'used_gb': used_kb / (1024*1024),
                'ratio': ratio,
                'percent': ratio * 100
            }
    except: return None

def read_disk_usage():
    try:
        total, used, free = shutil.disk_usage("/")
        total_h, used_h, free_h = shutil.disk_usage("/home")
        return {
            'root': {'used': used // (2**30), 'total': total // (2**30), 'percent': (used/total)*100},
            'home': {'used': used_h // (2**30), 'total': total_h // (2**30), 'percent': (used_h/total_h)*100}
        }
    except: return None

def find_root_block_dev():
    try:
        root_dev = None
        with open("/proc/mounts", "r") as f:
            for line in f:
                parts = line.split()
                if parts[1] == "/":
                    root_dev = parts[0]
                    break
        
        if root_dev:
            dev_name = root_dev.split("/")[-1]
            block_dev = dev_name
            if "nvme" in dev_name:
                block_dev = re.sub(r'p\d+$', '', dev_name)
            else:
                block_dev = re.sub(r'\d+$', '', dev_name)
            return block_dev
    except: pass
    return None

def get_disk_scheduler():
    try:
        block_dev = find_root_block_dev()
        if block_dev:
            sched_path = f"/sys/class/block/{block_dev}/queue/scheduler"
            if os.path.exists(sched_path):
                with open(sched_path, "r") as f:
                    content = f.read().strip()
                    available = [x.strip('[]') for x in content.split()]
                    match = re.search(r'\[(.*?)\]', content)
                    current = match.group(1) if match else "N/A"
                    return {'current': current, 'available': available}
    except: pass
    return {'current': 'N/A', 'available': []}

def get_network_details(iface):
    info = {'ip': '...', 'name': '...', 'dns': '...'}
    if iface == "N/A": return info
    
    try:
            out = subprocess.check_output(f"{get_cmd('ip')} -4 addr show {iface} | grep -oP '(?<=inet\\s)\\d+(\\.\\d+){{3}}'", shell=True, stderr=subprocess.DEVNULL).decode().strip()
            if out: info['ip'] = out.split('\n')[0]
    except: pass

    try:
        try:
            info['name'] = subprocess.check_output(f"{get_cmd('nmcli')} -t -f NAME connection show --active | head -n1", shell=True, stderr=subprocess.DEVNULL).decode().strip()
        except:
            try:
                info['name'] = subprocess.check_output(f"{get_cmd('iwgetid')} -r", shell=True, stderr=subprocess.DEVNULL).decode().strip()
            except: pass
        
        try:
            dns_out = subprocess.check_output(f"{get_cmd('nmcli')} -t -f IP4.DNS connection show --active | head -n1", shell=True, stderr=subprocess.DEVNULL).decode().strip()
            if dns_out: info['dns'] = dns_out.replace(",", ", ")
        except: pass
        
        if info['dns'] == "...":
            try:
                dev_out = subprocess.check_output(f"{get_cmd('nmcli')} dev show | grep 'IP4.DNS'", shell=True, stderr=subprocess.DEVNULL).decode()
                ips = re.findall(r':\s+((?:\d{1,3}\.){3}\d{1,3})', dev_out)
                if ips: info['dns'] = ", ".join(ips)
            except: pass
    except: pass
    return info

def calc_core_stats(prev_stats):
    try:
        def get_cpu_times():
            with open("/proc/stat", "r") as f:
                lines = f.readlines()
            stats = {}
            for line in lines:
                if line.startswith("cpu"):
                    parts = line.split()
                    core = parts[0]
                    values = [int(x) for x in parts[1:]]
                    total = sum(values)
                    idle = values[3]
                    stats[core] = (total, idle)
            return stats

        current_stats = get_cpu_times()
        if prev_stats is None:
            return [], current_stats
        
        start_stats = prev_stats
        end_stats = current_stats
        
        results = []
        for core in sorted(start_stats.keys(), key=lambda x: int(x[3:]) if x[3:].isdigit() else -1):
            t1, i1 = start_stats[core]
            t2, i2 = end_stats[core]
            diff_total = t2 - t1
            diff_idle = i2 - i1
            usage = 0
            if diff_total > 0:
                usage = 100 * (1 - diff_idle / diff_total)
            
            freq_txt = "N/A"
            if core != "cpu":
                freq_path = f"/sys/devices/system/cpu/{core}/cpufreq/scaling_cur_freq"
                if os.path.exists(freq_path):
                    try:
                        with open(freq_path, "r") as f:
                            freq_mhz = int(f.read().strip()) / 1000
                            freq_txt = f"{freq_mhz:.0f} MHz"
                    except: pass
            
            results.append((core, usage, freq_txt))
        return results, end_stats
    except Exception as e:
        return [], prev_stats