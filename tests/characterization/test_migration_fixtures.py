"""Structural characterization of the immutable migration fixtures."""

import hashlib
from collections.abc import Iterator, Mapping
from pathlib import Path

import pytest
import yaml
from homeassistant.helpers.template import TemplateEnvironment

REPOSITORY_ROOT = Path(__file__).parents[2]
FIXTURES = {
    "v4.17_pre": REPOSITORY_ROOT
    / "tests"
    / "fixtures"
    / "migration"
    / "v4_17_pre"
    / "automation.yaml",
    "v4.16_pre": REPOSITORY_ROOT
    / "tests"
    / "fixtures"
    / "migration"
    / "v4_16_pre"
    / "automation.yaml",
}
EXPECTED_SHA256 = {
    "v4.17_pre": "4f3cec8d2ba8ed0ffd037b2cc2ecb510ddc94a6a75007824d52c7c2f13b0b0ea",
    "v4.16_pre": "974c46e340325f00f7d0d7c6b54afe963d99e58a14c7c13681368caf20fd6acc",
}


def _load_yaml(path: Path) -> Mapping[object, object]:
    """Load one fixture without importing any predecessor module."""
    document = yaml.safe_load(path.read_bytes())
    assert isinstance(document, Mapping)
    return document


def _iter_template_strings(value: object) -> Iterator[str]:
    """Yield all strings containing Jinja syntax from a YAML value tree."""
    if isinstance(value, Mapping):
        for child in value.values():
            yield from _iter_template_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_template_strings(child)
    elif isinstance(value, str) and ("{{" in value or "{%" in value):
        yield value


def _iter_action_strings(value: object) -> Iterator[str]:
    """Yield service action strings from a YAML value tree."""
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in {"action", "service"} and isinstance(child, str):
                yield child
            yield from _iter_action_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_action_strings(child)


@pytest.mark.parametrize("version", FIXTURES)
def test_imported_fixture_has_the_canonical_sha256(version: str) -> None:
    """Preserve the exact bytes selected by the migration inventory."""
    path = FIXTURES[version]

    assert hashlib.sha256(path.read_bytes()).hexdigest() == EXPECTED_SHA256[version]


@pytest.mark.parametrize("version", FIXTURES)
def test_imported_fixture_is_valid_yaml_and_all_templates_compile(
    version: str,
) -> None:
    """Parse YAML and compile every embedded template with HA's environment."""
    path = FIXTURES[version]
    document = _load_yaml(path)
    templates = tuple(_iter_template_strings(document))
    assert templates

    environment = TemplateEnvironment(None)
    for template in templates:
        environment.compile(template, filename=f"{version}:automation.yaml")


def test_v417_and_v416_remain_independent_versioned_baselines() -> None:
    """Keep both versioned fixtures distinct and self-identifying."""
    v417 = _load_yaml(FIXTURES["v4.17_pre"])
    v416 = _load_yaml(FIXTURES["v4.16_pre"])

    assert v417["alias"] == "Clima - Asesor por ventanas y persianas v4.17_pre"
    assert v416["alias"] == "Clima - Asesor por ventanas y persianas v4.16_pre"
    assert FIXTURES["v4.17_pre"] != FIXTURES["v4.16_pre"]
    assert EXPECTED_SHA256["v4.17_pre"] != EXPECTED_SHA256["v4.16_pre"]


@pytest.mark.parametrize("version", FIXTURES)
def test_baseline_has_no_physical_cover_service_action(version: str) -> None:
    """Preserve the recommendation-only baseline invariant."""
    document = _load_yaml(FIXTURES[version])
    actions = tuple(_iter_action_strings(document))

    assert not [action for action in actions if action.split(".", 1)[0] == "cover"]
