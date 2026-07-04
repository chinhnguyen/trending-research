from enum import Enum

from pydantic import BaseModel, Field


class NailShape(str, Enum):
    ALMOND = "almond"
    COFFIN = "coffin"
    ROUND = "round"
    SQUARE = "square"
    STILETTO = "stiletto"


class NailLength(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class FinishPreference(str, Enum):
    GLOSSY = "glossy"
    MATTE = "matte"
    CHROME = "chrome"
    GLITTER = "glitter"
    SHEER = "sheer"


class UserPreferences(BaseModel):
    """Inputs for personalized 'you may like it' nail trend recommendations."""

    display_name: str = Field(default="Guest")
    favorite_colors: list[str] = Field(
        default_factory=list,
        description="Hex codes or color names the user likes",
    )
    avoided_colors: list[str] = Field(default_factory=list)
    preferred_shapes: list[NailShape] = Field(default_factory=list)
    preferred_lengths: list[NailLength] = Field(default_factory=list)
    preferred_finishes: list[FinishPreference] = Field(default_factory=list)
    style_keywords: list[str] = Field(
        default_factory=list,
        description="e.g. minimalist, Y2K, floral, abstract",
    )
    occasion: str | None = Field(
        default=None,
        description="Optional context: everyday, wedding, holiday, office",
    )
    budget: str | None = Field(
        default=None,
        description="Optional: drugstore, salon, luxury",
    )
    notes: str | None = Field(default=None)
