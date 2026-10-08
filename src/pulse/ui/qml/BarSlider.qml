import QtQuick
import QtQuick.Controls
Slider {
    id: control
    implicitHeight: 28
    background: Rectangle {
        x: control.leftPadding; y: control.topPadding + control.availableHeight / 2 - height / 2
        width: control.availableWidth; height: 4; radius: 2; color: "#353741"
        Rectangle { width: control.visualPosition * parent.width; height: parent.height; radius: 2; color: "#b3a0fa" }
    }
    handle: Rectangle {
        x: control.leftPadding + control.visualPosition * (control.availableWidth - width)
        y: control.topPadding + control.availableHeight / 2 - height / 2
        width: 16; height: 16; radius: 8; color: control.pressed ? "#b3a0fa" : "#f1f2f4"
        border.color: control.activeFocus ? "#b3a0fa" : "#353741"; border.width: 2
    }
}
