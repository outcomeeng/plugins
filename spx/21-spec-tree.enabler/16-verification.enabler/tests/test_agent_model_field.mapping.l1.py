"""Compliance: every wrapper agent (skills: field present) declares model: sonnet."""

import pathlib
import re

import pytest

AGENTS_DIR = (
    pathlib.Path(__file__).resolve().parents[4]
    / "src"
    / "plugins"
    / "spec-tree"
    / "agents"
)
VALID_MODELS = frozenset({"sonnet"})

_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
_SKILLS_RE = re.compile(r"^skills\s*:", re.MULTILINE)
_MODEL_RE = re.compile(r"^model\s*:\s*(.+)$", re.MULTILINE)


def _parse_agent(path: pathlib.Path) -> tuple[bool, str]:
    """Return (is_wrapper_agent, model_value)."""
    text = path.read_text(encoding="utf-8")
    fm_match = _FRONTMATTER_RE.match(text)
    if not fm_match:
        return False, ""
    block = fm_match.group(1)
    has_skills = bool(_SKILLS_RE.search(block))
    model_match = _MODEL_RE.search(block)
    model = model_match.group(1).strip() if model_match else ""
    return has_skills, model


_agents = sorted(AGENTS_DIR.glob("*.md"))


@pytest.mark.parametrize("agent_path", _agents, ids=[p.name for p in _agents])
def test_wrapper_agent_declares_model(agent_path: pathlib.Path) -> None:
    is_wrapper, model = _parse_agent(agent_path)
    if not is_wrapper:
        pytest.skip("not a wrapper agent")
    assert model in VALID_MODELS, (
        f"{agent_path.name}: model must be one of {sorted(VALID_MODELS)!r}, got {model!r}"
    )
