# Theme format

Built-in names: default, ocean, rose. Built-ins are bundled as package data;
matching editable examples live under themes/ at the repository root. Changing
an example does not change the bundled theme: pass its file path to preview it.
For example: `./run.sh --demo --theme themes/ocean/theme.json`.

Theme JSON fields are optional and inherit Default values:

| Field | Meaning |
| --- | --- |
| version | Format version, currently 1 |
| name | Display name, 1–60 characters |
| colors | background, border, title, body, muted, accent, progress; #RRGGBB |
| layout | min_width, max_width, min_height, padding_x, padding_y, spacing, radius |
| typography | label_size, title_size, body_size in pixels |
| animation | spring, gentle, or snappy |

```json
{
  "version": 1,
  "name": "My theme",
  "colors": {"accent": "#77c9ef", "progress": "#75d3bd"},
  "layout": {"min_height": 70, "padding_y": 10},
  "animation": "gentle"
}
```

Pydantic validates strict types, hex colors, ranges, and width ordering; unknown
keys are errors. The complete bounds are in themes/schema.json. Files are capped
at 64 KiB. Invalid or missing files fall back to the built-in Default model and
print a diagnostic. Theme names and paths may be set through CLI --theme or
appearance.theme in TOML. CLI takes precedence. Config-relative paths resolve
against the config directory; CLI paths resolve against the launcher's working
directory. run.sh changes to the project directory before launching Pulse.

Theme data reaches only QML. Core queue, rules, sources, and history have no theme
imports. Animation presets are named numerical settings owned by the app;
themes cannot provide animation code. Reduced motion disables shape springs,
uses short fades, and applies immediate meter updates regardless of theme.
Input masks continue following the themed shape. Collapsed pill stays 30 × 30;
expanded cards keep the compact layout and two-line body limit.
Specialized now-playing and volume cards use fixed compact heights of 72 and
58 pixels, respectively; layout.min_height applies to ordinary message cards.

Themes currently support solid colors only. Background images, blur, effects,
theme importers, live reload and a settings editor are not implemented.

Validation references: [Pydantic models](https://docs.pydantic.dev/latest/concepts/models/)
and [strict validation](https://docs.pydantic.dev/latest/concepts/strict_mode/).
