import QtQuick
import Quickshell
import qs.Commons
import qs.Ui

PopupWindow {
  id: root

  required property Item anchorItem
  required property var bar
  property string text: ""
  property string rightText: ""
  property bool hovered: false
  property bool ready: false
  property bool suppressed: false
  readonly property var anchorWindow: anchorItem ? anchorItem.QsWindow.window : null

  function dismiss() { suppressed = true }

  onHoveredChanged: {
    ready = false
    suppressed = false
  }

  visible: !!anchorWindow && hovered && ready && !suppressed
  color: "transparent"
  implicitWidth: content.implicitWidth + 20
  implicitHeight: content.implicitHeight + 14

  Timer {
    interval: 400
    running: root.hovered && !root.suppressed
    onTriggered: root.ready = true
  }

  anchor {
    id: popupAnchor
    window: root.anchorWindow
    adjustment: PopupAdjustment.Slide
    edges: Edges.Top | Edges.Left
    gravity: Edges.Bottom | Edges.Right
    rect.width: 1
    rect.height: 1

    onAnchoring: {
      if (!root.anchorWindow || !root.anchorItem || !root.bar) return
      var target = root.anchorItem
      var x = target.width / 2 - root.implicitWidth / 2
      var y = target.height + 6
      if (root.bar.position === "bottom") {
        y = -root.implicitHeight - 6
      } else if (root.bar.position === "left") {
        x = target.width + 6
        y = target.height / 2 - root.implicitHeight / 2
      } else if (root.bar.position === "right") {
        x = -root.implicitWidth - 6
        y = target.height / 2 - root.implicitHeight / 2
      }
      var point = root.anchorWindow.itemPosition(target)
      popupAnchor.rect.x = Math.round(point.x + x)
      popupAnchor.rect.y = Math.round(point.y + y)
    }
  }

  BorderSurface {
    anchors.fill: parent
    color: Color.tooltip.background
    borderSpec: Border.surfaceSpec("tooltip", "border", Color.tooltip.border, 1)
    radius: Style.cornerRadius

    Row {
      id: content
      anchors.centerIn: parent
      spacing: Style.space(16)

      Text {
        id: label
        textFormat: Text.PlainText
        text: root.text
        color: Color.tooltip.text
        font.family: root.bar ? root.bar.fontFamily : Style.font.family
        font.pixelSize: Style.font.body
        horizontalAlignment: Text.AlignLeft
      }

      Text {
        visible: root.rightText !== ""
        textFormat: Text.PlainText
        text: root.rightText
        color: Color.tooltip.text
        font: label.font
        horizontalAlignment: Text.AlignRight
      }
    }
  }
}
