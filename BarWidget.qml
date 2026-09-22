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
    onPressed: function(mouseButton) {
      captureTooltip.dismiss()
      if (mouseButton === Qt.RightButton) root.toggle()
      else if (mouseButton === Qt.LeftButton && root.bar) {
        root.close()
        root.bar.run(root.capture && root.capture.recording
          ? "omarchy-capture-screenrecording --stop-recording"
          : "omarchy-menu toggle trigger.capture.screenrecord")
      }
    }
  }

  CaptureTooltip {
    id: captureTooltip
    anchorItem: button
    bar: root.bar
    text: "Left-click:\nRight-click:"
    rightText: (button.active ? "stop recording" : "screen recording")
      + "\nkey capture settings"
    hovered: button.tooltipHovered && !root.opened
      && !(root.bar && root.bar.activePopout)
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
      Keys.onPressed: function(event) {
        if (event.key === Qt.Key_Q && event.modifiers === Qt.NoModifier && !customColorField.activeFocus) {
          root.close()
          event.accepted = true
        }
      }

      Item {
        width: parent.width
        implicitHeight: heading.implicitHeight + Style.space(4) + subtitle.implicitHeight

        Text {
          id: heading
          anchors.left: parent.left
          width: captureState.x - Style.space(10)
          text: "Key capture settings"
          color: Color.popups.text
          font.family: Style.font.family
          font.pixelSize: Style.font.subtitle
          font.bold: true
        }

        Text {
          id: subtitle
          anchors.left: parent.left
          anchors.top: heading.bottom
          anchors.topMargin: Style.space(4)
          width: bindingsLabel.x - Style.space(10)
          text: "Use mouse to move overlay"
          color: Color.popups.text
          font.family: Style.font.family
          font.pixelSize: Style.font.caption
          wrapMode: Text.WordWrap
        }
        Text {
          id: captureState
          anchors.right: captureToggle.left
          anchors.rightMargin: Style.space(6)
          anchors.verticalCenter: heading.verticalCenter
          text: captureToggle.checked ? "ON" : "OFF"
          font.family: Style.font.family
          font.pixelSize: Style.font.caption
          color: captureToggle.checked
            ? root.systemColors["palette.green"] || root.systemColors["palette.color2"] || Color.accent
            : root.systemColors["palette.red"] || root.systemColors["palette.color1"] || Color.urgent
        }

        ToggleSwitch {
          id: captureToggle
          objectName: "captureToggle"
          anchors.right: parent.right
          anchors.verticalCenter: heading.verticalCenter
          trackHeight: Style.space(11)
          cursorPad: Style.space(2)
          activeFocusOnTab: true
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

        Text {
          id: bindingsLabel
          anchors.right: bindingsOnlyToggle.left
          anchors.rightMargin: Style.space(6)
          anchors.verticalCenter: subtitle.verticalCenter
          text: bindingsOnlyToggle.checked ? "Only Omarchy" : "All bindings"
          color: Color.popups.text
          font.family: Style.font.family
          font.pixelSize: Style.font.caption
        }

        ToggleSwitch {
          id: bindingsOnlyToggle
          objectName: "bindingsOnlyToggle"
          anchors.right: parent.right
          anchors.verticalCenter: subtitle.verticalCenter
          trackHeight: captureToggle.trackHeight
          cursorPad: captureToggle.cursorPad
          activeFocusOnTab: true
          hasCursor: activeFocus
          foreground: Color.popups.text
          checked: root.capture && root.capture.onlyOmarchyBindings
          busy: !root.capture || root.capture.busy
          Accessible.name: "Only Omarchy bindings"
          onToggled: root.capture.run("bindings-only", !checked)
          Keys.onReturnPressed: if (!busy) toggled()
          Keys.onEnterPressed: if (!busy) toggled()
          Keys.onSpacePressed: if (!busy) toggled()

          CaptureTooltip {
            anchorItem: bindingsOnlyToggle
            bar: root.bar
            hovered: bindingsOnlyToggle.containsMouse && root.opened
            text: "Hiding ordinary typing"
          }
        }
      }

      Item {
        width: parent.width
        implicitHeight: Math.max(gear.implicitHeight, shortcuts.implicitHeight)

        Button {
          id: gear
          anchors.right: parent.right
          anchors.verticalCenter: parent.verticalCenter
          iconText: "󰒓"
          iconSize: Style.font.icon * 1.5
          tooltipText: "Edit key capture settings and keybindings"
          focusable: true
          onClicked: {
            root.close()
            if (root.capture) root.capture.edit()
          }
        }

        Text {
          id: shortcuts
          anchors.left: parent.left
          anchors.right: gear.left
          anchors.rightMargin: Style.space(10)
          anchors.verticalCenter: parent.verticalCenter
          text: root.capture ? "Start / Stop:  " + root.capture.toggleShortcut : ""
          color: Color.popups.text
          font.family: Style.font.family
          font.pixelSize: Style.font.body
          elide: Text.ElideRight
        }
      }

      Row {
        width: parent.width
        spacing: Style.space(10)

        Text {
          id: opacityTitle
          width: Math.max(implicitWidth, Style.space(36))
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
