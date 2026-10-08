import QtQuick
import QtQuick.Controls
SpinBox {
    id: control
    implicitWidth: 156; implicitHeight: 40
    leftPadding: 38; rightPadding: 38; editable: true
    opacity: enabled ? 1 : 0.5
    contentItem: TextInput {
        text: control.textFromValue(control.value, control.locale)
        font.pixelSize: 14; color: "#f1f2f4"; selectionColor: "#66538e"
        horizontalAlignment: Qt.AlignHCenter; verticalAlignment: Qt.AlignVCenter
        readOnly: !control.editable; validator: control.validator
        inputMethodHints: Qt.ImhDigitsOnly
    }
    up.indicator: Rectangle {
        x: control.width - width; width: 34; height: control.height; radius: 8
        color: control.up.pressed ? "#34303f" : "transparent"
        Text { anchors.centerIn: parent; text: "+"; color: "#b3a0fa"; font.pixelSize: 20 }
    }
    down.indicator: Rectangle {
        width: 34; height: control.height; radius: 8
        color: control.down.pressed ? "#34303f" : "transparent"
        Text { anchors.centerIn: parent; text: "−"; color: "#b3a0fa"; font.pixelSize: 20 }
    }
    background: Rectangle { radius: 8; color: "#1a1c22"; border.color: control.activeFocus ? "#b3a0fa" : "#353741" }
}
