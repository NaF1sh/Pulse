import QtQuick

Item {
    id: face
    width: 30; height: 30
    // The theme accent is now the pet's pastel coat, rather than its eyes.
    property color ink: "#b3a0fa"
    property var design: ({species: "round", coat: "#c4a8fa", expression: "idle", marking: "#fff3e5"})
    property color coat: design.coat || ink
    property color features: design.coat === "#41434e" ? "#d9c1ff" : "#322045"
    property bool hovered: false
    property bool animate: true
    property bool blinking: false
    property bool sleepy: false
    property string expressionOverride: ""
    readonly property string expression: expressionOverride || (hovered ? "happy" : sleepy ? "sleepy" : design.expression || "idle")
    onAnimateChanged: {
        if (!animate) { blinking = false; sleepy = false }
    }
    onHoveredChanged: {
        sleepy = false
        if (animate && !hovered) nap.restart()
    }
    onExpressionChanged: portrait.requestPaint()
    onBlinkingChanged: portrait.requestPaint()
    onFeaturesChanged: portrait.requestPaint()
    onDesignChanged: portrait.requestPaint()
    onCoatChanged: portrait.requestPaint()

    Canvas {
        id: portrait
        anchors.fill: parent
        antialiasing: true
        onPaint: {
            let ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            ctx.save()
            ctx.scale(width / 30, height / 30)
            function oval(x, y, w, h, color) {
                let k = 0.5522848
                ctx.beginPath()
                ctx.moveTo(x + w / 2, y)
                ctx.bezierCurveTo(x + w / 2 + w / 2 * k, y, x + w, y + h / 2 - h / 2 * k, x + w, y + h / 2)
                ctx.bezierCurveTo(x + w, y + h / 2 + h / 2 * k, x + w / 2 + w / 2 * k, y + h, x + w / 2, y + h)
                ctx.bezierCurveTo(x + w / 2 - w / 2 * k, y + h, x, y + h / 2 + h / 2 * k, x, y + h / 2)
                ctx.bezierCurveTo(x, y + h / 2 - h / 2 * k, x + w / 2 - w / 2 * k, y, x + w / 2, y)
                ctx.fillStyle = color
                ctx.fill()
            }
            function line(x1, y1, x2, y2, color, thickness) {
                ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2)
                ctx.strokeStyle = color; ctx.lineWidth = thickness; ctx.lineCap = "round"; ctx.stroke()
            }
            function triangle(x, y, size, color) {
                ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + size, y + 1)
                ctx.lineTo(x + size / 2, y - size); ctx.closePath()
                ctx.fillStyle = color; ctx.fill()
            }
            let species = face.design.species || "round"
            let marking = face.design.marking || "#fff3e5"
            let round = species === "round"
            let headY = round ? 0.5 : 6
            let coat = ctx.createLinearGradient(0, headY, 0, 30)
            coat.addColorStop(0, Qt.lighter(face.coat, 1.1).toString())
            coat.addColorStop(1, face.coat.toString())
            if (["cat", "calico", "fox"].indexOf(species) >= 0) {
                triangle(3, 10, 9, face.coat); triangle(18, 10, 9, face.coat)
                triangle(5, 9, 5, "#ffb4d0"); triangle(20, 9, 5, "#ffb4d0")
            }
            if (["bear", "panda", "capybara", "koala", "hamster", "pig", "cow"].indexOf(species) >= 0) {
                let earColor = species === "panda" ? marking : face.coat
                let earSize = species === "koala" ? 10 : 8
                oval(1, 3, earSize, earSize, earColor); oval(29 - earSize, 3, earSize, earSize, earColor)
                if (species !== "panda") {
                    oval(3, 5, earSize - 4, earSize - 4, "#ffc0d3")
                    oval(31 - earSize, 5, earSize - 4, earSize - 4, "#ffc0d3")
                }
            }
            if (species === "bunny") {
                oval(5, 0, 7, 15, face.coat); oval(18, 0, 7, 15, face.coat)
                oval(7, 2, 3, 10, "#ffa8d1"); oval(20, 2, 3, 10, "#ffa8d1")
            }
            if (species === "dog") {
                oval(1, 4, 10, 14, marking); oval(19, 4, 10, 14, marking)
            }
            if (species === "axolotl") {
                for (let y of [9, 14, 19]) {
                    oval(0, y, 8, 5, "#ff89bb"); oval(22, y, 8, 5, "#ff89bb")
                }
            }
            oval(round ? 0.5 : 2, headY, round ? 29 : 26, round ? 29 : 23, coat)
            if (species === "frog") {
                oval(3, 3, 10, 11, face.coat); oval(17, 3, 10, 11, face.coat)
            }
            if (["fox", "hamster", "penguin"].indexOf(species) >= 0 || face.design.id === "shiba") {
                oval(3, 16, 24, 13, species === "penguin" ? "#fffaff" : "#fff0db")
                if (species === "penguin") {
                    oval(5, 12, 10, 12, "#fffaff"); oval(15, 12, 10, 12, "#fffaff")
                }
            }
            if (species === "calico" || species === "cow") {
                oval(3, 6, 10, 8, marking); oval(19, 6, 9, 7, marking)
            }
            if (species === "cow") {
                oval(7, 0, 4, 8, "#edb890"); oval(19, 0, 4, 8, "#edb890")
            }
            if (species === "chick") {
                oval(12, 2, 4, 7, "#ffd05f"); oval(16, 1, 4, 7, "#ffd05f")
            }
            if (species === "panda") {
                oval(5, 10, 9, 11, marking); oval(16, 10, 9, 11, marking)
            }
            let mood = face.expression
            let happy = ["happy", "blush", "laugh"].indexOf(mood) >= 0
            let sleeping = ["sleepy", "rest", "yawn"].indexOf(mood) >= 0
            let surprised = mood === "surprised"
            let eyeY = round ? 9.5 : 12
            let mouthY = round ? 19 : 21
            // Rosy cheeks and oversized oval eyes follow the supplied emote sheet.
            oval(3.5, 17.9, 5.5, 3.4, "#ff94bd")
            oval(21, 17.9, 5.5, 3.4, "#ff94bd")
            ctx.strokeStyle = face.features
            ctx.lineWidth = 2.1
            ctx.lineCap = "round"
            for (let x of [7.5, 17.5]) {
                let wink = ["wink", "playful"].indexOf(mood) >= 0 && x > 10
                if (mood === "sparkle") {
                    oval(x, eyeY, 5, 8, face.features)
                    line(x + 2.5, eyeY - 1, x + 2.5, eyeY + 8, "#fffaff", 1.6)
                    line(x, eyeY + 3.5, x + 5, eyeY + 3.5, "#fffaff", 1.6)
                } else if (wink || mood === "kiss" || mood === "laugh") {
                    let direction = x < 10 ? 1 : -1
                    ctx.beginPath(); ctx.moveTo(x + (direction > 0 ? 0 : 5), eyeY + 1)
                    ctx.lineTo(x + (direction > 0 ? 5 : 0), eyeY + 3.5)
                    ctx.lineTo(x + (direction > 0 ? 0 : 5), eyeY + 6)
                    ctx.stroke()
                } else if (happy || sleeping || face.blinking) {
                    ctx.beginPath()
                    ctx.moveTo(x, eyeY + 3.5)
                    ctx.quadraticCurveTo(x + 2.5, happy ? eyeY - 1.7 : eyeY + 7.5, x + 5, eyeY + 3.5)
                    ctx.stroke()
                } else {
                    oval(x, eyeY, 5, 8, face.features)
                    if (mood === "smug") {
                        ctx.fillStyle = coat; ctx.fillRect(x - 1, eyeY - 1, 7, 4.5)
                        line(x - 0.4, eyeY + 3.5, x + 5.4, eyeY + 3.5, face.features, 1.7)
                    } else {
                        oval(x + 0.9, eyeY + 1, 1.6, 2, "#fff9ff")
                    }
                    if (mood === "tears") oval(x + 1, eyeY + 6, 3.5, 5, "#a8dbff")
                    if (mood === "grumpy") line(x - 0.3, eyeY + (x < 10 ? 0 : 2), x + 5.3, eyeY + (x < 10 ? 2 : 0), face.features, 2)
                }
            }
            if ((happy && mood !== "blush") || mood === "sparkle" || mood === "playful") {
                ctx.beginPath()
                ctx.moveTo(11.5, mouthY - 0.3)
                ctx.quadraticCurveTo(15, mouthY - 1, 18.5, mouthY - 0.3)
                ctx.bezierCurveTo(18.5, mouthY + 6, 11.5, mouthY + 6, 11.5, mouthY - 0.3)
                ctx.fillStyle = "#f56fa8"
                ctx.fill()
                oval(12.8, mouthY + 2, 4.4, 2.5, "#ffacd1")
            } else if (surprised || mood === "yawn" || mood === "sleepy") {
                oval(13.5, mouthY, 3, surprised ? 4.5 : 2.3, face.features)
            } else if (mood === "kiss") {
                ctx.beginPath(); ctx.moveTo(14, mouthY - 1); ctx.lineTo(17, mouthY + 1)
                ctx.lineTo(14, mouthY + 3); ctx.stroke()
            } else if (mood === "tears" || mood === "grumpy") {
                ctx.beginPath(); ctx.moveTo(12.3, mouthY + 3)
                ctx.quadraticCurveTo(15, mouthY - 1, 17.7, mouthY + 3); ctx.stroke()
            } else {
                ctx.beginPath()
                ctx.moveTo(12.3, mouthY + 0.3)
                ctx.bezierCurveTo(12.8, mouthY + 4.6, 17.2, mouthY + 4.6, 17.7, mouthY + 0.3)
                ctx.stroke()
            }
            if (["cat", "calico", "seal"].indexOf(species) >= 0) {
                for (let y of [19, 22]) {
                    line(1, y, 5, y - 0.5, face.features, 1)
                    line(25, y - 0.5, 29, y, face.features, 1)
                }
            }
            if (species === "pig" || species === "cow") {
                oval(10.5, 19, 9, 6, "#f28ab6")
                oval(12.5, 21, 1.4, 2, "#c76492"); oval(16.2, 21, 1.4, 2, "#c76492")
            }
            if (species === "koala" || species === "capybara") oval(12, 17, 6, 8, "#755064")
            if (species === "bear") {
                oval(10, 18, 10, 8, "#f0c3a0")
                oval(13.3, 19, 3.4, 2.7, face.features)
                line(15, 21, 15, 24, face.features, 1.5)
            }
            if (species === "chick" || species === "penguin") oval(12.5, 18, 5, 3.5, "#ffc561")
            if (mood === "blush") {
                for (let x of [4.5, 7, 22, 24.5]) line(x, 18, x - 0.5, 21, "#ff79b1", 1)
            }
            ctx.restore()
        }
    }
    Timer {
        interval: 3200; repeat: true
        running: face.animate && face.visible && face.opacity > 0 && !face.sleepy
        onTriggered: {
            face.blinking = true
            reopen.restart()
            interval = 2600 + Math.random() * 2200
        }
    }
    Timer {
        id: reopen
        interval: 120
        onTriggered: face.blinking = false
    }
    Timer {
        id: nap
        interval: 30000
        running: face.animate && face.visible && face.opacity > 0 && !face.hovered
        onTriggered: face.sleepy = true
    }
}
