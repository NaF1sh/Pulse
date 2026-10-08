import QtQuick

Item {
    id: media
    property var card: ({title: "", body: "", artwork: "", status: "Playing"})
    property bool reducedMotion: false
    property bool playing: card.status !== "Paused"
    implicitHeight: 72

    Rectangle {
        x: 12; y: 12; width: 48; height: 48; radius: 12
        color: pulseTheme.colors.border
        gradient: Gradient {
            GradientStop { position: 0; color: Qt.darker(pulseTheme.colors.accent, 1.7) }
            GradientStop { position: 1; color: pulseTheme.colors.background }
        }
        Text {
            anchors.centerIn: parent
            text: "♫"; font.pixelSize: 26
            color: pulseTheme.colors.accent
            visible: cover.status !== Image.Ready
        }
        Image {
            id: cover
            objectName: "albumCover"
            readonly property bool loaded: status === Image.Ready
            anchors.fill: parent; anchors.margins: 2
            source: media.card.artwork || ""
            sourceSize.width: 96; sourceSize.height: 96
            asynchronous: true
            fillMode: Image.PreserveAspectCrop
            visible: status === Image.Ready
        }
    }
    Column {
        x: 74; y: 12; width: parent.width - 124
        spacing: 3
        Text {
            text: media.card.status === "Demo" ? "MUSIC · DEMO" : "NOW PLAYING"
            color: pulseTheme.colors.accent
            font.pixelSize: 8; font.letterSpacing: 1.5; font.weight: Font.DemiBold
        }
        Text {
            width: parent.width
            text: media.card.title
            textFormat: Text.PlainText; elide: Text.ElideRight
            color: pulseTheme.colors.title
            font.pixelSize: pulseTheme.typography.title_size; font.weight: Font.DemiBold
        }
        Text {
            width: parent.width
            text: media.card.body
            textFormat: Text.PlainText; elide: Text.ElideRight
            color: pulseTheme.colors.body; font.pixelSize: 11
        }
    }
    Row {
        anchors.right: parent.right; anchors.rightMargin: 17
        anchors.verticalCenter: parent.verticalCenter
        spacing: 3; height: 20
        Repeater {
            model: 4
            Rectangle {
                required property int index
                width: 3; height: 10 + (index % 3) * 4
                anchors.verticalCenter: parent.verticalCenter
                radius: 1.5; color: pulseTheme.colors.accent
                opacity: 0.9
                transformOrigin: Item.Center
                SequentialAnimation on scale {
                    running: media.playing && media.visible && media.opacity > 0.1 && !media.reducedMotion
                    loops: Animation.Infinite
                    NumberAnimation { to: 0.45; duration: 380 + index * 90; easing.type: Easing.InOutSine }
                    NumberAnimation { to: 1; duration: 420 + index * 70; easing.type: Easing.InOutSine }
                }
            }
        }
    }
}
