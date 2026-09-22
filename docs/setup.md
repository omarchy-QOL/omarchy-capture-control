# Setup and settings

Start with the [installation commands](../README.md#install).

Requires Omarchy Quattro, Quickshell 0.3.1, Qt 6, Python 3.12+, Neovim,
Show Me The Key 1.21.0, and GTK 4.10 or newer. Omarchy supplies the recorder.
Install the dependencies and build the renderer before starting key capture.

## Overlay placement

Add this window rule to your Hyprland Lua configuration to keep the key display
floating, visible across workspaces, and near the bottom of the screen:

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

## Keyboard shortcut

Optionally add this to `~/.config/hypr/bindings.lua` if Super+F8 is unused:

```lua
o.bind("SUPER + F8", "Toggle key capture", "omarchy shell keycapture toggle")
```

Keep the description when changing the key so the panel can find your shortcut.
Replace the separate start/stop bindings if upgrading from version 0.1.0.

## Bar placement

To put the icon before Voxtype instead of the clock:

```bash
omarchy plugin enable io.github.ilyazar.capture-control \
  --before io.github.ilyazar.voxtype-control
```

Remove `ScreenRecording` from the `omarchy.indicators` entry's `items` array
in `~/.config/omarchy/shell.json` to avoid a duplicate icon. Preserve the other
indicators. On hosts without Voxtype, place this widget before `omarchy.clock`.

## Settings

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
