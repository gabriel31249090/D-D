"""Build a private Windows desktop installer using only the installed Python/.NET.

No downloaded repository, book, bridge configuration, user database or credential
is included. The installed runtime does not depend on Python on the target PC.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZIP_DEFLATED, ZipFile

from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.2.0"


def copy_tree(source: Path, target: Path, *, exclude=(), suffixes=None):
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if path.is_symlink() or any(part in exclude or part == "__pycache__" for part in relative.parts):
            continue
        if path.is_file() and path.suffix not in (".pyc", ".pyo") and (suffixes is None or path.suffix.lower() in suffixes):
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)


def runtime_packages(runtime: Path):
    """Copy declared runtime dependencies, including their license metadata."""
    queue = ["fastapi", "pydantic", "sqlalchemy", "alembic", "uvicorn"]
    visited = set()
    records = []
    while queue:
        name = queue.pop()
        distribution = metadata.distribution(name)
        canonical = distribution.metadata["Name"].lower().replace("_", "-")
        if canonical in visited:
            continue
        visited.add(canonical)
        site_root = Path(distribution.locate_file("")).resolve()
        for item in distribution.files or []:
            relative = Path(str(item))
            if relative.is_absolute() or ".." in relative.parts or "__pycache__" in relative.parts or relative.suffix == ".pyc":
                continue
            source = Path(distribution.locate_file(item)).resolve()
            if source.is_file() and source.is_relative_to(site_root):
                destination = runtime / "Lib" / "site-packages" / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
        for raw in distribution.requires or []:
            requirement = Requirement(raw)
            if requirement.marker is None or requirement.marker.evaluate({"extra": ""}):
                queue.append(requirement.name)
        records.append({"name": distribution.metadata["Name"], "version": distribution.version})
    return sorted(records, key=lambda item: item["name"].lower())


def build_payload(stage: Path):
    if not (ROOT / "desktop" / "app.py").is_file():
        raise SystemExit("desktop/app.py is not ready; wait for the application modules before the final build")
    runtime = stage / "runtime"
    python_base = Path(sys.base_prefix)
    runtime.mkdir(parents=True)
    for name in ("python.exe", "pythonw.exe", "python3.dll", "python312.dll", "vcruntime140.dll", "vcruntime140_1.dll"):
        source = python_base / name
        if not source.is_file():
            raise SystemExit(f"Required local Python runtime file not found: {name}")
        shutil.copy2(source, runtime / name)
    copy_tree(python_base / "Lib", runtime / "Lib",
              exclude=("site-packages", "test", "tests", "idlelib", "ensurepip", "venv", "turtledemo"))
    copy_tree(python_base / "DLLs", runtime / "DLLs")
    copy_tree(python_base / "tcl", runtime / "tcl")
    (runtime / "python312._pth").write_text(".\nLib\nDLLs\nLib/site-packages\n..\nimport site\n", encoding="utf-8")
    # Explicit allowlist: never copy the entire project/workspace.
    for name in ("desktop", "backend", "migrations"):
        copy_tree(ROOT / name, stage / name, exclude=("tests", ".arcanum", "raw"),
                  suffixes={".py", ".ico", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ttf", ".otf"})
    shutil.copy2(ROOT / "alembic.ini", stage / "alembic.ini")
    packages = runtime_packages(runtime)
    licenses = stage / "licenses"
    licenses.mkdir()
    shutil.copy2(python_base / "LICENSE.txt", licenses / "LICENSE_PYTHON.txt")
    for name in ("LICENSE_TCL.txt", "LICENSE_TK.txt"):
        shutil.copy2(ROOT / "packaging" / name, licenses / name)
    contract = ROOT / "docs" / "API_CONTRACT.md"
    if contract.exists():
        shutil.copy2(contract, licenses / "SRD_AND_SCOPE.md")
    (licenses / "RUNTIME_PACKAGES.json").write_text(json.dumps(packages, indent=2), encoding="utf-8")
    (licenses / "THIRD_PARTY.txt").write_text(
        "Python 3.12 and Tcl/Tk licenses are included here.\n"
        "Dependency licenses are preserved in runtime/Lib/site-packages/*dist-info/.\n"
        "The Python runtime is copied without modification from the local official Python installation.\n"
        "Private books, source archives, databases, account data and MCP configurations are excluded.\n", encoding="utf-8")
    return packages


def compile_executable(output: Path, *, payload: Path | None = None):
    framework = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Microsoft.NET" / "Framework64" / "v4.0.30319"
    compiler = framework / "csc.exe"
    if not compiler.is_file():
        raise SystemExit("The Windows .NET Framework C# compiler is required to build the installer")
    command = [str(compiler), "/nologo", "/target:winexe", "/platform:x64", "/optimize+", "/utf8output",
        f"/out:{output}", "/reference:System.Windows.Forms.dll", "/reference:System.Drawing.dll",
        f"/reference:{framework/'System.IO.Compression.dll'}",
        f"/reference:{framework/'System.IO.Compression.FileSystem.dll'}", "/reference:System.Web.Extensions.dll"]
    icon = ROOT / "desktop" / "assets" / "arcanum.ico"
    if icon.is_file():
        command.append(f"/win32icon:{icon}")
    if payload is not None:
        command.append(f"/resource:{payload},Arcanum.Payload.zip")
    else:
        command.append("/define:UNINSTALLER")
    command.append(str(ROOT / "packaging" / "Setup.cs"))
    subprocess.run(command, cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-only", action="store_true", help="Validate build tools without packaging incomplete application modules")
    args = parser.parse_args()
    if os.name != "nt" or sys.version_info[:2] != (3, 12):
        raise SystemExit("Build this Windows x64 installer with the project's Python 3.12 virtual environment")
    output = ROOT / "dist"
    output.mkdir(exist_ok=True)
    work = output / ("build-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
    work.mkdir()
    if args.prepare_only:
        compile_executable(work / "Uninstall.exe")
        print(json.dumps({"ok": True, "compiler_checked": True, "work": str(work)}))
        return
    stage = work / "app"
    packages = build_payload(stage)
    compile_executable(stage / "Uninstall.exe")
    payload = work / "payload.zip"
    with ZipFile(payload, "w", ZIP_DEFLATED, compresslevel=6) as archive:
        for file in sorted(stage.rglob("*")):
            if file.is_file():
                archive.write(file, file.relative_to(stage).as_posix())
    installer = output / f"ARCANUM-Setup-{VERSION}-win-x64.exe"
    compile_executable(installer, payload=payload)
    report = {"version": VERSION, "installer": str(installer), "stage": str(stage),
        "sha256": hashlib.file_digest(installer.open("rb"), "sha256").hexdigest(),
        "installer_bytes": installer.stat().st_size, "file_count": sum(1 for p in stage.rglob("*") if p.is_file()),
        "python": sys.version, "packages": packages, "private_sources_included": False,
        "installed_smoke": "not yet run"}
    (output / "BUILD_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

