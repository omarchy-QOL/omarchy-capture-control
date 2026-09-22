#!/usr/bin/python3
"""Keep the capture process and its editable settings together."""

import argparse
import configparser
import json
import os
from pathlib import Path
import re
import subprocess
import sys

CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
APP_HOME = CONFIG_HOME / "showmethekey"
SETTINGS = APP_HOME / "glib-2.0/settings/keyfile"
UNIT = "showmethekey-video.service"
RENDERER = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "capture-control/showmethekey-gtk"


def running():
    return subprocess.run(
        ["systemctl", "--user", "is-active", "--quiet", UNIT],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0


def settings():
    config = configparser.ConfigParser(interpolation=None)
    if config.read(SETTINGS):
        for section in ("one/alynx/showmethekey", "capture-control"):
            if section not in config:
                raise ValueError(f"Missing [{section}] in {SETTINGS}")
    return config


def initialize():
    if SETTINGS.exists():
        return
    config = configparser.ConfigParser(interpolation=None)
    config["one/alynx/showmethekey"] = {
        "first-time": "false", "width": "900.0", "height": "100.0",
        "timeout": "1500.0", "alignment": "'center'",
        "show-keyboard": "true", "show-mouse": "true", "hide-visible": "false",
    }
    config["capture-control"] = {"background-opacity": "0.3", "text-color": "#ffffff"}
    save(config)


def save(config):
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    temporary = SETTINGS.with_suffix(".tmp")
    with temporary.open("w") as output:
        config.write(output, space_around_delimiters=False)
    temporary.replace(SETTINGS)


def opacity(config):
    value = config.getfloat("capture-control", "background-opacity", fallback=0.3)
    if not 0 <= value <= 1:
        raise ValueError("Background opacity must be between 0 and 1")
    return value


def text_color(config):
    value = config.get("capture-control", "text-color", fallback="#ffffff")
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise ValueError("Text colour must be a six-digit hex colour")
    return value.lower()


def only_omarchy_bindings(config):
    hidden = config.getboolean("one/alynx/showmethekey", "hide-visible", fallback=False)
    mode = config.get("one/alynx/showmethekey", "mode", fallback="'composed'")
    return hidden and mode != "'raw'"


def start():
    if running():
        return
    if not RENDERER.is_file():
        raise ValueError("Run build-renderer.py once before starting capture")
    initialize()
    css = APP_HOME / "gtk-4.0/gtk.css"
    css.parent.mkdir(parents=True, exist_ok=True)
    config = settings()
    css.write_text("window.smtk-keys-win.background { background: "
                   f"rgba(0, 0, 0, {opacity(config)}); color: {text_color(config)}; }}\n")
    subprocess.run([
        "systemd-run", "--user", "--quiet", "--collect", "--service-type=exec",
        "--unit=" + UNIT, "--setenv=GSETTINGS_BACKEND=keyfile",
        "--setenv=XDG_CONFIG_HOME=" + str(APP_HOME),
        str(RENDERER), "-A", "-C",
    ], check=True)


def stop():
    if running():
        subprocess.run(["systemctl", "--user", "stop", UNIT], check=True)


def set_native(key, value):
    env = {**os.environ, "GSETTINGS_BACKEND": "keyfile", "XDG_CONFIG_HOME": str(APP_HOME)}
    subprocess.run(["gsettings", "set", "one.alynx.showmethekey", key, value],
                   env=env, check=True)


def set_bindings_only(value):
    if value not in ("true", "false"):
        raise ValueError("Bindings filter must be true or false")
    initialize()
    config = settings()
    if value == "true" and config.get("one/alynx/showmethekey", "mode", fallback="'composed'") == "'raw'":
        set_native("mode", "composed")
    set_native("hide-visible", value)


def set_appearance(action, value):
    initialize()
    config = settings()
    key = "background-opacity" if action == "opacity" else "text-color"
    config["capture-control"][key] = value
    opacity(config)
    text_color(config)
    save(config)
    if running():
        stop()
        start()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("status", "start", "stop", "bindings-only", "opacity", "color", "edit"))
    parser.add_argument("value", nargs="?")
    args = parser.parse_args(argv)
    needs_value = args.action in ("bindings-only", "opacity", "color")
    if needs_value != (args.value is not None):
        parser.error(f"{args.action} requires one value" if needs_value
                     else f"{args.action} takes no value")

    if args.action == "status":
        recording = subprocess.run(
            ["pgrep", "--quiet", "-f", "^gpu-screen-recorder"],
        ).returncode == 0
        config = settings()
        print(json.dumps({"recording": recording, "running": running(),
                          "opacity": opacity(config), "textColor": text_color(config),
                          "onlyOmarchyBindings": only_omarchy_bindings(config)}))
    elif args.action == "start":
        start()
    elif args.action == "stop":
        stop()
    elif args.action == "bindings-only":
        set_bindings_only(args.value)
    elif args.action in ("opacity", "color"):
        set_appearance(args.action, args.value)
    elif args.action == "edit":
        initialize()
        os.execvp("omarchy-launch-terminal", [
            "omarchy-launch-terminal", "-e", "nvim", "-O", str(SETTINGS),
            str(CONFIG_HOME / "hypr/bindings.lua"),
        ])


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, configparser.Error, subprocess.CalledProcessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
