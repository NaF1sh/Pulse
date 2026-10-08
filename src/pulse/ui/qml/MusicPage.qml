import QtQuick
import QtQuick.Controls

Column {
    id: page
    property bool desktopSupported: true
    property var controller
    readonly property var playback: controller ? controller.musicState : ({available:false, busy:false, error:"", title:"", artist:"", artwork:""})
    spacing: 18
    Rectangle {
        width: parent.width; height: 152; radius: 16; color: "#1a1c22"; border.color: "#2b2d36"
        Rectangle { x: 20; y: 24; width: 100; height: 100; radius: 14; color: "#30283f"
            Text { anchors.centerIn: parent; text: "♫"; color: "#b3a0fa"; font.pixelSize: 38 }
            Image { anchors.fill: parent; anchors.margins: 2; source: page.playback.artwork || ""; fillMode: Image.PreserveAspectCrop; asynchronous: true; sourceSize.width: 200; sourceSize.height: 200 }
        }
        Column { x: 140; width: parent.width - 160; anchors.verticalCenter: parent.verticalCenter; spacing: 10
            Text { text: page.playback.available ? (page.playback.playing ? "NOW PLAYING" : "PAUSED") : "YOUR MUSIC, CLOSE AT HAND"; color: "#b3a0fa"; font.pixelSize: 9; font.letterSpacing: 1.2 }
            Text { width: parent.width; text: !page.desktopSupported ? "Windows music integration" : page.playback.title || "Play something you love"; color: "#f1f2f4"; font.pixelSize: 17; font.bold: true; elide: Text.ElideRight; textFormat: Text.PlainText }
            Text { width: parent.width; text: !page.desktopSupported ? "Not available in this preview." : page.playback.artist || "Open your music app to get started."; color: "#999da9"; font.pixelSize: 12; elide: Text.ElideRight; textFormat: Text.PlainText }
        }
    }
    Row { spacing: 10
        SurfaceButton { text: "Previous"; enabled: !!page.playback.previous && !page.playback.busy; onClicked: page.controller.controlMusic("previous") }
        SurfaceButton { text: page.playback.playing ? "Pause" : "Play"; highlighted: true; enabled: !!page.playback.toggle && !page.playback.busy; onClicked: page.controller.controlMusic("toggle") }
        SurfaceButton { text: "Next"; enabled: !!page.playback.next && !page.playback.busy; onClicked: page.controller.controlMusic("next") }
    }
    Text { width: parent.width; text: page.playback.error || "Control the active player without switching windows. You can also use the buttons directly in the island."; color: page.playback.error ? "#f0a5ae" : "#999da9"; font.pixelSize: 12; wrapMode: Text.Wrap; lineHeight: 1.4 }
    Text { width: parent.width; text: "Works with players that share desktop media controls (MPRIS). Unsupported controls are disabled. If several players are open, Pulse prefers the one already playing."; color: "#999da9"; font.pixelSize: 11; wrapMode: Text.Wrap }
}
