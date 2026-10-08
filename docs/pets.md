# Pulse pets

The two user-provided references are saved in docs/references/animal-mascots.png
and docs/references/pulse-emotes.png. The built-in collection interprets all
19 animals and 19 round emotes as QML vector drawings, rather than using cropped
reference images. Drawings share face geometry and species-specific ears,
markings, muzzles and expressions so they stay clear at 30 pixels.

Right-click the island to open a separate, focusable picker window. Scroll the
grid, then click a preview to apply and save it. Escape closes the picker; Quit
Pulse exits the whole application. Left-click behavior on the island is unchanged.
The idle pet's 30 px footprint is preserved. Animal input regions cover that
small bounding box so ears are not clipped by a circular window mask; round
emotes use the circular mask. Expanded cards keep their rounded mask.

Selection is stored separately from hand-edited TOML at
XDG_CONFIG_HOME/pulse/pet.json, normally ~/.config/pulse/pet.json. Saving uses an
atomic replacement with owner-only file permissions. A missing or malformed
preference uses Lavender. A write failure reports a diagnostic but keeps the
selected pet for this run. --pet ID overrides the saved selection for one run
without overwriting it; choosing in the picker saves a new preference.
--list-pets prints IDs without starting Qt or connecting to the desktop.

Pets use fixed reference-inspired colors, independent of card themes. Hover
shows a happy expression, and inactivity leads to a sleepy expression after
30 seconds. Blinking occurs only while idle and visible. Reduced motion disables
these automatic expression animations. Pet selection does not change capture,
queueing, rules or notification history.

Eligible cards arriving from idle now trigger a brief surprised expression
before expansion. Manually dismissing the last card triggers a happy expression
as the pet returns. Replacement and queued-only updates do not replay the
surprise. Reduced motion disables temporary reactions and their entry delay.

Checks cover catalog completeness, persistence, invalid preferences, save errors,
CLI overrides, and an offscreen render of every preview with an actual click to
select Panda. Desktop picker focus and placement still need user verification.
