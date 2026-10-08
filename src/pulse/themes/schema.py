from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Color = Annotated[str, Field(pattern=r"^#[0-9a-fA-F]{6}$")]


class ThemeModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class Colors(ThemeModel):
    background: Color = "#101014"
    border: Color = "#35353c"
    title: Color = "#eeeeef"
    body: Color = "#bebec8"
    muted: Color = "#aaaab5"
    accent: Color = "#b3a0fa"
    progress: Color = "#8ccebb"


class Layout(ThemeModel):
    min_width: int = Field(default=300, ge=260, le=380)
    max_width: int = Field(default=380, ge=260, le=380)
    min_height: int = Field(default=70, ge=60, le=90)
    padding_x: int = Field(default=20, ge=12, le=22)
    padding_y: int = Field(default=10, ge=8, le=14)
    spacing: int = Field(default=3, ge=2, le=6)
    radius: int = Field(default=20, ge=12, le=24)

    @model_validator(mode="after")
    def ordered_widths(self):
        if self.min_width > self.max_width:
            raise ValueError("min_width must not exceed max_width")
        return self


class Typography(ThemeModel):
    label_size: int = Field(default=10, ge=9, le=11)
    title_size: int = Field(default=14, ge=12, le=16)
    body_size: int = Field(default=12, ge=10, le=13)


class Theme(ThemeModel):
    version: Literal[1] = 1
    name: str = Field(default="Default", min_length=1, max_length=60)
    colors: Colors = Field(default_factory=Colors)
    layout: Layout = Field(default_factory=Layout)
    typography: Typography = Field(default_factory=Typography)
    animation: Literal["spring", "gentle", "snappy"] = "spring"


PRESETS = {
    "spring": {"spring": 3.5, "width_damping": 0.32, "height_damping": 0.35, "fade": 120, "meter": 160},
    "gentle": {"spring": 3.0, "width_damping": 0.55, "height_damping": 0.55, "fade": 160, "meter": 200},
    "snappy": {"spring": 5.0, "width_damping": 0.45, "height_damping": 0.45, "fade": 90, "meter": 110},
}


def qml_data(theme):
    result = theme.model_dump()
    result["animation"] = dict(PRESETS[theme.animation])
    return result
