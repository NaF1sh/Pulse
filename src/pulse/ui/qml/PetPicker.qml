import QtQuick
import QtQuick.Window

Window {
    id: picker
    width: 610; height: 540
    minimumWidth: 440; minimumHeight: 360
    title: "Pulse — choose your pet"
    color: "#17171f"
    visible: false
    flags: Qt.Window
    property var controls: null
    Item {
        anchors.fill: parent
        focus: true
        Keys.onEscapePressed: picker.close()
        Text {
            x: 24; y: 20
            text: "Choose your Pulse pet"
            font.pixelSize: 22; font.bold: true; color: "#f3efff"
        }
        Text {
            x: 24; y: 53; width: parent.width - 48
            text: "Click a pet to select · double-click the island to show/hide music"
            font.pixelSize: 12; color: "#aaa4bc"
            wrapMode: Text.Wrap
        }
        GridView {
            id: grid
            x: 16; y: 88
            width: parent.width - 32; height: parent.height - (picker.controls ? 190 : 152)
            clip: true
            cellWidth: width / Math.max(3, Math.floor(width / 110))
            cellHeight: 100
            boundsBehavior: Flickable.StopAtBounds
            model: pulsePets.catalog
            delegate: Item {
                required property var modelData
                width: grid.cellWidth; height: grid.cellHeight
                Rectangle {
                    anchors.fill: parent; anchors.margins: 5
                    radius: 12
                    color: tileMouse.containsMouse ? "#343044" : "#22212d"
                    border.width: modelData.id === pulsePets.current.id ? 2 : 1
                    border.color: modelData.id === pulsePets.current.id ? "#c4a8fa" : "#353142"
                }
                Face {
                    width: 44; height: 44
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: 14
                    design: modelData
                    animate: false
                }
                Text {
                    x: 8; y: 67; width: parent.width - 16
                    text: modelData.name
                    horizontalAlignment: Text.AlignHCenter
                    elide: Text.ElideRight; textFormat: Text.PlainText
                    font.pixelSize: 11; color: "#eee7fa"
                }
                MouseArea {
                    id: tileMouse
                    anchors.fill: parent; hoverEnabled: true
                    onClicked: { pulsePets.select(modelData.id); picker.close() }
                }
            }
        }
        Text {
            x: 24; anchors.bottom: parent.bottom; anchors.bottomMargin: picker.controls ? 68 : 25
            text: "Selected: " + pulsePets.current.name + " · scroll for more"
            font.pixelSize: 11; color: "#aaa4bc"
        }
        Rectangle {
            x: 24; anchors.bottom: parent.bottom; anchors.bottomMargin: 16
            width: 126; height: 32; radius: 8
            visible: picker.controls !== null
            color: musicMouse.containsMouse ? "#47405e" : "#302b40"
            Text {
                anchors.centerIn: parent
                text: picker.controls && picker.controls.musicVisible ? "Hide music" : "Show music"
                color: "#e5d6ff"; font.pixelSize: 12
            }
            MouseArea {
                id: musicMouse; anchors.fill: parent; hoverEnabled: true
                onClicked: { picker.controls.toggle_music(); picker.close() }
            }
        }
        Rectangle {
            anchors.right: parent.right; anchors.rightMargin: 24
            anchors.bottom: parent.bottom; anchors.bottomMargin: 16
            width: 92; height: 32; radius: 8
            color: exitMouse.containsMouse ? "#62394c" : "#3a2936"
            Text { anchors.centerIn: parent; text: "Quit Pulse"; color: "#f9c5d8"; font.pixelSize: 12 }
            MouseArea { id: exitMouse; anchors.fill: parent; hoverEnabled: true; onClicked: Qt.quit() }
        }
    }
}
