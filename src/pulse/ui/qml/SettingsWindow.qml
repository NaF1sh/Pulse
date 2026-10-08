import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts

Window {
    id: settings
    objectName: "pulseSettings"
    width: 800; height: 620
    minimumWidth: 700; minimumHeight: 560
    title: "Pulse — Settings"
    color: "#111216"
    property var preferences: null
    property var controller: typeof pulseController !== "undefined" ? pulseController : null
    property int tab: 0
    readonly property bool welcoming: preferences ? preferences.welcomeNeeded : false
    readonly property color accent: pulseTheme.colors.accent
    readonly property color ink: "#f1f2f4"
    readonly property color secondary: "#999da9"
    readonly property var sections: ["General", "Companion", "Appearance", "History", "Status", "Focus", "Music", "Tasks"]
    function open() { show(); requestActivate() }
    Shortcut { sequence: "Escape"; onActivated: settings.close() }

    component QuietButton: Button {
        id: control
        property bool selected: false
        property bool destructive: false
        hoverEnabled: true
        implicitHeight: 36
        padding: 12
        contentItem: Text {
            text: control.text
            color: control.destructive ? "#f0a5ae" : control.selected ? settings.ink : settings.secondary
            font.pixelSize: 13; font.weight: control.selected ? Font.DemiBold : Font.Normal
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        background: Rectangle {
            radius: 8
            color: control.down ? "#30323c" : control.selected ? "#252731" : control.hovered ? "#202229" : "transparent"
            border.width: 1
            border.color: control.activeFocus ? settings.accent : control.selected ? "#363945" : "transparent"
        }
        Accessible.name: text
    }

    Rectangle {
        width: 184; height: parent.height
        color: "#16171c"
        Rectangle { anchors.right: parent.right; width: 1; height: parent.height; color: "#282a32" }
        Row {
            x: 22; y: 28; spacing: 10
            Face { width: 28; height: 28; design: pulsePets.current; animate: false }
            Text { text: "Pulse"; color: settings.ink; font.pixelSize: 22; font.weight: Font.DemiBold }
        }
        Text { x: 24; y: 70; text: "YOUR DESKTOP COMPANION"; color: settings.secondary; font.pixelSize: 8; font.letterSpacing: 1.2 }
        Column {
            visible: !settings.welcoming
            x: 12; y: 115; width: parent.width - 24; spacing: 6
            Repeater {
                model: settings.sections
                QuietButton {
                    required property string modelData
                    required property int index
                    width: parent.width
                    text: modelData; selected: settings.tab === index
                    onClicked: { settings.tab = index; if (index === 3 && preferences) preferences.refreshHistory() }
                }
            }
        }
        Text { x: 24; anchors.bottom: quit.top; anchors.bottomMargin: 22; text: "Small presence.\nLess interruption."; color: settings.secondary; font.pixelSize: 11; lineHeight: 1.5 }
        QuietButton { id: quit; x: 12; width: parent.width - 24; anchors.bottom: parent.bottom; anchors.bottomMargin: 18; text: "Quit Pulse"; destructive: true; onClicked: Qt.quit() }
    }

    Item {
        visible: !settings.welcoming
        x: 184; width: parent.width - x; height: parent.height
        Column {
            x: 32; y: 30; width: parent.width - 64; spacing: 8
            Text { text: settings.sections[settings.tab]; color: settings.ink; font.pixelSize: 26; font.weight: Font.DemiBold }
            Text {
                width: parent.width
                text: ["Choose what deserves your attention.", "A little personality for your desktop.", "Set the mood. Keep the same quiet presence.", "Catch up on notifications at your own pace.", "See what is connected and ready.", "One task at a time. Make space for a break.", "Keep your soundtrack within reach.", "Your agents and running jobs, in the island."][settings.tab]
                color: settings.secondary; font.pixelSize: 12; wrapMode: Text.Wrap
            }
        }
        Rectangle { x: 32; y: 111; width: parent.width - 64; height: 1; color: "#282a32" }
        StackLayout {
            x: 32; y: 133; width: parent.width - 64; height: parent.height - 198
            currentIndex: settings.tab
            Flickable {
                contentHeight: general.implicitHeight; clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: ScrollBar {}
                Column {
                    id: general; width: parent.width; spacing: 10
                    Repeater {
                        model: [
                            {key:"music", title:"Now playing", detail:"Keep your current song close."},
                            {key:"volume", title:"Volume feedback", detail:"See volume changes and mute status."},
                            {key:"dnd", title:"Do not disturb", detail:"Pause ordinary notifications. Critical alerts follow your preferences."},
                            {key:"motion", title:"Reduce motion", detail:"Use brief fades with fewer animations."},
                            {key:"quiet_plasma", title:"Quiet Plasma popups · experimental", detail:"Pause Plasma popups and sounds while Pulse is connected. Critical alerts may still appear. See Status for connection details."}
                        ].filter(option => !preferences || preferences.desktopSources || option.key === "motion")
                        Rectangle {
                            required property var modelData
                            width: general.width; height: Math.max(82, detail.implicitHeight + 48)
                            radius: 12; color: "#1a1c22"; border.color: "#2b2d36"
                            Text { x: 18; y: 17; text: modelData.title; color: settings.ink; font.pixelSize: 13; font.weight: Font.DemiBold }
                            Text { id: detail; x: 18; y: 40; width: parent.width - 100; text: modelData.detail; color: settings.secondary; font.pixelSize: 11; wrapMode: Text.Wrap }
                            Switch {
                                id: toggle
                                objectName: "preference-" + modelData.key
                                anchors.right: parent.right; anchors.rightMargin: 12; anchors.verticalCenter: parent.verticalCenter
                                checked: preferences ? preferences[modelData.key] : false
                                onClicked: if (preferences) preferences.toggle(modelData.key)
                                Accessible.name: modelData.title
                                indicator: Rectangle {
                                    implicitWidth: 38; implicitHeight: 22
                                    x: toggle.leftPadding; y: (toggle.height - height) / 2
                                    radius: 11
                                    color: toggle.checked ? settings.accent : "#414551"
                                    border.color: toggle.activeFocus ? settings.ink : "transparent"
                                    Rectangle {
                                        x: toggle.checked ? 19 : 3; y: 3; width: 16; height: 16; radius: 8
                                        color: toggle.checked ? "#17181e" : "#e0e1e6"
                                        Behavior on x { NumberAnimation { duration: preferences && preferences.motion ? 0 : 120 } }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            GridView {
                id: pets; clip: true
                cellWidth: width / Math.max(3, Math.floor(width / 108)); cellHeight: 108
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: ScrollBar {}
                model: pulsePets.catalog
                delegate: Button {
                    id: pet
                    required property var modelData
                    width: pets.cellWidth - 8; height: 100
                    hoverEnabled: true
                    Accessible.name: modelData.name
                    onClicked: pulsePets.select(modelData.id)
                    background: Rectangle {
                        radius: 12; color: pet.hovered ? "#252731" : "#1a1c22"
                        border.color: pet.activeFocus || pet.modelData.id === pulsePets.current.id ? settings.accent : "#2b2d36"
                    }
                    contentItem: Item {
                        Face { width: 40; height: 40; y: 9; anchors.horizontalCenter: parent.horizontalCenter; design: pet.modelData; animate: false }
                        Text { y: 59; width: parent.width; text: pet.modelData.name; color: settings.ink; font.pixelSize: 11; horizontalAlignment: Text.AlignHCenter; elide: Text.ElideRight; textFormat: Text.PlainText }
                        Rectangle { width: 4; height: 4; radius: 2; anchors.horizontalCenter: parent.horizontalCenter; y: 78; color: settings.accent; visible: pet.modelData.id === pulsePets.current.id }
                    }
                }
            }
            AppearancePage { preferences: settings.preferences }
            Item {
                Row { id: historyToolbar; spacing: 8
                    QuietButton { text: "Refresh"; onClicked: if (preferences) preferences.refreshHistory() }
                    QuietButton { text: "Clear history"; destructive: true; onClicked: if (preferences) preferences.clearHistory() }
                }
                SurfaceField {
                    id: historySearch; anchors.top: historyToolbar.bottom; anchors.topMargin: 12
                    width: parent.width; placeholderText: "Search messages or apps…"
                    Accessible.name: "Search notification history"
                    onTextChanged: if (preferences) preferences.setHistoryQuery(text)
                }
                Column {
                    anchors.centerIn: parent; width: parent.width - 40; spacing: 12
                    visible: history.count === 0
                    Text { width: parent.width; text: historySearch.text ? "No matching notifications" : "All caught up"; horizontalAlignment: Text.AlignHCenter; color: settings.ink; font.pixelSize: 18; font.weight: Font.DemiBold }
                    Text { width: parent.width; text: historySearch.text ? "Try another app name or a word from the message." : "Your saved notifications will appear here.\nEnjoy a quiet moment."; horizontalAlignment: Text.AlignHCenter; color: settings.secondary; font.pixelSize: 12; lineHeight: 1.5 }
                }
                ListView {
                    id: history; anchors.top: historySearch.bottom; anchors.topMargin: 16
                    anchors.bottom: parent.bottom; width: parent.width; clip: true; spacing: 8
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: ScrollBar {}
                    model: preferences ? preferences.entries : []
                    delegate: Rectangle {
                        required property var modelData
                        width: history.width; height: entry.implicitHeight + 32; radius: 12; color: "#1a1c22"; border.color: "#2b2d36"
                        Column { id: entry; x: 16; y: 16; width: parent.width - 32; spacing: 7
                            Text { width: parent.width; text: modelData.app + " · " + modelData.received_at; color: settings.secondary; font.pixelSize: 10; elide: Text.ElideRight; textFormat: Text.PlainText }
                            Text { width: parent.width; text: modelData.title; color: settings.ink; font.pixelSize: 13; font.weight: Font.DemiBold; wrapMode: Text.Wrap; textFormat: Text.PlainText }
                            Text { width: parent.width; text: modelData.body; visible: text.length > 0; color: "#b9bdc8"; font.pixelSize: 12; wrapMode: Text.Wrap; textFormat: Text.PlainText }
                        }
                    }
                }
            }
            Flickable {
                clip: true; contentHeight: statusContent.implicitHeight
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: ScrollBar {}
                Column {
                    id: statusContent; width: parent.width; spacing: 12
                    Row {
                        spacing: 8
                        QuietButton { text: "Show a preview"; onClicked: if (preferences) preferences.previewNotification() }
                        QuietButton { text: "Retry notifications"; onClicked: if (preferences) preferences.retryConnections() }
                    }
                    Repeater {
                        model: preferences ? preferences.sources : []
                        Rectangle {
                            required property var modelData
                            width: statusContent.width; height: statusText.implicitHeight + 32
                            radius: 12; color: "#1a1c22"; border.color: modelData.problem ? "#775b3b" : "#2b2d36"
                            Column {
                                id: statusText; x: 16; y: 16; width: parent.width - 32; spacing: 7
                                Text { text: modelData.name; color: settings.ink; font.pixelSize: 13; font.weight: Font.DemiBold }
                                Text { width: parent.width; text: modelData.detail; color: modelData.problem ? "#e1bd8a" : settings.secondary; font.pixelSize: 11; wrapMode: Text.Wrap; textFormat: Text.PlainText }
                            }
                        }
                    }
                }
            }
            FocusPage { controller: settings.controller }
            MusicPage { controller: settings.controller; desktopSupported: !settings.preferences || settings.preferences.desktopSources }
            TasksPage { controller: settings.controller }
        }
        Rectangle { x: 32; anchors.bottom: parent.bottom; anchors.bottomMargin: 54; width: parent.width - 64; height: 1; color: "#282a32" }
        Text { x: 32; anchors.bottom: parent.bottom; anchors.bottomMargin: 23; width: parent.width - 64; text: preferences ? preferences.status || "Preferences save automatically" : ""; color: settings.secondary; font.pixelSize: 11; elide: Text.ElideRight; textFormat: Text.PlainText }
    }

    Item {
        visible: settings.welcoming
        x: 184; width: parent.width - x; height: parent.height
        Column {
            x: 36; y: 38; width: parent.width - 72; spacing: 16
            Text { text: "Meet your quiet companion."; color: settings.ink; font.pixelSize: 24; font.weight: Font.DemiBold }
            Text { width: parent.width; text: "Pulse keeps your tasks and connected agents close at hand in a small island at the top of your screen. Desktop notifications, music, and volume are also available on Linux."; color: settings.secondary; font.pixelSize: 13; wrapMode: Text.Wrap; lineHeight: 1.4 }
            Repeater {
                model: [
                    {title: "A small gesture goes a long way", detail: "Right-click the pet for Settings. Click a message to open its app. Use × to dismiss it."},
                    {title: "Your music, when you want it", detail: "Double-click to hide or restore the music card. Playback stays in your music app."},
                    {title: "Your notifications stay on this device", detail: "In live mode, Pulse saves up to 1,000 messages locally unless history is disabled. Clear them in History. Your desktop may also show its own popup."}
                ]
                Rectangle {
                    required property var modelData
                    width: parent.width; height: welcomeText.implicitHeight + 28; radius: 12; color: "#1a1c22"; border.color: "#2b2d36"
                    Column { id: welcomeText; x: 16; y: 14; width: parent.width - 32; spacing: 7
                        Text { width: parent.width; text: modelData.title; color: settings.ink; font.pixelSize: 13; font.weight: Font.DemiBold; wrapMode: Text.Wrap }
                        Text { width: parent.width; text: modelData.detail; color: settings.secondary; font.pixelSize: 12; wrapMode: Text.Wrap; lineHeight: 1.3 }
                    }
                }
            }
            Row {
                spacing: 12
                QuietButton { text: "Make it yours"; selected: true; onClicked: if (preferences) { preferences.completeWelcome(); settings.tab = 1 } }
                QuietButton { text: "Show a preview"; onClicked: if (preferences) preferences.previewNotification() }
            }
        }
    }
}
