# Capture Control

Screen recording and visible key presses from one Omarchy bar icon, powered by
[Show Me The Key][showmethekey], an established key visualizer built for
Wayland. Use Omarchy's recorder and turn the key display on when needed.

![Capture Control's key display settings in the Omarchy bar](preview.png)

## Install

On Omarchy Quattro:

```bash
omarchy pkg add showmethekey meson ninja gcc glib2-devel
omarchy plugin add https://github.com/omarchy-QOL/omarchy-capture-control.git
capture_plugin="$HOME/.config/omarchy/plugins/io.github.ilyazar.capture-control"
python3 "$capture_plugin/build-renderer.py"
omarchy plugin enable io.github.ilyazar.capture-control --before omarchy.clock
```

Then finish the [one-time overlay setup](docs/setup.md#overlay-placement).
The build adds text colour support to a private copy of Show Me The Key;
your system package stays unchanged.

## Use

- **Left-click** the bar icon to open the recording menu or stop a recording.
- **Right-click** to toggle the key display, set background opacity, and choose
  a text colour. Five presets and a custom hex colour are available.
- **Gear** opens the key display settings and your shortcuts in Neovim.
- **Super+F8**, if [configured](docs/setup.md#keyboard-shortcut), toggles keys.
  The panel shows your current shortcut.

Recording and key display work independently. Keys stay off until you turn
them on, and the bar icon is always there.

Double-tap **Alt** to pause or resume the key display. Double-tap **Ctrl** to
make the overlay draggable, then again to let clicks pass through it.
Changing opacity or colour briefly restarts the overlay and resets its position.

## Remove

```bash
systemctl --user stop showmethekey-video.service
omarchy plugin disable io.github.ilyazar.capture-control
omarchy plugin remove io.github.ilyazar.capture-control
```

Remove the window rule and any shortcut you added. If you hid the stock
recording indicator, restore it. Your settings remain available for
reinstalling.

[Setup and settings](docs/setup.md) · [Development](docs/development.md)

Part of [Omarchy QOL](https://github.com/omarchy-QOL). MIT licensed;
Show Me The Key is Apache-2.0 licensed.

[showmethekey]: https://github.com/AlynxZhou/showmethekey
