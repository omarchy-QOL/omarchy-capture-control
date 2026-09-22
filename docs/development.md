# Development

Link the checkout at
`~/.config/omarchy/plugins/io.github.ilyazar.capture-control`, then run
`omarchy shell shell rescanPlugins` and enable the plugin as in the
[README](../README.md#install).

## Implementation

The plugin delegates input handling and permissions to Show Me The Key.
One shared status service checks recording and key capture once per second
across all monitors; it does not read keys.

## First-run setup

`setup.py` checks installed packages through Pacman. The panel offers only
missing packages; the installer runs `omarchy pkg add` in Omarchy's terminal.
Build tools are required only while the private renderer is missing. A file
lock prevents the panel and installer from building simultaneously.

`overlay.lua` registers a named runtime window rule. It is applied before
starting the renderer and reapplied after a compositor configuration reload.
No installation or removal hooks modify the user's Hyprland configuration.

## Renderer patch

Upstream draws text with a hardcoded white Cairo source. The build script pins
the 1.21.0 source archive and verifies its checksum, then replaces that line
with three lines reading the GTK text colour. A small SIGTERM handler also
uses the application's normal quit path, allowing its privileged input
backend to exit before the service stops. Input handling is unchanged.
Each build extracts the verified source and checks every patch before compiling.
The binary is replaced atomically, so rebuilding does not interrupt capture.
The binary lives in `~/.local/share/capture-control/`; build files stay in
`~/.cache/capture-control/`. No system package files are replaced.

The bar action is adapted from Omarchy's `ScreenRecording.qml`. The colour
dropdown is copied from Keyboard Layout Pulse's `ColorDropdown.qml`, using
the same host controls and sizing. Show Me The Key is
[Apache-2.0 licensed](https://github.com/AlynxZhou/showmethekey).

## Verify

From the checkout root:

```bash
omarchy plugin validate "$PWD"
python3 -m unittest discover -s tests -v
```

For QML lint, provide the host import root (`qs` pointing to the Omarchy shell)
and use `/usr/lib/qt6/bin/qmllint`. The host's dynamic properties and
Quickshell's exit-status metadata produce known type warnings; verify actual
loading and interaction in the shell as well.
