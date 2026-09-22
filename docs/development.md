# Development

Link the checkout at
`~/.config/omarchy/plugins/io.github.ilyazar.capture-control`, then run
`omarchy shell shell rescanPlugins` and enable the plugin as in the
[README](../README.md#install).

## Implementation

The plugin delegates input handling and permissions to Show Me The Key.
One shared status service checks recording and key capture once per second
across all monitors; it does not read keys.

## Renderer patch

Upstream draws text with a hardcoded white Cairo source. The build script pins
the 1.21.0 source archive and verifies its checksum, then replaces that line
with three lines reading the GTK text colour. A small SIGTERM handler also
uses the application's normal quit path, allowing its privileged input
backend to exit before the service stops. Input handling is unchanged.
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
