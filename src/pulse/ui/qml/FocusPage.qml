import QtQuick
import QtQuick.Controls

Flickable {
    id: page
    property var controller
    readonly property var session: controller ? controller.focus : null
    readonly property var sessionState: session ? session.state : ({phase: "idle", clock: "25:00", active: false, paused: false, completed: 0})
    clip: true; contentHeight: content.implicitHeight
    ScrollBar.vertical: ScrollBar {}
    Column {
        id: content; width: page.width - 12; spacing: 16
        Rectangle {
            width: parent.width; height: 182; radius: 16; color: "#1a1c22"; border.color: "#34303f"
            Column { anchors.centerIn: parent; spacing: 10
                Text { anchors.horizontalCenter: parent.horizontalCenter; text: ({idle:"MAKE TIME FOR ONE THING",focus:"FOCUS SESSION",break:"TAKE A BREATHER",break_ready:"NICE WORK. TIME FOR A BREAK.",done:"READY WHEN YOU ARE"})[page.sessionState.phase]; color: "#b3a0fa"; font.pixelSize: 10; font.letterSpacing: 1.4 }
                Text { anchors.horizontalCenter: parent.horizontalCenter; text: page.sessionState.phase === "idle" ? focusMinutes.value + ":00" : page.sessionState.clock; color: "#f1f2f4"; font.pixelSize: 54; font.weight: Font.Light }
                Text { anchors.horizontalCenter: parent.horizontalCenter; text: page.sessionState.paused ? "Paused · take your time" : page.sessionState.completed + " focus sessions completed this run"; color: "#999da9"; font.pixelSize: 12 }
            }
        }
        Row { spacing: 16; enabled: page.sessionState.phase === "idle" || page.sessionState.phase === "done"
            Column { spacing: 6
                Text { text: "Focus · minutes"; color: "#b9bdc8"; font.pixelSize: 12 }
                MinutePicker { id: focusMinutes; from: 1; to: 180; value: 25; editable: true; Accessible.name: "Focus minutes" }
            }
            Column { spacing: 6
                Text { text: "Break · minutes"; color: "#b9bdc8"; font.pixelSize: 12 }
                MinutePicker { id: breakMinutes; from: 1; to: 60; value: 5; editable: true; Accessible.name: "Break minutes" }
            }
        }
        Row { spacing: 8
            SurfaceButton { objectName: "startFocus"; text: "Start focus"; highlighted: true; visible: page.sessionState.phase === "idle" || page.sessionState.phase === "done"; onClicked: page.session.start(focusMinutes.value, breakMinutes.value) }
            SurfaceButton { text: "Start break"; highlighted: true; visible: page.sessionState.phase === "break_ready"; onClicked: page.session.startBreak() }
            SurfaceButton { objectName: "pauseFocus"; text: page.sessionState.paused ? "Resume" : "Pause"; visible: page.sessionState.phase === "focus" || page.sessionState.phase === "break"; onClicked: page.session.togglePause() }
            SurfaceButton { text: "End session"; visible: page.sessionState.active; onClicked: page.session.stop() }
        }
        Text { width: parent.width; text: "Your countdown stays in the island. Notifications appear briefly, then the timer returns. Pulse reminds you when to take a break; you decide when to start it."; color: "#999da9"; font.pixelSize: 12; wrapMode: Text.Wrap; lineHeight: 1.4 }
        Text { width: parent.width; text: "Sessions run while Pulse is open. Do not disturb remains your choice in General."; color: "#999da9"; font.pixelSize: 11; wrapMode: Text.Wrap }
    }
}
