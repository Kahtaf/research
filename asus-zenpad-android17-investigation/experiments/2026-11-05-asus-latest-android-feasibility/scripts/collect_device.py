#!/usr/bin/env python3
"""Read-only hardware and vendor baseline for the authorized ASUS tablet."""
import datetime
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SERIAL = "DEVICE_SERIAL_REDACTED"
OUT = ROOT / "evidence" / "device"
OUT.mkdir(parents=True, exist_ok=True)

def shell(command):
    result = subprocess.run(["adb", "-s", SERIAL, "shell", command],
                            text=True, capture_output=True, timeout=45)
    return {"command": command, "exit_code": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}

device = shell("getprop ro.product.device")
if device["exit_code"] != 0 or device["stdout"].strip() != "P00A_2":
    raise SystemExit("Expected ASUS P00A_2 is not connected")

checks = {
    "identity": "getprop | grep -iE 'ro.product|ro.hardware|ro.board|ro.build|ro.boot|ro.treble|ro.vndk|ro.crypto'",
    "kernel": "uname -a; cat /proc/version; cat /proc/cmdline; ls -l /proc/config.gz; cat /proc/cpuinfo",
    "partitions": "cat /proc/partitions; cat /proc/mounts; ls -l /dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name; df -k /system /data /cache",
    "device_tree": "ls -l /proc/device-tree /sys/firmware/devicetree/base; cat /proc/device-tree/model; cat /proc/device-tree/compatible",
    "display": "wm size; wm density; dumpsys SurfaceFlinger | head -n 100",
    "input": "cat /proc/bus/input/devices",
    "modules": "cat /proc/modules; ls -l /system/lib/modules /system/vendor/lib/modules /system/vendor/lib64/modules",
    "hardware_libraries": "ls -l /system/lib/hw /system/lib64/hw /system/vendor/lib/hw /system/vendor/lib64/hw; ls -l /system/vendor/lib/egl /system/vendor/lib64/egl",
    "hal_services": "service list; ls /system/bin | grep -iE 'camera|audio|surface|wifi|wlan|netd|hwserv|servicemanager|keystore'; ls -l /system/vendor/bin",
    "power": "ls /sys/class/power_supply; ls /sys/class/power_supply/battery; cat /sys/power/state; dumpsys battery",
    "features": "pm list features",
    "memory": "cat /proc/meminfo; cat /proc/swaps",
    "firmware": "ls -lR /system/vendor/firmware /system/etc/firmware /system/etc/wifi",
    "device_nodes": "ls -l /dev | grep -iE 'mali|ion|dri|binder|ashmem|camera|video|galcore|kgsl|wmt|stp|wifi'",
    "kernel_interfaces": "ls -ld /sys/fs/bpf /sys/fs/cgroup /dev/cpuctl /dev/memcg /dev/binderfs /dev/binder /dev/hwbinder /dev/vndbinder /dev/ashmem /dev/ion /dev/dri /dev/mali 2>/dev/null",
}
results = {"collected_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "serial": SERIAL}
for name, command in checks.items():
    result = shell(command)
    results[name] = result
    (OUT / f"{name}.txt").write_text(result["stdout"] + result["stderr"])
    print(name, "exit", result["exit_code"], "bytes", len(result["stdout"]), flush=True)
(OUT / "collection.json").write_text(json.dumps(results, indent=2) + "\n")
for remote, local in [("/proc/config.gz", OUT / "config.gz"),
                      ("/system/vendor", OUT / "vendor"),
                      ("/system/lib/hw", OUT / "system-lib-hw"),
                      ("/system/lib64/hw", OUT / "system-lib64-hw")]:
    result = subprocess.run(["adb", "-s", SERIAL, "pull", remote, str(local)],
                            text=True, capture_output=True, timeout=180)
    (OUT / (local.name + "-pull.txt")).write_text(result.stdout + result.stderr)
    print("pull", remote, "exit", result.returncode, flush=True)
