"""Level 1 scenario tests for init-worktrees provisioning over real git.

Both scenarios run the provisioning module against a throwaway bare remote in a
temporary directory (L1: git plus tmp dirs). One proves a prior checkout's
``.spx/`` is carried across byte-for-byte; the other proves a fresh provision
produces a bare repository, a sibling ``main`` worktree tracking ``origin/main``,
and N pool worktrees detached at the ``origin/main`` tip.
"""

from __future__ import annotations

import pytest

from outcomeeng_testing.harnesses.worktree_provisioning import (
    head_sha,
    is_bare_repo,
    is_detached,
    load_init_worktrees_module,
    provisioning_env,
)

_module = load_init_worktrees_module()
Layout = _module.Layout
classify = _module.classify
main = _module.main
probe = _module.probe
provision = _module.provision


def test_prior_spx_is_carried_across_byte_for_byte() -> None:
    with provisioning_env() as env:
        prior = env.single_checkout("prior")
        spx = prior / ".spx"
        (spx / "sessions" / "todo").mkdir(parents=True)
        payload = b"queued-session\x00\x01\x02 not-ascii\n"
        (spx / "sessions" / "todo" / "session.md").write_bytes(payload)
        container = env.container()

        result = provision(
            container=container,
            repo_name="repo",
            origin_url=str(env.origin),
            carry_spx=spx,
        )

        carried = result.spx_dir / "sessions" / "todo" / "session.md"
        assert carried.read_bytes() == payload
        assert result.spx_dir == container / ".spx"
        assert not spx.exists()


def test_fresh_provision_builds_bare_pool_with_detached_worktrees() -> None:
    with provisioning_env() as env:
        container = env.container()
        names = ("repo-a", "repo-b", "repo-c")

        result = provision(
            container=container,
            repo_name="repo",
            origin_url=str(env.origin),
            pool_worktree_names=names,
        )

        assert is_bare_repo(result.bare_dir)
        assert result.bare_dir == container / "repo.git"
        assert classify(probe(result.main_worktree)) is Layout.POOL

        tip = env.origin_main_tip()
        assert len(result.pool_worktrees) == len(names)
        for worktree in result.pool_worktrees:
            assert worktree.parent == container
            assert is_detached(worktree)
            assert head_sha(worktree) == tip


def test_probe_classifies_a_real_single_checkout() -> None:
    with provisioning_env() as env:
        checkout = env.single_checkout()

        assert classify(probe(checkout)) is Layout.SINGLE


def test_probe_classifies_a_real_non_compliant_checkout() -> None:
    with provisioning_env() as env:
        checkout = env.single_checkout()
        env.attach_linked_worktree(checkout)

        assert classify(probe(checkout)) is Layout.NON_COMPLIANT


def test_provision_cli_from_prior_derives_origin_and_carries_spx() -> None:
    with provisioning_env() as env:
        prior = env.single_checkout("prior")
        (prior / ".spx").mkdir()
        (prior / ".spx" / "marker.txt").write_text("carried", encoding="utf-8")
        container = env.container()

        exit_code = main(
            [
                "provision",
                "--container",
                str(container),
                "--repo",
                "repo",
                "--from",
                str(prior),
            ]
        )

        assert exit_code == 0
        assert is_bare_repo(container / "repo.git")
        carried = container / ".spx" / "marker.txt"
        assert carried.read_text(encoding="utf-8") == "carried"
        assert classify(probe(container / "main")) is Layout.POOL


def test_provision_cli_origin_builds_pool() -> None:
    with provisioning_env() as env:
        container = env.container()

        exit_code = main(
            [
                "provision",
                "--container",
                str(container),
                "--repo",
                "repo",
                "--origin",
                str(env.origin),
                "--worktree",
                "repo-a",
            ]
        )

        assert exit_code == 0
        assert is_bare_repo(container / "repo.git")
        assert classify(probe(container / "main")) is Layout.POOL
        assert (container / "repo-a").is_dir()


def test_provision_refuses_a_container_that_already_holds_spx() -> None:
    with provisioning_env() as env:
        prior = env.single_checkout("prior")
        (prior / ".spx").mkdir()
        container = env.container()
        (container / ".spx").mkdir()

        with pytest.raises(FileExistsError):
            provision(
                container=container,
                repo_name="repo",
                origin_url=str(env.origin),
                carry_spx=prior / ".spx",
            )
