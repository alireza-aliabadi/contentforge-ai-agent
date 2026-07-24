"""Platform style profiles and constraints."""

from backend.api.schemas import PlatformInfo
from backend.models.entities import Platform

PLATFORM_PROFILES: dict[Platform, PlatformInfo] = {
    Platform.LINKEDIN: PlatformInfo(
        id=Platform.LINKEDIN,
        label="LinkedIn",
        max_length=3000,
        style_notes=(
            "Professional tone, first-person optional, short paragraphs, "
            "line breaks for scannability, soft CTA."
        ),
    ),
    Platform.TWITTER: PlatformInfo(
        id=Platform.TWITTER,
        label="X / Twitter",
        max_length=280,
        style_notes="Punchy, concise, hook-first. Prefer threads when expanding depth.",
    ),
    Platform.BLOG: PlatformInfo(
        id=Platform.BLOG,
        label="Blog",
        max_length=None,
        style_notes="Long-form structure with H2/H3 headings, intro, body, conclusion.",
    ),
    Platform.MEDIUM: PlatformInfo(
        id=Platform.MEDIUM,
        label="Medium",
        max_length=None,
        style_notes="Narrative long-form, storytelling + insight, readable sections.",
    ),
    Platform.YOUTUBE_COMMUNITY: PlatformInfo(
        id=Platform.YOUTUBE_COMMUNITY,
        label="YouTube Community",
        max_length=5000,
        style_notes="Conversational, engagement-focused, question-driven CTA.",
    ),
    Platform.CUSTOM: PlatformInfo(
        id=Platform.CUSTOM,
        label="Custom",
        max_length=None,
        style_notes="Follow user prompt constraints; default to clear professional prose.",
    ),
}


def list_platforms() -> list[PlatformInfo]:
    return list(PLATFORM_PROFILES.values())


def get_platform(platform: Platform) -> PlatformInfo:
    return PLATFORM_PROFILES[platform]
