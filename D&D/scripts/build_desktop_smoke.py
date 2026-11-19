"""Exercise the actual installer, installed runtime and uninstaller in disposable paths."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]


def main():
    build = json.loads((ROOT / "dist" / "BUILD_REPORT.json").read_text(encoding="utf-8"))
    installer = Path(build["installer"])
    work = ROOT / "dist" / ("install-smoke-" + uuid4().hex)
    work.mkdir()
    installed = work / "installed"
    data = work / "user-data"
    data.mkdir()
    keep = data / "preserve-me.txt"
    keep.write_text("Personal campaign marker. Must survive uninstall.", encoding="utf-8")
    log = work / "installer.log"
    subprocess.run([str(installer), "--silent", "--install-dir", str(installed),
        "--no-register", "--no-shortcuts", "--log", str(log)], check=True, timeout=120)
    assert (installed / ".arcanum-install.json").is_file(), "Installer did not create its manifest"
    environment = {**os.environ, "ARCANUM_DATA_DIR": str(data), "PYTHONUTF8": "1"}
    # Intentionally use a foreign CWD: installed application imports must be self-contained.
    result = subprocess.run([str(installed / "runtime" / "python.exe"), "-m", "desktop.app", "--smoke-test"],
        cwd=work, env=environment, capture_output=True, text=True, encoding="utf-8", timeout=60)
    (work / "app-smoke.stdout.txt").write_text(result.stdout, encoding="utf-8")
    (work / "app-smoke.stderr.txt").write_text(result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError("Installed application smoke failed: " + result.stderr[-4000:])
    extra = installed / "user-added-note.txt"
    extra.write_text("Not managed by the installer.", encoding="utf-8")
    subprocess.run([str(installed / "Uninstall.exe"), "--silent", "--log", str(log)], check=True, timeout=15)
    for _ in range(100):
        if not (installed / ".arcanum-install.json").exists():
            break
        time.sleep(.1)
    assert not (installed / "runtime" / "python.exe").exists(), "Uninstaller did not remove managed runtime"
    assert not (installed / ".arcanum-install.json").exists(), "Uninstaller did not complete"
    assert extra.read_text(encoding="utf-8") == "Not managed by the installer."
    assert keep.read_text(encoding="utf-8").startswith("Personal campaign")
    report = {"installer": str(installer), "work": str(work), "install": "passed", "installed_runtime_smoke": "passed",
        "foreign_cwd": True, "uninstall": "passed", "personal_data_preserved": True,
        "unmanaged_install_file_preserved": True, "os_registration_and_shortcuts": "not exercised in disposable smoke",
        "app_output": result.stdout.strip()}
    (ROOT / "dist" / "INSTALL_SMOKE_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    build["installed_smoke"] = "passed"
    (ROOT / "dist" / "BUILD_REPORT.json").write_text(json.dumps(build, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

