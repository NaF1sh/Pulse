import QtQuick
import QtQuick.Controls
Button {
    id: control
    padding: 12; implicitHeight: 38; hoverEnabled: true
    Accessible.name: text
    contentItem: Text {
        text: control.text; color: control.highlighted ? "#171320" : "#e2e0e8"
        opacity: control.enabled ? 1 : 0.35
        font.pixelSize: 12; font.weight: control.highlighted ? Font.DemiBold : Font.Normal
        horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
    }
    background: Rectangle {
        radius: 8
        color: control.highlighted ? (control.down ? "#9681df" : "#c0acf9") : (control.hovered ? "#292b35" : "#1a1c22")
        opacity: control.enabled ? 1 : 0.5
        border.color: control.activeFocus ? "#e0d4ff" : control.highlighted ? "transparent" : "#353741"
    }
}
