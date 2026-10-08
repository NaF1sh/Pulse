import QtQuick
import QtQuick.Window
import QtQuick.Controls
import Pulse.Appearance 1.0
Window {
    id: root
    width: 420; height: tasksExpanded ? 500 : 160
    visible: false
    color: "transparent"
    title: "Pulse"
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus
    readonly property var backgroundStyle: typeof pulsePreferences !== "undefined" ? pulsePreferences.background : ({custom: false, image: "", dim: 0.2, position: 0.5})
    readonly property var barColors: backgroundStyle.custom ? backgroundStyle.colors : pulseTheme.colors
    property bool tasksExpanded: false
    readonly property bool hasTasks: pulseController.tasks.summary.total > 0
    onHasTasksChanged: if (!hasTasks) tasksExpanded = false
    property bool expanded: false
    onTasksExpandedChanged: { expanded = tasksExpanded; refreshCard() }
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
    property real cardWidth: hasTasks ? 350 : mediaShown ? Math.min(pulseTheme.layout.max_width, Math.max(pulseTheme.layout.min_width, 330))
                            : levelShown ? pulseTheme.layout.min_width
                            : Math.min(pulseTheme.layout.max_width, 280)
    property var notificationActions: displayed.actions || []
    property real baseCardHeight: mediaShown ? 100 : levelShown ? 58 : (displayed.kind === "progress" ? 68 : 54) + (notificationActions.length ? 32 : 0)
    property real cardHeight: baseCardHeight + (hasTasks ? 36 : 0) + (tasksExpanded ? 280 : 0)
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
        color: root.barColors.background
        border.color: islandMouse.containsMouse && root.open ? Qt.lighter(root.barColors.border, 1.5) : root.barColors.border; border.width: 1
        Behavior on border.color { ColorAnimation { duration: root.reducedMotion ? 0 : 120 } }
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
        BarBackground {
            anchors.fill: parent; anchors.margins: 1
            visible: root.open
            backgroundColor: root.barColors.background
            imageSource: root.backgroundStyle.image
            dim: root.backgroundStyle.dim; imagePosition: root.backgroundStyle.position
            cornerRadius: Math.max(0, island.radius - 1)
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
            color: Qt.lighter(root.barColors.background, 1.3)
            visible: !root.mediaShown && !root.levelShown
            opacity: root.cardOpacity
            Image {
                id: sourceIcon
                objectName: "notificationSourceIcon"
                anchors.centerIn: parent
                width: 26; height: 26
                source: root.displayed.icon || ""
                fillMode: Image.PreserveAspectFit
                visible: status === Image.Ready
            }
            Face {
                anchors.centerIn: parent; width: 25; height: 25
                design: pulsePets.current; animate: false
                visible: sourceIcon.status !== Image.Ready
            }
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
                color: root.barColors.title; font.pixelSize: 13; font.weight: Font.DemiBold
                elide: Text.ElideRight; textFormat: Text.PlainText
            }
            Text {
                id: message
                width: parent.width
                text: pulseController.actionError || root.displayed.body || (pulseController.active ? "" : "Waiting for notifications")
                visible: text.length > 0
                color: root.barColors.body; font.pixelSize: 12
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
                    height: 4; radius: 2; color: root.barColors.border
                    Rectangle {
                        width: parent.width * root.displayed.value
                        height: parent.height; radius: 2
                        color: root.displayed.kind === "level" ? root.barColors.accent : root.barColors.progress
                        Behavior on width { NumberAnimation { duration: root.reducedMotion ? 0 : pulseTheme.animation.meter } }
                    }
                }
                Text {
                    id: percentage
                    anchors.right: parent.right
                    text: root.displayed.valueLabel || Math.round(root.displayed.value * 100) + "%"
                    color: root.barColors.body; font.pixelSize: pulseTheme.typography.label_size
                }
            }
            Row {
                visible: root.displayed.kind === "media"
                height: visible ? 14 : 0
                spacing: 8
                Text { text: "♪"; color: root.barColors.accent; font.pixelSize: pulseTheme.typography.body_size }
                Text {
                    text: root.displayed.status === "Paused" ? "Paused"
                          : root.displayed.status === "Demo" ? "Now playing · Demo" : "Now playing"
                    color: root.barColors.muted; font.pixelSize: pulseTheme.typography.label_size
                }
            }
        }
        MediaCard {
            anchors.left: parent.left; anchors.right: parent.right; height: 72
            visible: root.mediaShown
            colors: root.barColors
            card: root.displayed
            reducedMotion: root.reducedMotion
            opacity: root.cardOpacity
            Behavior on opacity { NumberAnimation { duration: root.reducedMotion ? 70 : pulseTheme.animation.fade } }
        }
        LevelCard {
            anchors.fill: parent
            visible: root.levelShown
            colors: root.barColors
            card: root.displayed
            reducedMotion: root.reducedMotion
            opacity: root.cardOpacity
            Behavior on opacity { NumberAnimation { duration: root.reducedMotion ? 70 : pulseTheme.animation.fade } }
        }
        MouseArea {
            id: islandMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: !pulseController.active || root.displayed.canOpen || (root.displayed.status === "Focus" || root.displayed.status === "Task") ? Qt.PointingHandCursor : Qt.ArrowCursor
            ToolTip.visible: containsMouse && !root.open
            ToolTip.delay: 900
            ToolTip.text: "Right-click for settings · Double-click to toggle music"
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            onClicked: mouse => {
                if (mouse.button === Qt.RightButton) { if (settingsWindow.preferences) root.openSettings(); else { petPicker.show(); petPicker.requestActivate() } }
                else if (root.displayed.status === "Task") root.tasksExpanded = !root.tasksExpanded
                else if (root.mediaShown && pulseController.active) { /* Double-click hides music. */ }
                else if (root.displayed.status === "Focus") { settingsWindow.tab = 5; root.openSettings() }
                else if (pulseController.active) {
                    if (root.levelShown) pulseController.dismiss()
                    else pulseController.activate(root.displayed.id)
                }
                else if (root.hasTasks) root.tasksExpanded = !root.tasksExpanded
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
        Row {
            anchors.horizontalCenter: parent.horizontalCenter; y: 69; spacing: 8
            visible: root.mediaShown && root.open; opacity: root.cardOpacity
            Repeater {
                model: [{action:"previous",label:"Previous"}, {action:"toggle",label:root.displayed.status === "Paused" ? "Play" : "Pause"}, {action:"next",label:"Next"}]
                Button {
                    id: transport
                    objectName: "music-" + modelData.action
                    required property var modelData
                    width: 76; height: 25
                    enabled: !!pulseController.musicState[modelData.action] && !pulseController.musicState.busy
                    Accessible.name: modelData.label + " track"
                    onClicked: pulseController.controlMusic(modelData.action)
                    contentItem: Text { text: transport.modelData.label; color: root.barColors.title; opacity: transport.enabled ? 1 : 0.4; font.pixelSize: 10; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                    background: Rectangle { radius: 7; color: Qt.rgba(0.5,0.5,0.5,transport.down ? 0.5 : 0.18); border.color: transport.activeFocus ? root.barColors.accent : "transparent" }
                }
            }
        }
        Row {
            x: 12; y: root.baseCardHeight; height: 30; spacing: 8
            visible: root.hasTasks && root.open
            Button {
                objectName: "toggleTaskDrawer"
                height: 28; width: 190
                text: (root.tasksExpanded ? "▴ " : "▾ ") + (pulseController.tasks.summary.working || pulseController.tasks.summary.attention
                      ? pulseController.tasks.summary.working + " working · " + pulseController.tasks.summary.attention + " need you"
                      : pulseController.tasks.summary.total + " recent tasks")
                onClicked: root.tasksExpanded = !root.tasksExpanded
                contentItem: Text { text: parent.text; color: root.barColors.title; font.pixelSize: 11; verticalAlignment: Text.AlignVCenter }
                background: Rectangle { color: "transparent" }
            }
            Button {
                height: 28; width: 115
                visible: root.displayed.status === "Task" && root.displayed.taskTarget
                text: (root.displayed.taskState || "").startsWith("needs-") ? "Review request" : "Open result"
                onClicked: pulseController.tasks.open(root.displayed.taskId)
                contentItem: Text { text: parent.text; color: root.barColors.title; font.pixelSize: 11; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                background: Rectangle { radius: 7; color: Qt.rgba(0.5,0.5,0.5,0.18) }
            }
        }
        TaskDrawer {
            objectName: "taskDrawer"
            x: 8; y: root.baseCardHeight + 36; width: parent.width - 16; height: 270
            visible: root.tasksExpanded; tasks: pulseController.tasks
        }
        Rectangle {
            anchors.right: parent.right; anchors.rightMargin: 7; y: 6
            width: 20; height: 20; radius: 10
            visible: root.open && !root.mediaShown && !root.levelShown
            opacity: root.cardOpacity
            color: dismissMouse.containsMouse ? root.barColors.border : "transparent"
            Text { anchors.centerIn: parent; text: "×"; font.pixelSize: 15; color: root.barColors.muted }
            MouseArea {
                id: dismissMouse; anchors.fill: parent; hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                ToolTip.visible: containsMouse
                ToolTip.delay: 650
                ToolTip.text: root.displayed.status === "Focus" ? "End focus session" : "Dismiss"
                onClicked: { if (root.tasksExpanded && root.displayed.id === -1) root.tasksExpanded = false; else if (root.displayed.status === "Focus") pulseController.focus.stop(); else if (root.displayed.status === "Task") pulseController.tasks.dismiss(root.displayed.taskId); else pulseController.close(root.displayed.id) }
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
                        color: actionMouse.containsMouse ? root.barColors.border : Qt.lighter(root.barColors.background, 1.6)
                        opacity: root.displayed.busy ? 0.5 : 1
                        Text { id: actionLabel; anchors.centerIn: parent; width: Math.min(120, implicitWidth); text: modelData.label; textFormat: Text.PlainText; elide: Text.ElideRight; color: root.barColors.title; font.pixelSize: 10 }
                        MouseArea {
                            id: actionMouse; anchors.fill: parent; hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
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
        color: root.barColors.muted; font.pixelSize: pulseTheme.typography.label_size
    }
    FrameAnimation { running: root.debugVisible && root.visible; onTriggered: root.frames++ }
    Timer {
        interval: 1000; repeat: true; running: root.debugVisible
        onTriggered: { root.fps = root.frames; root.frames = 0 }
    }
    Component.onCompleted: { Qt.callLater(syncMask); refreshCard() }
}
