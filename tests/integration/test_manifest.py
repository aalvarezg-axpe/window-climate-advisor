"""Tests for the integration manifest."""

import json
from pathlib import Path

MANIFEST_PATH = (
    Path(__file__).parents[2]
    / "custom_components"
    / "window_climate_advisor"
    / "manifest.json"
)
INTEGRATION_PATH = MANIFEST_PATH.parent
HACS_PATH = MANIFEST_PATH.parents[2] / "hacs.json"
BRAND_ICON_PATH = INTEGRATION_PATH / "brand" / "icon.png"


def _translation_keys(value: object) -> object:
    """Return only the nested key structure of a translation document."""
    if isinstance(value, dict):
        return {key: _translation_keys(item) for key, item in value.items()}
    return None


def test_manifest_declares_a_calculated_helper() -> None:
    """The manifest has the required Phase 00 integration metadata."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest == {
        "domain": "window_climate_advisor",
        "name": "Window Climate Advisor",
        "version": "0.2.0b5",
        "config_flow": True,
        "dependencies": ["sun"],
        "documentation": (
            "https://github.com/aalvarezg-axpe/window-climate-advisor#readme"
        ),
        "integration_type": "helper",
        "iot_class": "calculated",
        "issue_tracker": (
            "https://github.com/aalvarezg-axpe/window-climate-advisor/issues"
        ),
        "codeowners": ["@aalvarezg-axpe"],
    }
    assert not (MANIFEST_PATH.parent / "strings.json").exists()


def test_hacs_distribution_metadata_is_complete() -> None:
    """The shadow candidate has the minimum versioned HACS contract."""
    assert json.loads(HACS_PATH.read_text(encoding="utf-8")) == {
        "name": "Window Climate Advisor",
        "homeassistant": "2026.8.0",
        "hide_default_branch": True,
    }
    assert BRAND_ICON_PATH.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


def test_custom_integration_translations_are_complete() -> None:
    """English and Spanish custom-integration translations stay in sync."""
    translations = INTEGRATION_PATH / "translations"
    english = json.loads((translations / "en.json").read_text(encoding="utf-8"))
    spanish = json.loads((translations / "es.json").read_text(encoding="utf-8"))

    assert _translation_keys(spanish) == _translation_keys(english)
    assert not (MANIFEST_PATH.parents[2] / "translations" / "es.json").exists()
