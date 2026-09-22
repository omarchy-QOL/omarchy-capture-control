hl.window_rule({
  name = "capture-control-overlay",
  match = {
    class = "^one\\.alynx\\.showmethekey$",
    title = "^Floating Window - Show Me The Key$",
  },
  float = true,
  pin = true,
  no_initial_focus = true,
  move = { "(monitor_w-window_w)/2", "monitor_h-window_h-40" },
  no_blur = true,
  no_shadow = true,
  border_size = 0,
  no_dim = true,
  tag = "-default-opacity",
  opacity = "1 1",
})
