"""Filesystem access for diagnostics node evidence."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng.distribution.build import SKILL_FILENAME, build, source_plugin_name
from outcomeeng.distribution.contracts import (
    DIST_DIR_NAME,
    PLUGINS_DIR_NAME,
    SOURCE_ROOT_NAME,
    Target,
)
from outcomeeng.distribution.diagnose_manifest import (
    DIAGNOSE_SKILL_NAME,
    DIAGNOSE_MANIFEST_RELATIVE_PATH,
    DiagnoseManifest,
    shipped_diagnose_manifest_contract,
)
from outcomeeng.validation.spx_version import REQUIRED_SPX_VERSION
from outcomeeng_testing.harnesses.dist_tree import DistTreeReader
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder

# ``parents[2]`` reaches the repository root from
# ``outcomeeng_testing/harnesses/diagnostics.py`` (harnesses ->
# outcomeeng_testing -> repo root).
REPO_ROOT = Path(__file__).resolve().parents[2]


def authored_diagnose_manifest() -> DiagnoseManifest:
    """Return the authored diagnose manifest."""
    return DiagnoseManifest.read(authored_diagnose_manifest_path())


def authored_diagnose_manifest_path() -> Path:
    """Locate the one authored diagnose manifest by its source contract."""
    plugins_root = REPO_ROOT / SOURCE_ROOT_NAME / PLUGINS_DIR_NAME
    manifests = tuple(
        plugin_root / DIAGNOSE_MANIFEST_RELATIVE_PATH
        for plugin_root in plugins_root.iterdir()
        if (plugin_root / DIAGNOSE_MANIFEST_RELATIVE_PATH).is_file()
    )
    if len(manifests) != 1:
        raise ValueError(
            f"expected exactly one authored diagnose manifest; found {len(manifests)}"
        )
    return manifests[0]


def authored_diagnose_plugin_name() -> str:
    """Return the plugin identity derived from manifest ownership."""
    return source_plugin_name(authored_diagnose_manifest_path())


def rendered_diagnose_manifests_match_their_owners() -> bool:
    """Return whether sibling manifests render only their own plugin identity."""
    authored_manifest_path = authored_diagnose_manifest_path()
    authored_manifest_text = authored_manifest_path.read_text(encoding="utf-8")
    authored_skill_text = authored_manifest_path.with_name(SKILL_FILENAME).read_text(
        encoding="utf-8"
    )

    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        builder = SrcTreeBuilder(root)
        for owner in Target:
            builder.add_plugin(
                owner.value,
                skills={DIAGNOSE_SKILL_NAME: authored_skill_text},
            )
            manifest_path = (
                builder.src_root
                / PLUGINS_DIR_NAME
                / owner.value
                / DIAGNOSE_MANIFEST_RELATIVE_PATH
            )
            manifest_path.write_text(authored_manifest_text, encoding="utf-8")

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
    expected = shipped_diagnose_manifest_contract(
        plugin_name=authored_diagnose_plugin_name(),
        spx_floor=REQUIRED_SPX_VERSION,
    )
    return all(read_shipped_diagnose_manifest(target) == expected for target in Target)


def read_shipped_diagnose_manifest(target: Target) -> DiagnoseManifest:
    """Return the shipped diagnose manifest for one distribution target."""
    manifest_path = (
        shipped_dist_reader().target_root(target)
        / authored_diagnose_plugin_name()
        / DIAGNOSE_MANIFEST_RELATIVE_PATH
    )
    return DiagnoseManifest.read(manifest_path)


def shipped_dist_reader() -> DistTreeReader:
    """Return a reader over the committed ``dist/`` tree at the repository root."""
    return DistTreeReader(REPO_ROOT)
