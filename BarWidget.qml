pragma ComponentBehavior: Bound
import QtQuick
import Quickshell.Io
import qs.Commons
import qs.Ui

Panel {
  id: root
  moduleName: "io.github.ilyazar.capture-control"

  readonly property var capture: bar && bar.shell ? bar.shell.serviceFor(moduleName) : null
  property bool editingColor: false
  property var systemColors: ({})
  onOpenedChanged: if (opened && capture) {
    capture.refresh()
    capture.refreshShortcuts()
  }
  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  FileView {
    id: themeColors
    path: Color.currentThemePath + "/colors.toml"
    watchChanges: true
    printErrors: false
    onLoaded: root.systemColors = Color.parseShell("[palette]\n" + text())
    onFileChanged: reload()
    onLoadFailed: root.systemColors = ({})
  }

  Connections {
    target: Color
    function onThemeShellValuesChanged() { themeColors.reload() }
  }

  BarIconButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: "󰻂"
    useActiveColor: false
    active: root.capture && root.capture.recording
    tooltipText: active ? "Stop recording" : "Screen Recording"
    onPressed: function(mouseButton) {
      if (mouseButton === Qt.RightButton) root.toggle()
      else if (mouseButton === Qt.LeftButton && root.bar) {
        root.close()
        root.bar.run(root.capture && root.capture.recording
          ? "omarchy-capture-screenrecording --stop-recording"
          : "omarchy-menu toggle trigger.capture.screenrecord")
      }
    }
  }

  KeyboardPanel {
    id: panel
    objectName: "capturePanel"
    anchorItem: button
    owner: root
    bar: root.bar
    open: root.opened
    focusTarget: captureToggle
    contentWidth: panel.fittedContentWidth(Style.space(340))
    contentHeight: panel.fittedContentHeight(content.implicitHeight)

    Column {
      id: content
      width: parent.width
      spacing: Style.space(10)
      Keys.onEscapePressed: root.close()

      Item {
        width: parent.width
        implicitHeight: Math.max(gear.implicitHeight, shortcuts.implicitHeight, captureToggle.implicitHeight)

        Button {
          id: gear
          anchors.left: parent.left
          anchors.verticalCenter: parent.verticalCenter
          iconText: "󰒓"
          tooltipText: "Edit capture settings and keybindings"
          focusable: true
          onClicked: {
            root.close()
            if (root.capture) root.capture.edit()
          }
        }

        Text {
          id: shortcuts
          anchors.left: gear.right
          anchors.leftMargin: Style.space(10)
          anchors.right: captureState.left
          anchors.rightMargin: Style.space(10)
          anchors.verticalCenter: parent.verticalCenter
          text: root.capture ? "Start  " + root.capture.startShortcut
            + "\nStop   " + root.capture.stopShortcut : ""
          color: Color.popups.text
          font.family: Style.font.family
          font.pixelSize: Style.font.body
          elide: Text.ElideRight
        }

        Text {
          id: captureState
          anchors.right: captureToggle.left
          anchors.rightMargin: Style.space(6)
          anchors.verticalCenter: captureToggle.verticalCenter
          text: captureToggle.checked ? "ON" : "OFF"
          font: shortcuts.font
          color: captureToggle.checked
            ? root.systemColors["palette.green"] || root.systemColors["palette.color2"] || Color.accent
            : root.systemColors["palette.red"] || root.systemColors["palette.color1"] || Color.urgent
        }

        ToggleSwitch {
          id: captureToggle
          objectName: "captureToggle"
          anchors.right: parent.right
          anchors.verticalCenter: parent.verticalCenter
          trackHeight: Math.round(shortcuts.font.pixelSize * 1.2)
          cursorPad: Style.space(3)
          activeFocusOnTab: true
          hasCursor: activeFocus
          checked: root.capture && root.capture.capturing
          busy: !root.capture || root.capture.busy
          Accessible.name: "Key capture"
          onToggled: root.capture.run(checked ? "stop" : "start")
          Keys.onReturnPressed: if (!busy) toggled()
          Keys.onEnterPressed: if (!busy) toggled()
          Keys.onSpacePressed: if (!busy) toggled()

          PanelToolTip {
            visible: captureToggle.containsMouse
            text: captureToggle.checked ? "Stop key capture" : "Start key capture"
            fontFamily: Style.font.family
          }
        }
      }

      Row {
        width: parent.width
        spacing: Style.space(10)

        Text {
          id: opacityTitle
          text: "Background"
          color: Color.popups.text
          font.family: Style.font.family
          font.pixelSize: Style.font.body
          anchors.verticalCenter: parent.verticalCenter
        }

        PanelSlider {
          id: opacitySlider
          width: parent.width - opacityTitle.width - opacityLabel.width - parent.spacing * 2
          bar: root.bar
          minimum: 0
          maximum: 100
          step: 5
          integer: true
          activeFocusOnTab: true
          Keys.onLeftPressed: root.capture.run("opacity", Math.max(0, value - 5) / 100)
          Keys.onRightPressed: root.capture.run("opacity", Math.min(100, value + 5) / 100)
          value: root.capture ? Math.round(root.capture.backgroundOpacity * 100) : 30
          enabled: root.capture && !root.capture.busy
          onReleased: function(value) { root.capture.run("opacity", value / 100) }
        }

        Text {
          id: opacityLabel
          width: Style.space(36)
          text: Math.round(opacitySlider.liveValue) + "%"
          color: Color.popups.text
          font.family: Style.font.family
          font.pixelSize: Style.font.caption
          anchors.verticalCenter: parent.verticalCenter
        }
      }

      ColorDropdown {
        objectName: "colorPicker"
        width: parent.width
        value: root.editingColor ? "custom" : (root.capture ? root.capture.textColor : "#ffffff")
        customColor: root.capture ? root.capture.textColor : "#ffffff"
        presets: [
          {label: "White", value: "#ffffff"},
          {label: "Light teal", value: "#94e2d5"},
          {label: "Red", value: "#f38ba8"},
          {label: "Yellow", value: "#f9e2af"},
          {label: "Purple", value: "#cba6f7"}
        ]
        enabled: root.capture && !root.capture.busy
        onChanged: function(value) {
          root.editingColor = value === "custom"
          if (root.editingColor) {
            customColorField.text = root.capture.textColor
            Qt.callLater(function() {
              customColorField.selectAll()
              customColorField.forceActiveFocus()
            })
          } else root.capture.run("color", value)
        }
      }

      Row {
        width: parent.width
        spacing: Style.space(8)
        visible: root.editingColor
        TextField {
          id: customColorField
          width: parent.width - applyColor.width - parent.spacing
          placeholderText: "#ffffff"
          enabled: root.capture && !root.capture.busy
          foreground: Color.popups.text
          font.family: Style.font.family
          validator: RegularExpressionValidator { regularExpression: /^#[0-9a-fA-F]{6}$/ }
          onAccepted: if (acceptableInput) root.capture.run("color", text)
        }
        Button {
          id: applyColor
          text: "Apply"
          bordered: true
          fontSize: Style.font.bodySmall
          focusable: true
          enabled: customColorField.acceptableInput && root.capture && !root.capture.busy
          onClicked: root.capture.run("color", customColorField.text)
        }
      }

      Text {
        visible: text !== ""
        text: root.capture ? root.capture.error : ""
        width: parent.width
        wrapMode: Text.WordWrap
        color: Color.urgent
        font.family: Style.font.family
        font.pixelSize: Style.font.caption
      }
    }
  }
}
