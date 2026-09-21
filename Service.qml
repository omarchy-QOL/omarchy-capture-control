import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io

Item {
  id: root

  property QtObject shell: null
  property bool recording: false
  property bool capturing: false
  property real backgroundOpacity: 0.3
  property string textColor: "#ffffff"
  property string error: ""
  property string toggleShortcut: "Unbound"
  property var pendingAction: null
  readonly property bool busy: action.running
  readonly property string helper: decodeURIComponent(Qt.resolvedUrl("control.py").toString().replace(/^file:\/\//, ""))

  function refresh() {
    if (!status.running && !action.running) status.running = true
  }

  function run(command, value) {
    if (action.running) {
      pendingAction = [command, value]
      return
    }
    error = ""
    if (command === "opacity") backgroundOpacity = Number(value)
    if (command === "color") textColor = String(value)
    if (command === "start" || command === "stop") capturing = command === "start"
    action.command = ["python3", helper, command]
    if (value !== undefined) action.command = action.command.concat([String(value)])
    action.running = true
  }

  function edit() {
    Quickshell.execDetached(["python3", helper, "edit"])
  }

  function refreshShortcuts() {
    if (!bindings.running) bindings.running = true
  }

  function shortcut(bindings, description) {
    var binding = bindings.find(function(item) { return item.description === description })
    if (!binding) return "Unbound"
    return [[64, "Super"], [4, "Ctrl"], [8, "Alt"], [1, "Shift"]]
      .filter(function(modifier) { return binding.modmask & modifier[0] })
      .map(function(modifier) { return modifier[1] }).concat([binding.key]).join("+")
  }

  Component.onCompleted: {
    refresh()
    refreshShortcuts()
  }

  Connections {
    target: Hyprland
    function onRawEvent(event) {
      if (event.name === "configreloaded") root.refreshShortcuts()
    }
  }

  IpcHandler {
    target: "keycapture"
    function start(): void { root.run("start") }
    function stop(): void { root.run("stop") }
    function toggle(): void { root.run(root.capturing ? "stop" : "start") }
  }

  Timer {
    interval: 1000
    running: true
    repeat: true
    onTriggered: root.refresh()
  }

  Process {
    id: status
    command: ["python3", root.helper, "status"]
    stderr: StdioCollector { id: statusError }
    onExited: function(code) {
      if (code !== 0) root.error = statusError.text.trim() || "Could not read capture state"
    }
    stdout: StdioCollector {
      onStreamFinished: {
        try {
          var state = JSON.parse(text)
          if (root.busy) return
          root.recording = state.recording
          root.capturing = state.running
          root.backgroundOpacity = state.opacity
          root.textColor = state.textColor
        } catch (error) { root.error = "Could not read capture state" }
      }
    }
  }

  Process {
    id: action
    stderr: StdioCollector { id: actionError }
    onExited: function(code) {
      if (code !== 0) root.error = actionError.text.trim() || "Capture command failed"
      if (root.pendingAction) {
        var next = root.pendingAction
        root.pendingAction = null
        root.run(next[0], next[1])
      } else root.refresh()
    }
  }

  Process {
    id: bindings
    command: ["hyprctl", "binds", "-j"]
    stdout: StdioCollector {
      onStreamFinished: {
        try {
          var entries = JSON.parse(text)
          root.toggleShortcut = root.shortcut(entries, "Toggle key capture")
        } catch (error) {
          root.toggleShortcut = "Unbound"
        }
      }
    }
  }
}
