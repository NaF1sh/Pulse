import QtQuick
import QtQuick.Window
Window {
    id: root
    width: 420; height: 160
    visible: false
    color: "transparent"
    title: "Pulse"
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus
    property bool expanded: false
    property bool open: false
    property bool contentVisible: false
    property string reactionMood: ""
    property var displayed: ({app: "", title: "Pulse", body: "", kind: "message", value: 0, id: -1})
    property var incoming: displayed
    onExpandedChanged: refreshCard()
    function refreshCard() {
        incoming = pulseController.card
        if (!pulseController.active && !expanded) {
            swapTimer.stop()
            contentVisible = false
            closeTimer.restart()
            return
        }
        closeTimer.stop()
        if (!open) {
            displayed = incoming
            open = true
            contentVisible = true
            return
        }
        // Queue-only changes must not blink the current card.
        if (JSON.stringify(incoming) === JSON.stringify(displayed)) {
            contentVisible = true
            return
        }
        if (incoming.id === displayed.id) {
            displayed = incoming
            contentVisible = true
            return
        }
        contentVisible = false
        swapTimer.restart()
    }
    Connections {
        target: pulseController
        function onChanged() {
            if (!pulseController.musicVisible && root.mediaShown) root.expanded = false
            root.refreshCard()
        }
        function onReaction(mood) {
            if (root.reducedMotion) return
            root.reactionMood = mood
            reactionTimer.restart()

        }
    }
    Timer {
        id: reactionTimer
        interval: root.reactionMood === "happy" ? 3000 : 800
        onTriggered: root.reactionMood = ""
    }
    Timer {
        id: swapTimer
        interval: root.reducedMotion ? 70 : pulseTheme.animation.fade
        onTriggered: { root.displayed = root.incoming; root.contentVisible = true }
    }
    Timer {
        id: closeTimer
        interval: root.reducedMotion ? 70 : pulseTheme.animation.fade
        onTriggered: root.open = false
    }
    property bool reducedMotion: false
    property bool debugVisible: false
    property int frames: 0
    property int fps: 0
    property string phase: Math.abs(island.width - (open ? cardWidth : 30)) < 1 ? (open ? "hold" : "idle") : (open ? "enter" : "exit")
    property bool mediaShown: displayed.kind === "media"
    property bool levelShown: displayed.kind === "level"
    property real cardWidth: mediaShown ? Math.min(pulseTheme.layout.max_width, Math.max(pulseTheme.layout.min_width, 330))
                            : levelShown ? pulseTheme.layout.min_width
                            : Math.min(pulseTheme.layout.max_width, 280)
    property var notificationActions: displayed.actions || []
    property real cardHeight: mediaShown ? 72 : levelShown ? 58 : (displayed.kind === "progress" ? 68 : 54) + (notificationActions.length ? 32 : 0)
    property real cardOpacity: root.contentVisible && root.open && island.width >= root.cardWidth - 2 ? 1 : 0
    signal maskChanged(real left, real top, real w, real h, real radius)
    function syncMask() {
        let maskRadius = !root.open && pulsePets.current.species !== "round" ? 1 : island.radius
        maskChanged(island.x, island.y, island.width, island.height, maskRadius)
    }
    Connections {
        target: pulsePets
        function onChanged() { root.syncMask() }
    }
    SettingsWindow { id: settingsWindow; preferences: typeof pulsePreferences !== "undefined" ? pulsePreferences : null }
    function openSettings() { settingsWindow.open() }
    PetPicker { id: petPicker; controls: pulseController }
    Timer {
        id: idleClickTimer
        interval: Qt.styleHints.mouseDoubleClickInterval
        onTriggered: root.expanded = !root.expanded
    }
    Rectangle {
        id: island
        objectName: "islandSurface"
        x: (root.width - width) / 2; y: 12
        width: root.open ? root.cardWidth : 30
        height: root.open ? root.cardHeight : 30
        radius: root.open ? Math.min(pulseTheme.layout.radius, 18) : 15
        clip: root.open
        color: pulseTheme.colors.background
        border.color: pulseTheme.colors.border; border.width: 1
        onXChanged: root.syncMask()
        onYChanged: root.syncMask()
        onRadiusChanged: root.syncMask()
        onWidthChanged: root.syncMask()
        onHeightChanged: root.syncMask()
        Behavior on width {
            enabled: !root.reducedMotion
            NumberAnimation { duration: 260; easing.type: Easing.InOutCubic }
        }
        Behavior on height {
            enabled: !root.reducedMotion
            NumberAnimation { duration: 260; easing.type: Easing.InOutCubic }
        }
        Face {
            anchors.centerIn: parent
            design: pulsePets.current
            expressionOverride: root.reactionMood
            hovered: islandMouse.containsMouse
            animate: !root.reducedMotion && !root.open && root.visible
            opacity: !root.open && island.width < 60 ? 1 : 0
            Behavior on opacity { NumberAnimation { duration: root.reducedMotion ? 70 : 100 } }
        }
        Rectangle {
            x: 11; y: 12; width: 30; height: 30; radius: 10
            color: Qt.lighter(pulseTheme.colors.background, 1.3)
            visible: !root.mediaShown && !root.levelShown
            opacity: root.cardOpacity
            Face { anchors.centerIn: parent; width: 25; height: 25; design: pulsePets.current; animate: false }
        }
        Column {
            id: content
            visible: !root.mediaShown && !root.levelShown
            x: 51; y: 9
            width: root.cardWidth - 79
            spacing: 3
            opacity: root.cardOpacity
            Behavior on opacity { NumberAnimation { duration: root.reducedMotion ? 70 : pulseTheme.animation.fade } }
            Text {
                id: heading
                width: parent.width
                text: root.displayed.title
                color: pulseTheme.colors.title; font.pixelSize: 12; font.weight: Font.DemiBold
                elide: Text.ElideRight; textFormat: Text.PlainText
            }
            Text {
                id: message
                width: parent.width
                text: pulseController.actionError || root.displayed.body || (pulseController.active ? "" : "Waiting for notifications")
                visible: text.length > 0
                color: pulseTheme.colors.body; font.pixelSize: 11
                wrapMode: Text.NoWrap; maximumLineCount: 1
                elide: Text.ElideRight; textFormat: Text.PlainText
            }
            Item {
                width: parent.width
                height: visible ? 12 : 0
                visible: root.displayed.kind === "progress" || root.displayed.kind === "level"
                Rectangle {
                    anchors.left: parent.left; anchors.right: percentage.left
                    anchors.rightMargin: 10; anchors.verticalCenter: parent.verticalCenter
                    height: 4; radius: 2; color: pulseTheme.colors.border
                    Rectangle {
                        width: parent.width * root.displayed.value
                        height: parent.height; radius: 2
                        color: root.displayed.kind === "level" ? pulseTheme.colors.accent : pulseTheme.colors.progress
                        Behavior on width { NumberAnimation { duration: root.reducedMotion ? 0 : pulseTheme.animation.meter } }
                    }
                }
                Text {
                    id: percentage
                    anchors.right: parent.right
                    text: root.displayed.valueLabel || Math.round(root.displayed.value * 100) + "%"
                    color: pulseTheme.colors.body; font.pixelSize: pulseTheme.typography.label_size
                }
            }
            Row {
                visible: root.displayed.kind === "media"
                height: visible ? 14 : 0
                spacing: 8
                Text { text: "♪"; color: pulseTheme.colors.accent; font.pixelSize: pulseTheme.typography.body_size }
                Text {
                    text: root.displayed.status === "Paused" ? "Paused"
                          : root.displayed.status === "Demo" ? "Now playing · Demo" : "Now playing"
                    color: pulseTheme.colors.muted; font.pixelSize: pulseTheme.typography.label_size
                }
            }
        }
        MediaCard {
            anchors.fill: parent
            visible: root.mediaShown
            card: root.displayed
            reducedMotion: root.reducedMotion
            opacity: root.cardOpacity
            Behavior on opacity { NumberAnimation { duration: root.reducedMotion ? 70 : pulseTheme.animation.fade } }
        }
        LevelCard {
            anchors.fill: parent
            visible: root.levelShown
            card: root.displayed
            reducedMotion: root.reducedMotion
            opacity: root.cardOpacity
            Behavior on opacity { NumberAnimation { duration: root.reducedMotion ? 70 : pulseTheme.animation.fade } }
        }
        MouseArea {
            id: islandMouse
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            onClicked: mouse => {
                if (mouse.button === Qt.RightButton) { if (settingsWindow.preferences) root.openSettings(); else { petPicker.show(); petPicker.requestActivate() } }
                else if (root.mediaShown && pulseController.active) { /* Double-click hides music. */ }
                else if (pulseController.active) {
                    if (root.levelShown) pulseController.dismiss()
                    else pulseController.activate(root.displayed.id)
                }
                else if (!pulseController.musicVisible) idleClickTimer.restart()
                else root.expanded = !root.expanded
            }
            onDoubleClicked: mouse => {
                if (mouse.button === Qt.LeftButton && (root.mediaShown || !pulseController.active)) {
                    idleClickTimer.stop()
                    root.expanded = false
                    pulseController.toggle_music()
                }
            }
        }
        Rectangle {
            anchors.right: parent.right; anchors.rightMargin: 7; y: 6
            width: 20; height: 20; radius: 10
            visible: root.open && !root.mediaShown && !root.levelShown
            opacity: root.cardOpacity
            color: dismissMouse.containsMouse ? pulseTheme.colors.border : "transparent"
            Text { anchors.centerIn: parent; text: "×"; font.pixelSize: 15; color: pulseTheme.colors.muted }
            MouseArea {
                id: dismissMouse; anchors.fill: parent; hoverEnabled: true
                onClicked: pulseController.close(root.displayed.id)
            }
        }
        Flickable {
            x: 51; y: root.cardHeight - 33
            width: root.cardWidth - 64; height: 28
            contentWidth: actionRow.width; contentHeight: height
            clip: true; boundsBehavior: Flickable.StopAtBounds
            visible: root.open && !root.mediaShown && !root.levelShown && root.notificationActions.length > 0
            opacity: root.cardOpacity
            Row {
                id: actionRow; spacing: 6
                Repeater {
                    model: root.notificationActions
                    Rectangle {
                        required property var modelData
                        width: Math.min(140, Math.max(60, actionLabel.implicitWidth + 20)); height: 25; radius: 8
                        color: actionMouse.containsMouse ? pulseTheme.colors.border : Qt.lighter(pulseTheme.colors.background, 1.6)
                        opacity: root.displayed.busy ? 0.5 : 1
                        Text { id: actionLabel; anchors.centerIn: parent; width: Math.min(120, implicitWidth); text: modelData.label; textFormat: Text.PlainText; elide: Text.ElideRight; color: pulseTheme.colors.title; font.pixelSize: 10 }
                        MouseArea {
                            id: actionMouse; anchors.fill: parent; hoverEnabled: true
                            enabled: !root.displayed.busy
                            onClicked: pulseController.activate(root.displayed.id, modelData.key)
                        }
                    }
                }
            }
        }
    }
    Text {
        anchors.top: island.bottom; anchors.topMargin: 5
        anchors.horizontalCenter: parent.horizontalCenter
        visible: root.debugVisible && root.open
        text: root.phase + " · " + root.fps + " fps · queued " + pulseController.queued
        color: pulseTheme.colors.muted; font.pixelSize: pulseTheme.typography.label_size
    }
    FrameAnimation { running: root.debugVisible && root.visible; onTriggered: root.frames++ }
    Timer {
        interval: 1000; repeat: true; running: root.debugVisible
        onTriggered: { root.fps = root.frames; root.frames = 0 }
    }
    Component.onCompleted: { Qt.callLater(syncMask); refreshCard() }
}
