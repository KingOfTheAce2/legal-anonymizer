#!/usr/bin/env python3
"""
Build orchestration script for Legal Anonymizer on Windows.

Produces a distributable .msi by:
  A) Building the Python sidecar exe via PyInstaller
  B) Copying it to the Tauri binaries directory with the correct triple-name
  C) Running the Tauri build to produce the .msi

Usage:
    python scripts/build_windows.py [--layer1] [--layer2] [--layer3] [--all]
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE_DIR = ROOT / "engine" / "python"
DESKTOP_DIR = ROOT / "apps" / "desktop"
TAURI_DIR = DESKTOP_DIR / "src-tauri"
BINARIES_DIR = TAURI_DIR / "binaries"

TRIPLE = "x86_64-pc-windows-msvc"
SIDECAR_NAME = f"anonymizer_engine-{TRIPLE}.exe"


def step_a_build_sidecar(layers: list[str]):
    """Build the Python sidecar executable using PyInstaller."""
    print("\n" + "=" * 60)
    print("  Step A: Building Python sidecar executable")
    print("=" * 60 + "\n")

    cmd = [sys.executable, str(ENGINE_DIR / "build_standalone.py")]
    for layer in layers:
        cmd.append(f"--{layer}")

    subprocess.run(cmd, cwd=str(ENGINE_DIR), check=True)

    # Verify output exists
    dist_exe = ENGINE_DIR / "dist" / "sidecar_entrypoint.exe"
    if not dist_exe.exists():
        # PyInstaller may name it based on the script name
        alt = ENGINE_DIR / "dist" / "anonymizer_engine.exe"
        if alt.exists():
            dist_exe = alt
        else:
            print(f"ERROR: Expected sidecar exe not found in {ENGINE_DIR / 'dist'}")
            print("Contents:", list((ENGINE_DIR / "dist").iterdir()) if (ENGINE_DIR / "dist").exists() else "dist/ missing")
            sys.exit(1)

    print(f"Sidecar built: {dist_exe} ({dist_exe.stat().st_size / 1024 / 1024:.1f} MB)")
    return dist_exe


def step_b_copy_sidecar(dist_exe: Path):
    """Copy sidecar exe to Tauri binaries directory with the correct triple name."""
    print("\n" + "=" * 60)
    print("  Step B: Copying sidecar to Tauri binaries")
    print("=" * 60 + "\n")

    BINARIES_DIR.mkdir(parents=True, exist_ok=True)
    dest = BINARIES_DIR / SIDECAR_NAME
    shutil.copy2(str(dist_exe), str(dest))
    print(f"Copied to: {dest}")


def step_c_build_tauri():
    """Run the Tauri build to produce the .msi installer."""
    print("\n" + "=" * 60)
    print("  Step C: Building Tauri desktop application")
    print("=" * 60 + "\n")

    # First build the frontend
    subprocess.run(["npm", "install"], cwd=str(DESKTOP_DIR), check=True, shell=True)
    subprocess.run(["npm", "run", "build"], cwd=str(DESKTOP_DIR), check=True, shell=True)

    # Then build the Tauri app
    subprocess.run(
        ["npm", "run", "tauri", "build"],
        cwd=str(DESKTOP_DIR),
        check=True,
        shell=True,
    )

    # Find the .msi
    msi_dir = TAURI_DIR / "target" / "release" / "bundle" / "msi"
    if msi_dir.exists():
        for msi in msi_dir.glob("*.msi"):
            print(f"\nInstaller: {msi} ({msi.stat().st_size / 1024 / 1024:.1f} MB)")
            return msi

    nsis_dir = TAURI_DIR / "target" / "release" / "bundle" / "nsis"
    if nsis_dir.exists():
        for exe in nsis_dir.glob("*.exe"):
            print(f"\nInstaller: {exe} ({exe.stat().st_size / 1024 / 1024:.1f} MB)")
            return exe

    print("WARNING: No installer found in bundle directory")
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Build Legal Anonymizer Windows installer",
    )
    parser.add_argument("--layer1", action="store_true", help="Include Layer 1 (spaCy)")
    parser.add_argument("--layer2", action="store_true", help="Include Layer 2 (Transformers)")
    parser.add_argument("--layer3", action="store_true", help="Include Layer 3 (Presidio)")
    parser.add_argument("--all", action="store_true", help="Include all layers")
    args = parser.parse_args()

    layers = []
    if args.all:
        layers = ["layer1", "layer2", "layer3"]
    else:
        if args.layer1:
            layers.append("layer1")
        if args.layer2:
            layers.append("layer2")
        if args.layer3:
            layers.append("layer3")

    if not layers:
        layers = ["layer1"]

    print("=" * 60)
    print("  Legal Anonymizer — Windows Build")
    print(f"  Layers: {', '.join(layers)}")
    print("=" * 60)

    dist_exe = step_a_build_sidecar(layers)
    step_b_copy_sidecar(dist_exe)
    installer = step_c_build_tauri()

    print("\n" + "=" * 60)
    print("  BUILD COMPLETE")
    print("=" * 60)
    if installer:
        print(f"\n  Installer: {installer}")
    print(f"  Layers: {', '.join(layers)}")
    print("\n  To install: double-click the .msi file")
    print("  No Python installation required on target machine.")


if __name__ == "__main__":
    main()
