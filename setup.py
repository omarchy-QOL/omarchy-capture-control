#!/usr/bin/python3
"""Prepare key capture through Omarchy's native package installer."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys

from control import RENDERER


def missing_packages():
    packages = ["showmethekey"]
    if not RENDERER.is_file():
        packages += ["meson", "glib2-devel", "gcc", "pkgconf", "gettext"]
    result = subprocess.run(["pacman", "-T", *packages], capture_output=True, text=True)
    if result.returncode not in (0, 127):
        raise RuntimeError(result.stderr.strip() or "Could not check installed packages")
    return result.stdout.splitlines()


def build():
    cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "capture-control"
    cache.mkdir(parents=True, exist_ok=True)
    with (cache / "build.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if not RENDERER.is_file():
            subprocess.run([sys.executable, str(Path(__file__).with_name("build-renderer.py"))], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("status", "install", "build"))
    args = parser.parse_args()
    if args.action == "status":
        print(json.dumps({"missing": missing_packages(), "renderer": RENDERER.is_file()}))
    elif args.action == "install":
        try:
            packages = missing_packages()
            if packages:
                subprocess.run(["omarchy", "pkg", "add", *packages], check=True)
            build()
        except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
            print(f"Setup failed: {error}", file=sys.stderr)
            input("Press Enter to close, then right-click Capture Control to retry. ")
            raise SystemExit(1)
    else:
        build()


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
