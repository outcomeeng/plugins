"""Filesystem access for diagnostics node evidence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng.distribution.build import build, source_plugin_name
from outcomeeng.distribution.contracts import (
    DIST_DIR_NAME,
    PLUGINS_DIR_NAME,
    SKILL_FILENAME,
    SOURCE_ROOT_NAME,
    Target,
)
from outcomeeng.distribution.diagnose_manifest import (
    DIAGNOSE_SKILL_NAME,
    DIAGNOSE_MANIFEST_RELATIVE_PATH,
    DiagnoseManifest,
    authored_diagnose_manifest_contract,
    shipped_diagnose_manifest_contract,
)
from outcomeeng.validation.spx_version import REQUIRED_SPX_VERSION
from outcomeeng_testing.harnesses.dist_tree import DistTreeReader
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder

# ``parents[2]`` reaches the repository root from
# ``outcomeeng_testing/harnesses/diagnostics.py`` (harnesses ->
# outcomeeng_testing -> repo root).
REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class OwnedDiagnoseManifest:
    """One authored diagnose manifest paired with its owning plugin."""

    plugin_name: str
    path: Path
    manifest: DiagnoseManifest


def authored_diagnose_manifests() -> tuple[OwnedDiagnoseManifest, ...]:
    """Return every authored diagnose manifest with its owning plugin."""
    plugins_root = REPO_ROOT / SOURCE_ROOT_NAME / PLUGINS_DIR_NAME
    manifest_paths = tuple(
        sorted(
            plugin_root / DIAGNOSE_MANIFEST_RELATIVE_PATH
            for plugin_root in plugins_root.iterdir()
            if (plugin_root / DIAGNOSE_MANIFEST_RELATIVE_PATH).is_file()
        )
    )
    return tuple(
        OwnedDiagnoseManifest(
            plugin_name=source_plugin_name(
                manifest_path,
                src_root=REPO_ROOT / SOURCE_ROOT_NAME,
            ),
            path=manifest_path,
            manifest=DiagnoseManifest.read(manifest_path),
        )
        for manifest_path in manifest_paths
    )


def authored_diagnose_manifests_match_contract() -> bool:
    """Return whether every authored manifest matches the source contract."""
    manifests = authored_diagnose_manifests()
    return bool(manifests) and all(
        owned.manifest == authored_diagnose_manifest_contract() for owned in manifests
    )


def rendered_diagnose_manifests_match_their_owners() -> bool:
    """Return whether sibling manifests render only their own plugin identity."""
    return all(
        _rendered_diagnose_manifest_matches_owners(owned)
        for owned in authored_diagnose_manifests()
    )


def _rendered_diagnose_manifest_matches_owners(
    authored: OwnedDiagnoseManifest,
) -> bool:
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        builder = SrcTreeBuilder(root)
        for owner in Target:
            builder.add_plugin(
                owner.value,
                skills={
                    DIAGNOSE_SKILL_NAME: authored.path.with_name(
                        SKILL_FILENAME
                    ).read_text(encoding="utf-8")
                },
            )
            manifest_path = (
                builder.src_root
                / PLUGINS_DIR_NAME
                / owner.value
                / DIAGNOSE_MANIFEST_RELATIVE_PATH
            )
            manifest_path.write_text(
                authored.path.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

        build(builder.src_root, root / DIST_DIR_NAME)
        reader = DistTreeReader(root)
        return all(
            DiagnoseManifest.read(
                reader.target_root(target)
                / owner.value
                / DIAGNOSE_MANIFEST_RELATIVE_PATH
            )
            == shipped_diagnose_manifest_contract(
                plugin_name=owner.value,
                spx_floor=REQUIRED_SPX_VERSION,
            )
            for owner in Target
            for target in Target
        )


def canonical_shipped_diagnose_manifests_match_contract() -> bool:
    """Return whether every committed target carries the canonical contract."""
    manifests = authored_diagnose_manifests()
    return bool(manifests) and all(
        read_shipped_diagnose_manifest(target, plugin_name=owned.plugin_name)
        == shipped_diagnose_manifest_contract(
            plugin_name=owned.plugin_name,
            spx_floor=REQUIRED_SPX_VERSION,
        )
        for owned in manifests
        for target in Target
    )


def read_shipped_diagnose_manifest(
    target: Target,
    *,
    plugin_name: str,
) -> DiagnoseManifest:
    """Return the shipped diagnose manifest for one distribution target."""
    manifest_path = (
        shipped_dist_reader().target_root(target)
        / plugin_name
        / DIAGNOSE_MANIFEST_RELATIVE_PATH
    )
    return DiagnoseManifest.read(manifest_path)


def shipped_dist_reader() -> DistTreeReader:
    """Return a reader over the committed ``dist/`` tree at the repository root."""
    return DistTreeReader(REPO_ROOT)
