"""Validate the versioned v4.17_pre behaviour catalog."""

import json
from collections.abc import Iterator, Mapping
from pathlib import Path

CATALOG_PATH = (
    Path(__file__).parents[2] / "tests" / "fixtures" / "migration" / "case_catalog.json"
)
REQUIRED_FIELDS = {
    "id",
    "source",
    "inputs",
    "legacy_priority",
    "legacy_output",
    "category",
    "disposition",
    "owner",
    "scenarios",
    "evidence_gap",
}
SOURCE_ARTIFACTS = {"A01", *(f"A{number:02d}" for number in range(3, 11))}
CATEGORIES = {
    "weather_safety",
    "thermal_policy",
    "state_stability",
    "data_quality",
}
DISPOSITIONS = {"keep", "replace", "adapt"}
OWNERS = {f"P01-T{number:02d}" for number in range(2, 10)}
SCENARIOS = {f"S{number:02d}" for number in range(2, 15)}
LEGACY_CODES = {"P", "G", "I", "V", "F", "H"}


def _catalog() -> Mapping[str, object]:
    """Load the catalog as its public JSON contract."""
    document = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    assert isinstance(document, Mapping)
    return document


def _strings(value: object) -> Iterator[str]:
    """Yield nested strings without interpreting catalog behaviour."""
    if isinstance(value, Mapping):
        for child in value.values():
            yield from _strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _strings(child)
    elif isinstance(value, str):
        yield value


def test_catalog_schema_and_case_identity_are_stable() -> None:
    """Require the versioned baseline contract and unique complete cases."""
    catalog = _catalog()
    cases = catalog["cases"]
    assert catalog["schema_version"] == 1
    assert catalog["baseline"] == "v4.17_pre"
    assert isinstance(cases, list)
    assert len(cases) == 27

    ids = [case["id"] for case in cases]
    assert len(ids) == len(set(ids))
    assert set(ids) == {f"C{number:03d}" for number in range(1, 28)}
    assert all(set(case) >= REQUIRED_FIELDS for case in cases)


def test_sources_owners_categories_and_dispositions_are_closed_sets() -> None:
    """Keep every catalog row traceable to accepted evidence and work."""
    cases = _catalog()["cases"]
    artifacts = {
        artifact
        for case in cases
        for artifact in (
            case["source"]["artifact"],
            *case.get("supporting_artifacts", []),
        )
    }

    assert artifacts == SOURCE_ARTIFACTS
    assert all(case["source"]["anchor"] for case in cases)
    assert all(case["inputs"] and case["legacy_output"] for case in cases)
    assert all(case["legacy_priority"] in {1, 2, 3, 4} for case in cases)
    assert {case["category"] for case in cases} == CATEGORIES
    assert {case["disposition"] for case in cases} == DISPOSITIONS
    assert {case["owner"] for case in cases} <= OWNERS


def test_all_accepted_scenarios_and_legacy_thermal_codes_are_mapped() -> None:
    """Cover S02-S14 and every requested P/G/I/V/F/H legacy decision."""
    cases = _catalog()["cases"]
    mapped_scenarios = {scenario for case in cases for scenario in case["scenarios"]}
    output_strings = {
        value for case in cases for value in _strings(case["legacy_output"])
    }

    assert mapped_scenarios == SCENARIOS
    assert output_strings >= LEGACY_CODES


def test_safety_is_kept_and_thermal_policy_is_not_frozen_as_legacy() -> None:
    """Separate immutable weather safety from replaceable thermal policy."""
    cases = _catalog()["cases"]
    weather = [case for case in cases if case["category"] == "weather_safety"]
    thermal = [case for case in cases if case["category"] == "thermal_policy"]

    assert weather
    assert all(case["legacy_priority"] == 1 for case in weather)
    assert all(case["disposition"] == "keep" for case in weather)
    assert thermal
    assert all(case["disposition"] in {"replace", "adapt"} for case in thermal)
    terrace_case = next(case for case in cases if case["id"] == "C011")
    assert terrace_case["owner"] == "P01-T05"
    assert terrace_case["disposition"] == "replace"


def test_terrace_heat_flag_has_no_production_consumer() -> None:
    """Retire the binary heuristic while real geometry remains available."""
    production = CATALOG_PATH.parents[3] / "custom_components"
    source = "".join(
        path.read_text(encoding="utf-8") for path in production.rglob("*.py")
    )

    assert "terraza_caliente" not in source


def test_catalog_contains_no_private_runtime_or_actuator_contract() -> None:
    """Keep characterization independent of one Home Assistant installation."""
    text = CATALOG_PATH.read_text(encoding="utf-8").lower()

    for forbidden in (
        "sensor.",
        "binary_sensor.",
        "input_",
        "notify.",
        "mobile_app",
        "cover.",
        "service:",
    ):
        assert forbidden not in text
