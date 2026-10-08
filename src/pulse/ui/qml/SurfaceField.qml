import QtQuick
import QtQuick.Controls
TextField {
    id: field
    padding: 10; color: "#f1f2f4"; font.pixelSize: 12
    placeholderTextColor: "#999da9"; selectionColor: "#66538e"
    background: Rectangle { radius: 8; color: "#1a1c22"; border.color: field.activeFocus ? "#b3a0fa" : "#353741" }
}
