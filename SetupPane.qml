import QtQuick
import qs.Commons
import qs.Ui

Column {
  id: root
  required property var capture
  readonly property Item focusTarget: accept.visible ? accept : root
  readonly property bool missing: capture && capture.missingPackages.length > 0
  signal dismissed()
  spacing: Style.space(10)

  Text {
    text: "Key capture setup"
    color: Color.popups.text
    font.family: Style.font.family
    font.pixelSize: Style.font.subtitle
    font.bold: true
  }

  Text {
    width: parent.width
    text: !root.capture || !root.capture.setupChecked ? "Checking dependencies…"
      : root.missing ? "Install dependencies first:"
      : root.capture.settingUp ? "Preparing key capture…"
      : "Key capture setup could not finish"
    wrapMode: Text.WordWrap
    color: Color.popups.text
    font.family: Style.font.family
    font.pixelSize: Style.font.body
  }

  Rectangle {
    width: parent.width
    implicitHeight: command.implicitHeight + Style.space(16)
    visible: root.missing
    color: Color.background
    border.color: Color.popups.border
    Text {
      id: command
      anchors.fill: parent
      anchors.margins: Style.space(8)
      text: "omarchy pkg add\n" + (root.capture ? root.capture.missingPackages.join(" ") : "")
      textFormat: Text.PlainText
      wrapMode: Text.WordWrap
      color: Color.popups.text
      font.family: "monospace"
      font.pixelSize: Style.font.bodySmall
    }
  }

  Text {
    width: parent.width
    visible: root.missing
    text: "Yes opens a terminal to prepare key capture.<br>"
      + "Packages use only the standard <tt>omarchy pkg add</tt>."
    textFormat: Text.StyledText
    wrapMode: Text.WordWrap
    color: Color.popups.text
    font.family: Style.font.family
    font.pixelSize: Style.font.caption
  }

  Row {
    width: parent.width
    spacing: Style.space(8)
    Button {
      id: accept
      width: (parent.width - parent.spacing) / 2
      text: root.missing ? "Yes" : "Retry"
      visible: root.capture && root.capture.setupChecked && !root.capture.settingUp
      bordered: true
      focusable: true
      onVisibleChanged: if (visible) Qt.callLater(function() { accept.forceActiveFocus() })
      onClicked: {
        if (root.missing) {
          root.capture.installDependencies()
          root.dismissed()
        } else root.capture.checkSetup()
      }
    }
    Button {
      width: accept.visible ? accept.width : parent.width
      text: root.missing ? "No" : "Close"
      bordered: true
      focusable: true
      onClicked: root.dismissed()
    }
  }
}
