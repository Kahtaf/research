#!/usr/bin/env python3
"""Reversible ASUS/OEM optional-package disabling for one authorized tablet."""
import argparse
import datetime
import json
from pathlib import Path
import re
import subprocess

SERIAL = "DEVICE_SERIAL_REDACTED"
ROOT = Path(__file__).resolve().parent
CANDIDATES = {
    "com.ironsource.appcloud.oobe.asus": "AppCloud app recommendations/promotions",
    "com.asus.gamewidget": "ASUS Game Broadcaster widget/service",
    "com.asus.quickmemo": "Quick Memo",
    "com.asus.quickmemoservice": "Quick Memo service",
    "com.asus.supernote": "SuperNote",
    "com.asus.task": "ASUS tasks/reminders",
    "com.asus.taskwidget": "Task Manager widget",
    "com.asus.weathertime": "ASUS Weather",
    "com.asus.zencircle": "ZenCircle",
    "com.asus.ephotoburst": "Burst photo viewer",
    "com.asus.collage": "Photo collage",
    "com.asus.livedemo": "Retail demo",
    "com.asus.livedemoservice": "Retail demo service",
    "com.asus.userfeedback": "ZenUI Help/feedback",
    "com.asus.loguploader": "Log uploader",
    "com.asus.loguploaderproxy": "Log uploader proxy",
    "com.asus.easylauncher": "Easy Mode launcher",
}
KEEP = [
    "com.teslacoilsw.launcher", "com.google.android.inputmethod.latin",
    "com.android.chrome", "com.android.vending", "com.google.android.gms",
    "com.google.android.gsf", "com.android.settings", "com.android.systemui",
    "com.android.bluetooth", "com.asus.camera", "com.asus.gallery",
    "com.asus.kidslauncher", "com.asus.launcher",
]


def adb(*args):
    result = subprocess.run(["adb", "-s", SERIAL, *args], text=True,
                            capture_output=True, timeout=30)
    if result.returncode:
        raise RuntimeError((result.stdout + result.stderr).strip())
    return result.stdout.strip()


def shell(*args):
    return adb("shell", *args)


def packages(flag=None):
    args = ["pm", "list", "packages", "--user", "0"]
    if flag:
        args.append(flag)
    return sorted(line.removeprefix("package:") for line in shell(*args).splitlines()
                  if line.startswith("package:"))


def google_state():
    return {name: [p for p in packages(flag) if p.startswith("com.google.")
                  or p == "com.android.vending" or p.startswith("com.mgoogle.")]
            for name, flag in [("installed", None), ("enabled", "-e"), ("disabled", "-d")]}


def save(path, data):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.replace(path)


def identity():
    if shell("getprop", "ro.product.manufacturer").lower() != "asus":
        raise RuntimeError("Manufacturer mismatch")
    if shell("getprop", "ro.product.device") != "P00A_2":
        raise RuntimeError("Device mismatch")


def verify(baseline, journal):
    enabled = set(packages("-e"))
    disabled = set(packages("-d"))
    return {
        "google_unchanged": google_state() == baseline["google"],
        "previously_disabled_preserved": set(baseline["disabled"]) <= disabled,
        "newly_disabled": sorted(p for p, item in journal.items()
                                 if item["status"] == "disabled" and p in disabled),
        "kept_packages_enabled": {p: p in enabled for p in KEEP},
        "home": shell("cmd", "package", "resolve-activity", "--brief", "-a",
                      "android.intent.action.MAIN", "-c", "android.intent.category.HOME"),
        "keyboard": shell("settings", "get", "secure", "default_input_method"),
        "webview": shell("settings", "get", "global", "webview_provider"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["inventory", "apply", "restore"])
    parser.add_argument("--run", type=Path)
    args = parser.parse_args()
    identity()
    if args.mode == "restore":
        if args.run is None:
            parser.error("restore requires --run")
        journal_path = args.run.resolve() / "journal.json"
        journal = json.loads(journal_path.read_text())
        for package, item in journal.items():
            if package not in CANDIDATES or item["original"] not in [0, 1]:
                raise RuntimeError("Unexpected journal entry")
            if item["status"] not in ["attempting", "disabled"]:
                continue
            action = "default-state" if item["original"] == 0 else "enable"
            result = shell("pm", action, "--user", "0", package)
            if package not in packages("-e"):
                raise RuntimeError(f"Restore failed for {package}: {result}")
            item["status"] = "restored"
            save(journal_path, journal)
            print("Restored", package)
        return

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    run = ROOT / "runs" / stamp
    run.mkdir(parents=True)
    baseline = {"serial": SERIAL, "installed": packages(), "enabled": packages("-e"),
                "disabled": packages("-d"), "google": google_state()}
    save(run / "baseline.json", baseline)
    (run / "battery.txt").write_text(shell("dumpsys", "battery") + "\n")
    journal = {}
    for package, label in CANDIDATES.items():
        if package not in baseline["enabled"]:
            continue
        dump = shell("dumpsys", "package", package)
        (run / (package + ".txt")).write_text(dump + "\n")
        state = re.search(r"User 0:[^\n]*\benabled=(\d+)", dump)
        if not state or int(state[1]) not in [0, 1]:
            raise RuntimeError(f"Unknown original state for {package}")
        journal[package] = {"label": label, "original": int(state[1]), "status": "planned"}
    save(run / "journal.json", journal)
    print("Run directory:", run)
    print("Candidates:", len(journal))
    for package, item in journal.items():
        print(package, "—", item["label"])
    if args.mode == "inventory":
        return
    print(f"Restore: python3 {ROOT / 'debloat.py'} restore --run {run}", flush=True)
    for package, item in journal.items():
        item["status"] = "attempting"
        save(run / "journal.json", journal)
        result = shell("pm", "disable-user", "--user", "0", package)
        if package not in packages("-d"):
            raise RuntimeError(f"Disable failed for {package}: {result}")
        item["status"] = "disabled"
        save(run / "journal.json", journal)
        print("Disabled", package, flush=True)
    checks = verify(baseline, journal)
    save(run / "verification.json", checks)
    print(json.dumps(checks, indent=2))
    if not checks["google_unchanged"] or not checks["previously_disabled_preserved"]:
        raise RuntimeError("Package preservation check failed; inspect verification.json")


if __name__ == "__main__":
    main()
