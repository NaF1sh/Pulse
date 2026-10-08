import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import Pulse.Appearance 1.0

Flickable {
    id: page
    property var preferences
    readonly property var style: preferences ? preferences.background : ({custom: false, hasImage: false, image: "", dim: 0.2, position: 0.5})
    readonly property var palette: style.custom ? style.colors : pulseTheme.colors
    contentHeight: content.implicitHeight; clip: true
    boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar {}
    component Label: Text { color: "#b9bdc8"; font.pixelSize: 12; wrapMode: Text.Wrap }
    component Choice: Button {
        id: button
        property bool selected: false
        hoverEnabled: true; padding: 12
        contentItem: Text { text: button.text; color: button.selected ? "#ffffff" : "#b9bdc8"; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter }
        background: Rectangle { radius: 8; color: button.hovered || button.selected ? "#30323f" : "#1a1c22"; border.color: button.activeFocus || button.selected ? "#b3a0fa" : "#353741" }
        Accessible.name: text
    }
    Column {
        id: content; width: page.width - 12; spacing: 16
        Rectangle {
            width: parent.width; height: 128; radius: 14; color: "#1a1c22"; border.color: "#2b2d36"
            Label { x: 16; y: 12; text: "LIVE PREVIEW"; font.pixelSize: 9; font.letterSpacing: 1.4 }
            BarBackground {
                anchors.centerIn: parent; anchors.verticalCenterOffset: 8
                width: Math.min(330, parent.width - 32); height: 64
                backgroundColor: page.palette.background; imageSource: page.style.image
                dim: page.style.dim; imagePosition: page.style.position; cornerRadius: 18
                Face { x: 12; y: 17; width: 30; height: 30; design: pulsePets.current; animate: false }
                Column { x: 54; y: 15; width: Math.min(330, page.width - 44) - 68; spacing: 5
                    Text { text: "Make room for what matters"; color: page.palette.title; font.pixelSize: 12; font.bold: true }
                    Text { text: "Your desktop. Your atmosphere."; color: page.palette.body; font.pixelSize: 11 }
                }
            }
        }
        Row { spacing: 8
            Repeater {
                model: [{key:"theme",title:"Theme"}, {key:"solid",title:"Color"}, {key:"random",title:"Random"}, {key:"image",title:"Image"}]
                Choice { required property var modelData; text: modelData.title; selected: preferences && preferences.backgroundMode === modelData.key; onClicked: preferences.setBackgroundMode(modelData.key) }
            }
        }
        Column {
            visible: preferences && preferences.backgroundMode === "theme"; spacing: 12; width: parent.width
            Label { text: "A coordinated palette for every notification."; width: parent.width }
            Row { spacing: 8
                Repeater {
                    model: [{key:"default",title:"Lavender"}, {key:"ocean",title:"Ocean"}, {key:"rose",title:"Rose"}]
                    Choice { required property var modelData; text: modelData.title; selected: preferences && preferences.theme === modelData.key; onClicked: preferences.selectTheme(modelData.key) }
                }
            }
        }
        Column {
            visible: preferences && preferences.backgroundMode === "solid"; spacing: 12; width: parent.width
            Label { text: "Pick a color. Text contrast adjusts automatically."; width: parent.width }
            Row { spacing: 8
                Repeater {
                    model: ["#594a86", "#b8d9dc", "#e8b9a9", "#263c48", "#d4c4e5", "#375946", "#daa65d", "#6e334b"]
                    Button {
                        required property string modelData
                        width: 32; height: 32; Accessible.name: "Background " + modelData
                        onClicked: preferences.setBackgroundColor(modelData)
                        background: Rectangle { radius: 16; color: parent.modelData; border.width: 2; border.color: parent.activeFocus || preferences && preferences.backgroundColor === parent.modelData ? "#ffffff" : "#444650" }
                    }
                }
            }
            Row { spacing: 8
                SurfaceField { id: hex; width: 130; text: preferences ? preferences.backgroundColor : ""; placeholderText: "#594a86"; Accessible.name: "Background hex color"; onAccepted: preferences.setBackgroundColor(text) }
                Choice { text: "Apply"; onClicked: preferences.setBackgroundColor(hex.text) }
                Choice { text: "Color picker…"; onClicked: colorPicker.open() }
            }
        }
        Column {
            visible: preferences && preferences.backgroundMode === "random"; width: parent.width; spacing: 12
            Label { width: parent.width; text: "A fresh, readable color for each new notification. Updates to the same card keep its color." }
            Choice { text: "Try another color"; onClicked: preferences.shuffleBackground() }
        }
        Column {
            visible: preferences && preferences.backgroundMode === "image"; width: parent.width; spacing: 10
            Label { width: parent.width; text: "Use a photo or wallpaper saved on your computer, including an image downloaded from Pinterest. Pulse keeps a private copy." }
            Label { text: "Paste the full image path" }
            SurfaceField {
                id: imagePath; objectName: "backgroundImagePath"
                width: parent.width
                placeholderText: "~/Downloads/wallpaper.jpg"
                Accessible.name: "Image file path"
                selectByMouse: true
                onAccepted: if (text.trim().length) preferences.importBackground(text)
            }
            Row { spacing: 8
                Choice { text: "Paste"; onClicked: { imagePath.forceActiveFocus(); imagePath.selectAll(); imagePath.paste() } }
                Choice { text: "Use image"; enabled: imagePath.text.trim().length > 0; onClicked: preferences.importBackground(imagePath.text) }
                Choice { text: "Browse…"; onClicked: imagePicker.open() }
            }
            Label { width: parent.width; text: "Paste with Ctrl+V, then press Enter or Use image."; font.pixelSize: 11 }
            Label { width: parent.width; visible: text.length > 0; text: preferences ? preferences.backgroundError : ""; color: "#f0a5ae" }
            Label { visible: !page.style.hasImage; text: "PNG, JPEG or WebP · up to 32 MB / 24 megapixels"; font.pixelSize: 11 }
            Column {
                visible: page.style.hasImage; width: parent.width; spacing: 4
                Label { text: "Crop position · top to bottom" }
                BarSlider { width: parent.width; from: 0; to: 1; value: page.style.position; Accessible.name: "Image crop position"; onMoved: preferences.setBackgroundPosition(value) }
                Label { text: "Darkness · " + Math.round(page.style.dim * 100) + "%" }
                BarSlider { width: parent.width; from: 0; to: 0.8; value: page.style.dim; Accessible.name: "Background darkness"; onMoved: preferences.setBackgroundDim(value) }
                Label { width: parent.width; text: "A soft shade behind the text keeps notifications readable."; font.pixelSize: 11 }
            }
        }
        Label { width: parent.width; visible: text.length > 0 && preferences.backgroundMode !== "image"; text: preferences ? preferences.backgroundError : ""; color: "#f0a5ae" }
        Row { spacing: 8
            Choice { text: "Preview on desktop"; onClicked: preferences.previewNotification() }
            Choice { text: "Reset to theme"; onClicked: preferences.setBackgroundMode("theme") }
        }
    }
    ColorDialog { id: colorPicker; title: "Notification background"; selectedColor: preferences ? preferences.backgroundColor : "#594a86"; onAccepted: preferences.setBackgroundColor(selectedColor.toString()) }
    FileDialog { id: imagePicker; title: "Choose a notification background"; nameFilters: ["Images (*.png *.jpg *.jpeg *.webp)"]; onAccepted: preferences.importBackground(selectedFile.toString()) }
}
