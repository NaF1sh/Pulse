import QtQuick
import QtQuick.Controls

Rectangle {
    id: drawer
    property var tasks
    color: "#17181e"; radius: 12
    MouseArea { anchors.fill: parent; acceptedButtons: Qt.LeftButton | Qt.RightButton }
    Text { x: 12; y: 10; text: "TASK ACTIVITY"; color: "#b3a0fa"; font.pixelSize: 9; font.letterSpacing: 1.1 }
    Button {
        anchors.right: parent.right; anchors.rightMargin: 8; y: 3; width: 104; height: 28
        text: "Clear finished"; onClicked: drawer.tasks.clearFinished()
        contentItem: Text { text: parent.text; color: "#b9bdc8"; font.pixelSize: 10; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
        background: Rectangle { radius: 6; color: parent.down ? "#353741" : "#242630" }
    }
    ListView {
        id: list; x: 8; y: 36; width: parent.width - 16; height: parent.height - 66
        clip: true; spacing: 6; model: drawer.tasks ? drawer.tasks.entries : []
        ScrollBar.vertical: ScrollBar {}
        delegate: Rectangle {
            required property var modelData
            width: list.width; height: 134; radius: 8; color: "#22242c"
            Column { x: 10; y: 8; width: parent.width - 20; spacing: 5
                Text { width: parent.width; text: modelData.title; textFormat: Text.PlainText; elide: Text.ElideRight; color: "#f1f2f4"; font.pixelSize: 12; font.bold: true }
                Text { width: parent.width; text: modelData.source + " · " + modelData.label + (modelData.dismissed ? " · dismissed" : ""); textFormat: Text.PlainText; elide: Text.ElideRight; color: modelData.state.startsWith("needs-") || modelData.state === "failed" ? "#e5bf8d" : "#b3a0fa"; font.pixelSize: 10 }
                Text { width: parent.width; height: 32; text: modelData.message || "No additional details provided."; textFormat: Text.PlainText; wrapMode: Text.Wrap; maximumLineCount: 2; elide: Text.ElideRight; color: "#b9bdc8"; font.pixelSize: 11 }
                Row { spacing: 6
                    SurfaceButton { text: modelData.state.startsWith("needs-") ? "Review request" : "Open result"; visible: modelData.hasTarget; implicitHeight: 28; padding: 7; onClicked: drawer.tasks.open(modelData.id) }
                    SurfaceButton { text: "Dismiss alert"; visible: !modelData.dismissed; implicitHeight: 28; padding: 7; onClicked: drawer.tasks.dismiss(modelData.id) }
                    Text { anchors.verticalCenter: parent.verticalCenter; text: modelData.updatedLabel; color: "#858a99"; font.pixelSize: 9 }
                }
            }
        }
        Text { anchors.centerIn: parent; visible: list.count === 0; text: "No reported tasks yet"; color: "#999da9"; font.pixelSize: 12 }
    }
    Text { x: 12; anchors.bottom: parent.bottom; anchors.bottomMargin: 8; width: parent.width - 24; text: drawer.tasks && drawer.tasks.summary.error || "Approvals stay in the original tool."; elide: Text.ElideRight; color: drawer.tasks && drawer.tasks.summary.error ? "#f0a5ae" : "#858a99"; font.pixelSize: 10 }
}
