# Setup and settings

Start with the [installation commands](../README.md#install).

Requires Omarchy Quattro, Quickshell 0.3.1, Qt 6, Python 3.12+, Neovim,
Show Me The Key 1.21.0, and GTK 4.10 or newer. Omarchy supplies the recorder.
Right-click the icon to install missing dependencies and prepare the renderer.
Installing packages opens a terminal; declining leaves screen recording usable.
Build failures can be retried from the panel. Source downloads require internet
access the first time.

## Overlay placement

The plugin applies its named Hyprland Lua window rule when capture starts and
again after a Hyprland configuration reload while capture is running. The
rule keeps the overlay floating, pinned across workspaces, and near the bottom
of the screen. It does not edit your configuration files; the runtime rule
expires on configuration reload and is reapplied when capture next starts.
There is no autostart: capture begins only on request.

## Keyboard shortcut

Optionally add this to `~/.config/hypr/bindings.lua` if Super+F8 is unused:

```lua
o.bind("SUPER + F8", "Toggle key capture", "omarchy shell keycapture toggle")
```

Keep the description when changing the key so the panel can find your shortcut.

## Bar placement

Placement is optional. For example, move the icon before the clock:

```bash
omarchy plugin enable io.github.ilyazar.capture-control --before omarchy.clock
```

`--before` only controls placement; it does not replace the stock recording
indicator. Capture Control leaves the stock indicators unchanged, including on
removal. The stock `ScreenRecording` component is part of `omarchy.indicators`,
not a separately replaceable plugin like `omarchy.keyboard-layout`.

To hide a duplicate recording indicator, remove `ScreenRecording` from the
`omarchy.indicators` entry's `items` array in
`~/.config/omarchy/shell.json`, preserving the other indicators. Restore that
entry yourself if you later remove Capture Control.

## Settings

The capture application uses GLib's plain-text settings backend, isolated in
`~/.config/showmethekey/`. The gear opens
`glib-2.0/settings/keyfile` there and the current Hyprland `bindings.lua`.
The plugin creates this file with its defaults on first use. Its
`[one/alynx/showmethekey]` section contains native application settings;
`[capture-control]` contains `background-opacity` (0 to 1) and `text-color`.
Do not edit the generated `gtk-4.0/gtk.css` file.

Opacity and colour changes briefly restart the renderer when applied. Opacity
applies on slider release; custom colour text applies on Enter or Apply.
At 100%, the background is solid black. Restarting returns the overlay to its
default position. Other native application settings use GLib's normal live
updates; hand-edited appearance values apply on the next capture start.

New installations default to **All bindings**, with the Omarchy filter off.
**Only Omarchy** controls Show Me The Key's native `hide-visible`
setting. It applies live without restarting capture and is saved while capture
is off. It hides keyboard input without Super, Ctrl, or Alt; it does not check
Hyprland's binding list. Application shortcuts can still appear, and unmodified
or Shift-only shortcuts disappear. Mouse clicks follow `show-mouse` separately.
The filter works in composed and compact modes. Enabling it in raw mode switches
to composed mode, which remains selected when the filter is turned off.
This setting needs no renderer rebuild or additional dependency.

Double-tap Alt to pause/resume the display. Double-tap Ctrl to enable dragging
the Clickable Area, then double-tap Ctrl again to restore click-through.
These native shortcuts can be changed in the settings file.

Key capture runs in `showmethekey-video.service` and survives plugin reloads.
To stop it from a terminal:

```bash
systemctl --user stop showmethekey-video.service
```
