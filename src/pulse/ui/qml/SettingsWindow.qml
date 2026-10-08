import QtQuick
import QtQuick.Window

Window {
    id: settings
    width: 660; height: 590
    minimumWidth: 540; minimumHeight: 560
    title: "Pulse — Settings"
    color: "#17171f"
    property var preferences: null
    property int tab: 0
    function open() { show(); requestActivate() }
    Item {
        anchors.fill: parent
        focus: true
        Keys.onEscapePressed: settings.close()
        Text { x: 28; y: 22; text: "Make Pulse yours"; color: "#f3efff"; font.pixelSize: 25; font.bold: true }
        Text { x: 28; y: 58; text: "Small companion. Your preferences."; color: "#aaa4bc"; font.pixelSize: 13 }
        Row {
            x: 24; y: 94; spacing: 8
            Repeater {
                model: ["General", "Pets", "Appearance", "History"]
                Rectangle {
                    required property string modelData
                    required property int index
                    width: 118; height: 36; radius: 10
                    color: settings.tab === index ? "#4b3c65" : "#24222e"
                    Text { anchors.centerIn: parent; text: modelData; color: "#eee7fa"; font.pixelSize: 13 }
                    MouseArea { anchors.fill: parent; onClicked: { settings.tab = index; if(index === 3 && preferences) preferences.refreshHistory() } }
                }
            }
        }
        Column {
            x: 28; y: 156; width: parent.width - 56; spacing: 14
            visible: settings.tab === 0
            Repeater {
                model: [
                    {key: "music", title: "Now playing", detail: "Keep the current song and cover visible"},
                    {key: "volume", title: "Volume changes", detail: "Show volume and mute feedback"},
                    {key: "dnd", title: "Do not disturb", detail: "Silence ordinary cards; critical alerts follow your config"},
                    {key: "motion", title: "Reduce motion", detail: "Keep transitions calm and simple"}
                ]
                Rectangle {
                    required property var modelData
                    width: parent.width; height: 72; radius: 13; color: "#24222e"
                    Text { x: 17; y: 14; text: modelData.title; color: "#f3efff"; font.pixelSize: 14; font.bold: true }
                    Text { x: 17; y: 39; width: parent.width - 96; text: modelData.detail; color: "#aaa4bc"; font.pixelSize: 11; wrapMode: Text.Wrap }
                    Rectangle {
                        anchors.right: parent.right; anchors.rightMargin: 18; anchors.verticalCenter: parent.verticalCenter
                        width: 42; height: 24; radius: 12
                        property bool enabledPreference: preferences ? preferences[modelData.key] : false
                        color: enabledPreference ? "#bfa0ef" : "#514a60"
                        Rectangle { x: parent.enabledPreference ? 21 : 3; y: 3; width: 18; height: 18; radius: 9; color: "#f8f4ff" }
                    }
                    MouseArea { anchors.fill: parent; onClicked: if(preferences) preferences.toggle(modelData.key) }
                }
            }
        }
        GridView {
            id: pets
            x: 24; y: 150; width: parent.width - 48; height: parent.height - 220
            visible: settings.tab === 1; clip: true
            cellWidth: width / Math.max(3, Math.floor(width / 110)); cellHeight: 100
            model: pulsePets.catalog
            delegate: Item {
                required property var modelData
                width: pets.cellWidth; height: pets.cellHeight
                Rectangle { anchors.fill: parent; anchors.margins: 5; radius: 12; color: "#24222e"; border.color: modelData.id === pulsePets.current.id ? "#c4a8fa" : "#353142"; border.width: 2 }
                Face { width: 44; height: 44; y: 14; anchors.horizontalCenter: parent.horizontalCenter; design: modelData; animate: false }
                Text { x: 8; y: 67; width: parent.width - 16; text: modelData.name; color: "#eee7fa"; font.pixelSize: 11; horizontalAlignment: Text.AlignHCenter; elide: Text.ElideRight; textFormat: Text.PlainText }
                MouseArea { anchors.fill: parent; onClicked: pulsePets.select(modelData.id) }
            }
        }
        Column {
            x: 28; y: 158; width: parent.width - 56; spacing: 16
            visible: settings.tab === 2
            Text { text: "Choose an island palette"; color: "#eee7fa"; font.pixelSize: 16 }
            Repeater {
                model: [{name:"default", label:"Lavender", accent:"#c4a8fa"}, {name:"ocean",label:"Ocean",accent:"#76cce5"}, {name:"rose",label:"Rose",accent:"#f0a6be"}]
                Rectangle {
                    required property var modelData
                    width: parent.width; height: 70; radius: 14; color: "#24222e"
                    border.color: preferences && preferences.theme === modelData.name ? modelData.accent : "#353142"
                    Rectangle { x: 18; y: 19; width: 32; height: 32; radius: 16; color: modelData.accent }
                    Text { x: 66; anchors.verticalCenter: parent.verticalCenter; text: modelData.label; color: "#eee7fa"; font.pixelSize: 15 }
                    MouseArea { anchors.fill: parent; onClicked: if(preferences) preferences.selectTheme(modelData.name) }
                }
            }
        }
        Item {
            x: 28; y: 150; width: parent.width - 56; height: parent.height - 220
            visible: settings.tab === 3
            Row {
                spacing: 12
                Repeater {
                    model: ["Refresh", "Clear history"]
                    Rectangle {
                        required property string modelData
                        required property int index
                        width: 120; height: 34; radius: 8; color: index ? "#482d3b" : "#302b40"
                        Text { anchors.centerIn: parent; text: modelData; color: "#eee7fa"; font.pixelSize: 12 }
                        MouseArea { anchors.fill: parent; onClicked: if(preferences) { if(index) preferences.clearHistory(); else preferences.refreshHistory() } }
                    }
                }
            }
            Text { y: 55; text: "No saved notifications yet. Live desktop notifications appear here."; visible: history.count === 0; width: parent.width; wrapMode: Text.Wrap; color: "#aaa4bc"; font.pixelSize: 13 }
            ListView {
                id: history
                y: 48; width: parent.width; height: parent.height - 48; clip: true; spacing: 10
                model: preferences ? preferences.entries : []
                delegate: Rectangle {
                    required property var modelData
                    width: history.width; height: entry.height + 24; radius: 10; color: "#24222e"
                    Column {
                        id: entry; x: 12; y: 12; width: parent.width - 24; spacing: 5
                        Text { width: parent.width; text: modelData.app + " · " + modelData.received_at; color: "#aaa4bc"; font.pixelSize: 10; elide: Text.ElideRight; textFormat: Text.PlainText }
                        Text { width: parent.width; text: modelData.title; color: "#eee7fa"; font.pixelSize: 13; font.bold: true; wrapMode: Text.Wrap; textFormat: Text.PlainText }
                        Text { width: parent.width; text: modelData.body; visible: text.length > 0; color: "#c4bed0"; font.pixelSize: 12; wrapMode: Text.Wrap; textFormat: Text.PlainText }
                    }
                }
            }
        }
        Text { x: 28; anchors.bottom: parent.bottom; anchors.bottomMargin: 27; width: parent.width - 170; text: preferences ? preferences.status || "Changes save automatically · Escape to close" : ""; color: "#aaa4bc"; font.pixelSize: 11; elide: Text.ElideRight }
        Rectangle {
            anchors.right: parent.right; anchors.rightMargin: 28; anchors.bottom: parent.bottom; anchors.bottomMargin: 18
            width: 100; height: 32; radius: 8; color: "#3a2936"
            Text { anchors.centerIn: parent; text: "Quit Pulse"; color: "#f9c5d8"; font.pixelSize: 12 }
            MouseArea { anchors.fill: parent; onClicked: Qt.quit() }
        }
    }
}
