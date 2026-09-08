"""Variable Git names and text for synchronization topology construction."""

from dataclasses import dataclass
from uuid import uuid4


def _text() -> str:
    return f"{uuid4()}\n"


@dataclass(frozen=True)
class RepositoryDomain:
    base_branch: str
    feature_branch: str
    alternate_branch: str
    missing_branch: str
    initial_file: str
    feature_file: str
    base_file: str
    alternate_file: str
    renamed_file: str
    untracked_file: str
    initial_content: str
    feature_content: str
    base_content: str
    alternate_content: str
    scratch_content: str
    initial_message: str
    feature_message: str
    base_message: str
    alternate_message: str
    rename_message: str


def repository_domain() -> RepositoryDomain:
    """Generate distinct names and payloads without choosing a sync outcome.

    The topology builders compose these independent values into the declared
    ahead, behind, overlapping, conflicting, and detached relationships.
    Multiple initial lines separate prepend and append edits for real Git merges.
    """
    return RepositoryDomain(
        base_branch=f"base-{uuid4()}",
        feature_branch=f"work/{uuid4()}",
        alternate_branch=f"alternate-{uuid4()}",
        missing_branch=f"missing-{uuid4()}",
        initial_file=f"{uuid4()}.md",
        feature_file=f"{uuid4()}.txt",
        base_file=f"{uuid4()}.txt",
        alternate_file=f"{uuid4()}.txt",
        renamed_file=f"{uuid4()}.md",
        untracked_file=f"{uuid4()}.local",
        initial_content=_text() + _text() + _text(),
        feature_content=_text(),
        base_content=_text(),
        alternate_content=_text(),
        scratch_content=_text(),
        initial_message=str(uuid4()),
        feature_message=str(uuid4()),
        base_message=str(uuid4()),
        alternate_message=str(uuid4()),
        rename_message=str(uuid4()),
    )


@dataclass(frozen=True)
class TrackedEdit:
    staged: bool
    content: str


def tracked_edits() -> tuple[TrackedEdit, ...]:
    """Compose both Git edit placements with independently generated content."""
    return tuple(TrackedEdit(staged, _text()) for staged in (False, True))
