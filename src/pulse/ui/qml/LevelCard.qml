import QtQuick

Item {
    id: level
    property var card: ({title: "Volume", value: 0, valueLabel: ""})
    property bool reducedMotion: false
    implicitHeight: 58
    Rectangle {
        x: 14; y: 11; width: 25; height: 25; radius: 8
        color: pulseTheme.colors.border
        Canvas {
            anchors.centerIn: parent
            width: 18; height: 18
            property bool muted: level.card.valueLabel === "Muted"
            onMutedChanged: requestPaint()
            onPaint: {
                let ctx = getContext("2d")
                ctx.clearRect(0, 0, width, height)
                ctx.fillStyle = pulseTheme.colors.accent
                ctx.strokeStyle = pulseTheme.colors.accent
                ctx.lineWidth = 1.4; ctx.lineCap = "round"
                ctx.beginPath(); ctx.moveTo(2, 7); ctx.lineTo(5, 7)
                ctx.lineTo(9, 4); ctx.lineTo(9, 14); ctx.lineTo(5, 11)
                ctx.lineTo(2, 11); ctx.closePath(); ctx.fill()
                if (muted) {
                    ctx.beginPath(); ctx.moveTo(12, 7); ctx.lineTo(16, 11)
                    ctx.moveTo(16, 7); ctx.lineTo(12, 11); ctx.stroke()
                } else {
                    for (let radius of [4, 7]) {
                        ctx.beginPath(); ctx.arc(8, 9, radius, -0.7, 0.7); ctx.stroke()
                    }
                }
            }
        }
    }
    Text {
        x: 49; y: 15
        text: level.card.title
        color: pulseTheme.colors.title; font.pixelSize: 13; font.weight: Font.DemiBold
    }
    Text {
        anchors.right: parent.right; anchors.rightMargin: 16
        y: 13
        text: level.card.valueLabel || Math.round(level.card.value * 100) + "%"
        color: pulseTheme.colors.accent; font.pixelSize: 16; font.weight: Font.DemiBold
    }
    Rectangle {
        x: 16; y: 43; width: parent.width - 32; height: 4
        radius: 2; color: pulseTheme.colors.border
        Rectangle {
            width: parent.width * level.card.value; height: 4; radius: 2
            color: pulseTheme.colors.accent
            Behavior on width { NumberAnimation { duration: level.reducedMotion ? 0 : 140; easing.type: Easing.OutCubic } }
        }
    }
}
