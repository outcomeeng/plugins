"""Typed source contract for the plugin-shipped diagnose manifest."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final, cast

from outcomeeng.distribution.contracts import (
    PLUGIN_NAME_VARIABLE,
    SKILLS_SUBDIR_NAME,
    SPX_FLOOR_VARIABLE,
    build_variable_token,
)


class DiagnoseManifestField(StrEnum):
    """Top-level diagnose manifest fields."""

    SPX_FLOOR = "spx_floor"
    MARKETPLACE = "marketplace"
    EXPECTED_PLUGINS = "expected_plugins"
    CHECKS = "checks"


class MarketplaceField(StrEnum):
    """Fields identifying the methodology marketplace."""

    NAME = "name"
    SOURCE = "source"


class DiagnoseCheck(StrEnum):
    """Checks selected by the spec-tree diagnose capability."""

    SESSION_ENVIRONMENT = "session-environment"
    SPX_REACHABILITY = "spx-reachability"
    WORKTREE_POOL = "worktree-pool"
    SESSION_STORE = "session-store"
    MARKETPLACE_INSTALL = "marketplace-install"


@dataclass(frozen=True)
class MarketplaceIdentity:
    """Marketplace identity consumed by the diagnose pipeline."""

    name: str
    source: str


@dataclass(frozen=True)
class DiagnoseManifest:
    """Validated diagnose manifest contract."""

    spx_floor: str
    marketplace: MarketplaceIdentity
    expected_plugins: tuple[str, ...]
    checks: tuple[str, ...]

    @classmethod
    def read(cls, path: Path) -> DiagnoseManifest:
        """Read and validate a diagnose manifest from disk."""
        raw: object = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise TypeError(f"{path} must contain a JSON object")
        data = cast(dict[str, object], raw)
        _require_exact_fields(data, DIAGNOSE_MANIFEST_FIELDS, path)

        marketplace_raw = data[DiagnoseManifestField.MARKETPLACE]
        if not isinstance(marketplace_raw, dict):
            raise TypeError(f"{path} marketplace must be an object")
        marketplace = cast(dict[str, object], marketplace_raw)
        _require_exact_fields(marketplace, MARKETPLACE_FIELDS, path)

        plugins_raw = data[DiagnoseManifestField.EXPECTED_PLUGINS]
        if not isinstance(plugins_raw, list):
            raise TypeError(f"{path} expected_plugins must be a list")

        checks_raw = data[DiagnoseManifestField.CHECKS]
        if not isinstance(checks_raw, list):
            raise TypeError(f"{path} checks must be a list")

        return cls(
            spx_floor=_require_string(
                data[DiagnoseManifestField.SPX_FLOOR],
                path,
                DiagnoseManifestField.SPX_FLOOR,
            ),
            marketplace=MarketplaceIdentity(
                name=_require_string(
                    marketplace[MarketplaceField.NAME],
                    path,
                    MarketplaceField.NAME,
                ),
                source=_require_string(
                    marketplace[MarketplaceField.SOURCE],
                    path,
                    MarketplaceField.SOURCE,
                ),
            ),
            expected_plugins=tuple(
                _require_string(value, path, DiagnoseManifestField.EXPECTED_PLUGINS)
                for value in plugins_raw
            ),
            checks=tuple(
                _require_string(value, path, DiagnoseManifestField.CHECKS)
                for value in checks_raw
            ),
        )


DIAGNOSE_SKILL_NAME: Final = "diagnose"
DIAGNOSE_MANIFEST_FILENAME: Final = "manifest.json"
DIAGNOSE_MANIFEST_RELATIVE_PATH: Final = (
    Path(SKILLS_SUBDIR_NAME) / DIAGNOSE_SKILL_NAME / DIAGNOSE_MANIFEST_FILENAME
)
DIAGNOSE_MARKETPLACE: Final = MarketplaceIdentity(
    name="outcomeeng",
    source="outcomeeng/plugins",
)
DIAGNOSE_CHECKS: Final = tuple(DiagnoseCheck)
DIAGNOSE_MANIFEST_FIELDS: Final = frozenset(
    field.value for field in DiagnoseManifestField
)
MARKETPLACE_FIELDS: Final = frozenset(field.value for field in MarketplaceField)
DIAGNOSE_MARKETPLACE_NAME_VARIABLE: Final = "diagnose_marketplace_name"
DIAGNOSE_MARKETPLACE_SOURCE_VARIABLE: Final = "diagnose_marketplace_source"
DIAGNOSE_CHECK_VARIABLE_PREFIX: Final = "diagnose_check_"


def diagnose_check_variable(check: DiagnoseCheck) -> str:
    """Return the build variable that owns one diagnose check value."""
    return f"{DIAGNOSE_CHECK_VARIABLE_PREFIX}{check.name.lower()}"


def diagnose_manifest_render_variables() -> dict[str, object]:
    """Return source-owned values rendered into every diagnose manifest."""
    variables = {
        DIAGNOSE_MARKETPLACE_NAME_VARIABLE: DIAGNOSE_MARKETPLACE.name,
        DIAGNOSE_MARKETPLACE_SOURCE_VARIABLE: DIAGNOSE_MARKETPLACE.source,
    }
    variables.update(
        {diagnose_check_variable(check): check.value for check in DIAGNOSE_CHECKS}
    )
    return variables


def authored_diagnose_manifest_contract() -> DiagnoseManifest:
    """Return the contract expected in authored plugin source."""
    return DiagnoseManifest(
        spx_floor=build_variable_token(SPX_FLOOR_VARIABLE),
        marketplace=MarketplaceIdentity(
            name=build_variable_token(DIAGNOSE_MARKETPLACE_NAME_VARIABLE),
            source=build_variable_token(DIAGNOSE_MARKETPLACE_SOURCE_VARIABLE),
        ),
        expected_plugins=(build_variable_token(PLUGIN_NAME_VARIABLE),),
        checks=tuple(
            build_variable_token(diagnose_check_variable(check))
            for check in DIAGNOSE_CHECKS
        ),
    )


def shipped_diagnose_manifest_contract(
    *, plugin_name: str, spx_floor: str
) -> DiagnoseManifest:
    """Return the rendered contract expected for an owning plugin."""
    return DiagnoseManifest(
        spx_floor=spx_floor,
        marketplace=DIAGNOSE_MARKETPLACE,
        expected_plugins=(plugin_name,),
        checks=tuple(check.value for check in DIAGNOSE_CHECKS),
    )


def _require_exact_fields(
    data: dict[str, object],
    expected: frozenset[str],
    path: Path,
) -> None:
    actual = set(data)
    if actual != expected:
        raise ValueError(
            f"{path} fields must be {sorted(expected)!r}; got {sorted(actual)!r}"
        )


def _require_string(value: object, path: Path, field: StrEnum) -> str:
    if not isinstance(value, str) or not value:
        raise TypeError(f"{path} {field.value} must be a non-empty string")
    return value
