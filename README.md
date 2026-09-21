# Capture Control

A small Omarchy bar widget combining the stock screen-recording action with
Show Me The Key controls. The icon uses the same size as Voxtype and remains
available when recording and key capture are off.

Part of [Omarchy QOL](https://github.com/omarchy-QOL). This plugin records the
screen and displays key presses; it does not edit videos.

- Left-click: open Omarchy's recording menu, or stop an active recording.
- Right-click: key capture switch, background opacity, and text colour.
- Gear: open capture settings and Hyprland bindings in two Neovim buffers.
- White, light teal, red, yellow, purple, and a custom `#rrggbb` text colour.
- The displayed start/stop shortcuts come from the active Hyprland bindings.

## Install

Requires Omarchy Quattro, Quickshell 0.3.1, Qt 6, Python 3.12+, Neovim,
Show Me The Key 1.21.0, and GTK 4.10 or newer. On Arch:

```bash
omarchy pkg add showmethekey meson ninja gcc glib2-devel
omarchy plugin add https://github.com/omarchy-QOL/omarchy-capture-control.git
python3 "$HOME/.config/omarchy/plugins/io.github.ilyazar.capture-control/build-renderer.py"
omarchy plugin enable io.github.ilyazar.capture-control --before omarchy.clock
```

The renderer build downloads a pinned Show Me The Key source archive and
checks its SHA-256 before compiling. Dependencies and the renderer must be
installed before starting key capture.

For local development, link the checkout at
`~/.config/omarchy/plugins/io.github.ilyazar.capture-control`, then run
`omarchy shell shell rescanPlugins` and the enable command above.

To place the widget before Voxtype instead of the clock:

```bash
omarchy plugin enable io.github.ilyazar.capture-control \
  --before io.github.ilyazar.voxtype-control
```

Remove `ScreenRecording` from the `omarchy.indicators` entry's `items` array
in `~/.config/omarchy/shell.json` to avoid a duplicate icon. Preserve the other
indicators. On hosts without Voxtype, place this widget before `omarchy.clock`.

Add unused shortcuts in `~/.config/hypr/bindings.lua`:

```lua
o.bind("SUPER + F8", "Start key capture", "omarchy shell keycapture start")
o.bind("SUPER + SHIFT + F8", "Stop key capture", "omarchy shell keycapture stop")
```

Keep those descriptions when changing the keys so the popup can find them.
Add this window rule to the user Hyprland configuration:

```lua
o.window({ class = "^one\\.alynx\\.showmethekey$",
  title = "^Floating Window - Show Me The Key$" }, {
  float = true, pin = true, no_initial_focus = true,
  move = { "(monitor_w-window_w)/2", "monitor_h-window_h-40" },
  no_blur = true, no_shadow = true, border_size = 0, no_dim = true,
  tag = "-default-opacity", opacity = "1 1",
})
```

Reload Hyprland and check `hyprctl configerrors` after the reload completes.
There is no autostart: capture begins only on request.

## Settings and lifetime

The capture application uses GLib's plain-text settings backend, isolated in
`~/.config/showmethekey/`. The gear opens
`glib-2.0/settings/keyfile` there and the current Hyprland `bindings.lua`.
Existing dconf settings seed this file on first use. Its
`[one/alynx/showmethekey]` section contains native application settings;
`[capture-control]` contains `background-opacity` (0 to 1) and `text-color`.
Do not edit the generated `gtk-4.0/gtk.css` file.

Opacity and colour changes briefly restart the renderer when applied. Opacity
applies on slider release; custom colour text applies on Enter or Apply.
At 100%, the background is solid black. Restarting returns the overlay to its
default position. Other native application settings use GLib's normal live
updates; hand-edited appearance values apply on the next capture start.

Double-tap Alt to pause/resume the display. Double-tap Ctrl to enable dragging
the Clickable Area, then double-tap Ctrl again to restore click-through.
These native shortcuts can be changed in the settings file.

`showmethekey-video.service` owns capture independently of plugin reloads.
The plugin has one shared status service across monitors. Its one-second
status check follows the stock recording indicator; it does not read keys.
The GTK application and packaged input backend handle input and permissions.

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

## Verify and remove

```bash
omarchy plugin validate "$PWD"
python3 -m unittest discover -s tests -v
```

For QML lint, provide the host import root (`qs` pointing to the Omarchy shell)
and use `/usr/lib/qt6/bin/qmllint`. The host's dynamic properties and
Quickshell's exit-status metadata produce known type warnings; verify actual
loading and interaction in the shell as well.

Stop capture before disabling or removing the plugin:

```bash
systemctl --user stop showmethekey-video.service
omarchy plugin disable io.github.ilyazar.capture-control
omarchy plugin remove io.github.ilyazar.capture-control
```

Remove its two bindings and restore `ScreenRecording` in the indicators list.
User settings and the private renderer remain available for reinstalling.
