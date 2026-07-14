"""Schemas for crawled pages and structured vision observations."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ContentBlock(BaseModel):
    """One text or image block in source DOM order."""

    kind: Literal["heading", "paragraph", "ordered_list", "unordered_list", "image"]
    text: str = ""
    level: int | None = Field(default=None, ge=1, le=6)
    items: list[str] = Field(default_factory=list)
    image_url: str | None = None
    image_index: int | None = Field(default=None, ge=0)
    alt_text: str = ""
    local_image_path: str | None = None

    model_config = ConfigDict(extra="forbid")


class GuidePage(BaseModel):
    """One statically extracted guide page."""

    page_title: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    blocks: list[ContentBlock]

    model_config = ConfigDict(extra="forbid")

    @property
    def image_blocks(self) -> list[ContentBlock]:
        return [block for block in self.blocks if block.kind == "image"]

    def html_context(self) -> str:
        """Return compact authoritative HTML-derived text for vision context."""
        lines: list[str] = []
        for block in self.blocks:
            if block.text:
                lines.append(block.text)
            lines.extend(block.items)
        return "\n".join(lines)

    def context_for_image(self, image_index: int, radius: int = 3) -> str:
        """Return nearby authoritative text for one screenshot."""
        position = next(
            (
                index
                for index, block in enumerate(self.blocks)
                if block.kind == "image" and block.image_index == image_index
            ),
            None,
        )
        if position is None:
            raise ValueError(f"Unknown image index: {image_index}")
        nearby = self.blocks[max(0, position - radius) : position + radius + 1]
        lines: list[str] = []
        for block in nearby:
            if block.text:
                lines.append(block.text)
            lines.extend(block.items)
        return "\n".join(lines)


class ControlObservation(BaseModel):
    """One control whose label is visible in a screenshot."""

    kind: Literal["button", "checkbox", "dropdown", "tab", "menu", "selector"]
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)

    model_config = ConfigDict(extra="forbid")


class FieldObservation(BaseModel):
    """One visible UI field and its on-screen location."""

    kind: Literal[
        "ip_address",
        "network_address",
        "name",
        "port",
        "text",
        "number",
        "selection",
        "boolean",
        "time",
        "password",
    ]
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    location: str = Field(min_length=1)

    model_config = ConfigDict(extra="forbid")


class VisionExtraction(BaseModel):
    """Strict structured output expected from the vision model."""

    page_title: str = Field(min_length=1)
    image_index: int = Field(ge=0)
    screen_name: str
    purpose: str
    visible_navigation_path: str
    controls: list[ControlObservation]
    fields: list[FieldObservation]
    ordered_steps: list[str]
    warnings: list[str]
    uncertainties: list[str]

    model_config = ConfigDict(extra="forbid")

    @field_validator("ordered_steps", "warnings", "uncertainties")
    @classmethod
    def reject_duplicate_text_items(cls, values: list[str]) -> list[str]:
        """Reject empty or duplicate generated statements."""
        normalized = [value.strip() for value in values]
        if any(not value for value in normalized):
            raise ValueError("Text list items cannot be empty")
        keys = [value.casefold() for value in normalized]
        if len(keys) != len(set(keys)):
            raise ValueError("Text list items must be unique")
        return normalized

    @model_validator(mode="after")
    def require_observation_or_uncertainty(self) -> "VisionExtraction":
        """Prevent an entirely empty result from passing unnoticed."""
        observed = (
            self.screen_name,
            self.purpose,
            self.visible_navigation_path,
            *(control.name for control in self.controls),
            *(field.name for field in self.fields),
            *self.ordered_steps,
            *self.warnings,
        )
        if not any(value.strip() for value in observed) and not self.uncertainties:
            raise ValueError("Vision result must contain observations or uncertainties")
        control_names = [item.name.strip().casefold() for item in self.controls]
        field_names = [item.name.strip().casefold() for item in self.fields]
        if len(control_names) != len(set(control_names)):
            raise ValueError("Control names must be unique")
        if len(field_names) != len(set(field_names)):
            raise ValueError("Field names must be unique")
        overlap = set(control_names) & set(field_names)
        if overlap:
            raise ValueError(
                "The same UI label cannot be both a control and a field: "
                f"{', '.join(sorted(overlap))}"
            )
        return self


class NormalizedGuide(BaseModel):
    """Gemma-edited, review-only guide content derived from approved inputs."""

    page_title: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    overview: str
    navigation_paths: list[str]
    controls: list[ControlObservation]
    fields: list[FieldObservation]
    ordered_steps: list[str]
    warnings: list[str]
    uncertainties: list[str]

    model_config = ConfigDict(extra="forbid")
