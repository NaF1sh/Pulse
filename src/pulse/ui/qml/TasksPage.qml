import QtQuick
import QtQuick.Controls
Flickable {
    id: page
    property var controller
    clip: true; contentHeight: content.implicitHeight
    ScrollBar.vertical: ScrollBar {}
    Column {
        id: content; width: page.width - 12; spacing: 16
        Text { width: parent.width; text: "Let your tools work. Know when they need you."; color: "#f1f2f4"; font.pixelSize: 17; wrapMode: Text.Wrap }
        Text { width: parent.width; text: "Tasks appear in your floating island. Click the task count to review activity without leaving it. Permission requests stay in the original tool."; color: "#b9bdc8"; font.pixelSize: 12; wrapMode: Text.Wrap; lineHeight: 1.4 }
        Text { text: "Try a terminal job"; color: "#b3a0fa"; font.pixelSize: 12; font.bold: true }
        SurfaceField { width: parent.width; readOnly: true; selectByMouse: true; text: 'pulse run --title "Run tests" -- npm test'; Accessible.name: "Example task command" }
        Text { width: parent.width; text: "Run this from your project’s terminal. Pulse reports success or failure while output and interactive prompts stay in that terminal."; color: "#999da9"; font.pixelSize: 11; wrapMode: Text.Wrap }
        Text { text: "Connect an AI tool"; color: "#b3a0fa"; font.pixelSize: 12; font.bold: true }
        Text { width: parent.width; text: "The local task interface accepts working, needs-input, needs-permission, done, failed, and cancelled events. A Claude Code hook adapter is included; setup instructions are in docs/tasks.md in the repository."; color: "#b9bdc8"; font.pixelSize: 12; wrapMode: Text.Wrap; lineHeight: 1.4 }
        Text { width: parent.width; text: "Only connected tools report status. Pulse does not inspect conversations, infer permissions, or approve actions. A working task shows its last reported state; dismiss it if the originating tool has stopped without sending an update."; color: "#999da9"; font.pixelSize: 11; wrapMode: Text.Wrap }
        Text { width: parent.width; text: page.controller ? (page.controller.tasks.summary.error || (page.controller.tasks.summary.connected ? "Local task connection ready" : "Task events are disabled in this session")) : ""; color: "#b3a0fa"; font.pixelSize: 12; wrapMode: Text.Wrap }
    }
}
