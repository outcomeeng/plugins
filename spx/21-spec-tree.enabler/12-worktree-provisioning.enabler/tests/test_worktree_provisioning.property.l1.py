"""Level 1 property test for the shared-``.spx/`` pool invariant.

Across generated pool sizes and worktree names, every worktree of a provisioned
pool — the main checkout and each detached pool worktree — resolves the same
``.spx/`` directory beside the git-common-dir. Real git in tmp dirs (L1).
"""

from __future__ import annotations

from typing import Final

from hypothesis import given, settings
from hypothesis import strategies as st

from outcomeeng_testing.harnesses.worktree_provisioning import (
    git_common_dir,
    load_init_worktrees_module,
    provisioning_env,
)

_module = load_init_worktrees_module()
provision = _module.provision

REPO_NAME: Final = "repo"
MAX_POOL_SIZE: Final = 4
MAX_EXAMPLES: Final = 20

# A pool worktree must not collide with the main checkout, which sits at the
# repository-name path.
WORKTREE_NAME = st.from_regex(r"[a-z][a-z0-9-]{0,7}", fullmatch=True).filter(
    lambda name: name != REPO_NAME
)
POOL_NAMES = st.lists(WORKTREE_NAME, min_size=0, max_size=MAX_POOL_SIZE, unique=True)


@given(names=POOL_NAMES)
@settings(max_examples=MAX_EXAMPLES, deadline=None)
def test_every_worktree_resolves_the_one_spx_beside_the_common_dir(
    names: list[str],
) -> None:
    with provisioning_env(repo_name=REPO_NAME) as env:
        container = env.container()
        result = provision(
            container=container,
            repo_name=env.repo_name,
            origin_url=str(env.origin),
            pool_worktree_names=tuple(names),
        )

        worktrees = [result.main_worktree, *result.pool_worktrees]
        for worktree in worktrees:
            resolved_spx = git_common_dir(worktree).parent / ".spx"
            assert resolved_spx.resolve() == result.spx_dir.resolve()
            assert resolved_spx.is_dir()
