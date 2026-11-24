#!/usr/bin/env python3
"""Portable local/headless Blender launcher. Only use trusted scenes."""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VERSION = "4.5.17"

def find_blender(explicit=None):
    candidates = [explicit] if explicit else [
        os.environ.get("BLENDER_BIN"), shutil.which("blender"),
        "/Applications/Blender.app/Contents/MacOS/Blender",
        str(Path(os.environ.get("ProgramFiles", "C:/Program Files")) /
            "Blender Foundation/Blender 4.5/blender.exe"),
    ]
    for candidate in candidates:
        if candidate:
            found = shutil.which(candidate) or (str(Path(candidate).resolve()) if Path(candidate).is_file() else None)
            if found:
                return found
    raise SystemExit("Blender not found. Install the pinned version or set BLENDER_BIN. See docs/blender-team-setup.md.")

def check_version(binary):
    proc = subprocess.run([binary, "--version"], capture_output=True, text=True, check=True)
    match = re.search(r"Blender\s+(\d+\.\d+\.\d+)", proc.stdout)
    if not match or match.group(1) != VERSION:
        raise SystemExit(f"Expected Blender {VERSION}, found {proc.stdout.splitlines()[:1]}")
    print(proc.stdout.splitlines()[0], flush=True)

def output_prefix(value):
    p = Path(value).expanduser().resolve()
    allowed = (ROOT / "renders").resolve()
    if not p.is_relative_to(allowed) or p == allowed:
        raise SystemExit("Render outputs must be under the ignored renders/ directory.")
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--smoke", action="store_true")
    group.add_argument("--scene", type=Path)
    parser.add_argument("--blender")
    parser.add_argument("--output", default="renders/frames/frame_")
    args = parser.parse_args()
    binary = find_blender(args.blender)
    check_version(binary)
    if args.check:
        return
    if args.smoke:
        target = output_prefix("renders/smoke/metallic-test.png")
        command = [binary, "--background", "--factory-startup", "--disable-autoexec",
                   "--python-exit-code", "1", "--python", str(ROOT / "engine/motion/smoke_scene.py"),
                   "--", str(target)]
        subprocess.run(command, check=True)
        if not target.is_file() or not target.stat().st_size:
            raise SystemExit("Smoke render missing or empty.")
        print(target)
        return
    scene = args.scene.expanduser().resolve()
    if scene.suffix.lower() != ".blend" or not scene.is_file():
        parser.error("--scene must point to an existing trusted .blend file")
    prefix = output_prefix(args.output)
    subprocess.run([binary, "--background", "--disable-autoexec", str(scene),
                    "--render-output", str(prefix), "--render-format", "PNG",
                    "--render-anim"], check=True)

if __name__ == "__main__":
    main()
