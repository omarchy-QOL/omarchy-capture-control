#!/usr/bin/python3
"""Keep the capture process and its editable settings together."""

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
    config.read(SETTINGS)
    return config


def initialize():
    if SETTINGS.exists():
        return
    config = configparser.ConfigParser(interpolation=None)
    config.read_string("[one/alynx/showmethekey]\n" + subprocess.check_output(
        ["dconf", "dump", "/one/alynx/showmethekey/"], text=True,
    ).removeprefix("[/]\n"))
    config["one/alynx/showmethekey"].update({
        "first-time": "false", "width": "900.0", "height": "100.0",
        "timeout": "1500.0", "alignment": "'center'",
        "show-keyboard": "true", "show-mouse": "true",
    })
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
    return (config.getboolean("one/alynx/showmethekey", "hide-visible", fallback=False)
            and config.get("one/alynx/showmethekey", "mode", fallback="'composed'") != "'raw'")


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


def main():
    action = sys.argv[1]
    if action == "status":
        recording = subprocess.run(
            ["pgrep", "--quiet", "-f", "^gpu-screen-recorder"],
        ).returncode == 0
        config = settings()
        print(json.dumps({"recording": recording, "running": running(),
                          "opacity": opacity(config), "textColor": text_color(config),
                          "onlyOmarchyBindings": only_omarchy_bindings(config)}))
    elif action == "start":
        start()
    elif action == "stop":
        stop()
    elif action == "bindings-only":
        value = sys.argv[2]
        if value not in ("true", "false"):
            raise ValueError("Bindings filter must be true or false")
        initialize()
        env = {**os.environ, "GSETTINGS_BACKEND": "keyfile", "XDG_CONFIG_HOME": str(APP_HOME)}
        command = ["gsettings", "set", "one.alynx.showmethekey"]
        if value == "true" and settings().get("one/alynx/showmethekey", "mode", fallback="'composed'") == "'raw'":
            subprocess.run(command + ["mode", "composed"], env=env, check=True)
        subprocess.run(command + ["hide-visible", value], env=env, check=True)
    elif action in ("opacity", "color"):
        initialize()
        config = settings()
        if not config.has_section("capture-control"):
            config.add_section("capture-control")
        key = "background-opacity" if action == "opacity" else "text-color"
        config["capture-control"][key] = sys.argv[2]
        opacity(config)
        text_color(config)
        save(config)
        if running():
            stop()
            start()
    elif action == "edit":
        initialize()
        os.execvp("omarchy-launch-terminal", [
            "omarchy-launch-terminal", "-e", "nvim", "-O", str(SETTINGS),
            str(CONFIG_HOME / "hypr/bindings.lua"),
        ])
    else:
        raise ValueError("Unknown capture action")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, configparser.Error, subprocess.CalledProcessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
