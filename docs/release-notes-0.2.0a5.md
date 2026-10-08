# Pulse 0.2.0a5 — Move the island

Drag the pet circle or an empty area of the expanded bar to reposition Pulse. Movement
follows the pointer directly after the normal drag threshold; releasing after a drag
does not open, dismiss, or activate the card. Buttons keep their own click behavior.

Positions last only for the current session. Every launch starts at top-middle again,
including after restarting the computer. Cards stay within the screen’s available area
and ease inward when expanded near an edge. Reduce motion disables this adjustment
animation. Content changes wait until a drag finishes so the card stays steady in hand.

Includes Windows, X11, and LayerShellQt placement paths. Automated tests exercise actual
QML dragging, click behavior, edge constraints, fresh-window reset, logical coordinates
at multiple scale factors, and the layer-shell margin adapter. Native Windows and Wayland
compositor movement still need hands-on verification. Windows CI now includes drag tests.

Quit Pulse and rerun the updated installer to update. Previous music, close-button,
uninstall, and stale-shortcut fixes remain included.
