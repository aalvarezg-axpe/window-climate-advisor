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
        "version": "0.1.0",
        "config_flow": True,
        "dependencies": ["sun"],
        "integration_type": "helper",
        "iot_class": "calculated",
        "codeowners": [],
    }
    assert not (MANIFEST_PATH.parent / "strings.json").exists()


def test_custom_integration_translations_are_complete() -> None:
    """English and Spanish custom-integration translations stay in sync."""
    translations = INTEGRATION_PATH / "translations"
    english = json.loads((translations / "en.json").read_text(encoding="utf-8"))
    spanish = json.loads((translations / "es.json").read_text(encoding="utf-8"))

    assert _translation_keys(spanish) == _translation_keys(english)
    assert not (MANIFEST_PATH.parents[2] / "translations" / "es.json").exists()
