"""Level 1 scenario tests for init-worktrees provisioning over real git.

The scenarios run the provisioning module against a throwaway bare remote in a
temporary directory (L1: git plus tmp dirs). They prove a prior checkout's
``.spx/`` is carried across byte-for-byte; that a fresh provision produces a bare
repository, a sibling main checkout at the repository-name path tracking the
git-resolved default branch, and N pool worktrees detached at that tip; that the
repository name is derived from the origin URL rather than a separate input; and
that the designation is branch-agnostic — a repository whose default branch is
not ``main`` provisions and classifies identically.
"""

from __future__ import annotations

import pytest

from outcomeeng_testing.harnesses.worktree_provisioning import (
    head_sha,
    is_bare_repo,
    is_detached,
    load_init_worktrees_module,
    provisioning_env,
    upstream_ref,
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
            origin_url=str(env.origin),
            pool_worktree_names=names,
        )

        assert is_bare_repo(result.bare_dir)
        assert result.bare_dir == container / f"{env.repo_name}.git"
        assert result.main_worktree == container / env.repo_name
        assert classify(probe(result.main_worktree)) is Layout.POOL
        assert upstream_ref(result.main_worktree) == f"origin/{env.default_branch}"

        tip = env.origin_default_tip()
        assert len(result.pool_worktrees) == len(names)
        for worktree in result.pool_worktrees:
            assert worktree.parent == container
            assert is_detached(worktree)
            assert head_sha(worktree) == tip


def test_provision_names_the_main_checkout_from_a_distinctive_origin() -> None:
    # provision takes no repository-name input; the bare dir and main checkout
    # are named from the origin URL, so a distinctively named origin yields a
    # distinctively named, compliant pool — provision and probe cannot disagree.
    with provisioning_env(repo_name="acme-tool") as env:
        container = env.container()

        result = provision(
            container=container,
            origin_url=str(env.origin),
        )

        assert result.bare_dir == container / "acme-tool.git"
        assert result.main_worktree == container / "acme-tool"
        assert classify(probe(result.main_worktree)) is Layout.POOL


def test_provision_designates_main_checkout_by_repo_name_for_non_main_default() -> None:
    with provisioning_env(default_branch="trunk") as env:
        container = env.container()

        result = provision(
            container=container,
            origin_url=str(env.origin),
            pool_worktree_names=("worktree-a",),
        )

        # Designated by the repository name and sibling placement, not the
        # branch: a non-``main`` default classifies identically.
        assert result.main_worktree == container / env.repo_name
        assert classify(probe(result.main_worktree)) is Layout.POOL
        # The main checkout tracks the git-resolved default, never a literal
        # ``origin/main``.
        assert upstream_ref(result.main_worktree) == f"origin/{env.default_branch}"
        # Additional worktrees detach at the resolved default-branch tip.
        tip = env.origin_default_tip()
        for worktree in result.pool_worktrees:
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


def test_probe_classifies_a_bare_repo_without_origin_as_non_compliant() -> None:
    # With no origin remote the classifier cannot name the main checkout, so the
    # bare repository is not a compliant pool.
    with provisioning_env() as env:
        bare = env.bare_without_origin()

        assert classify(probe(bare)) is Layout.NON_COMPLIANT


def test_probe_resolves_the_repo_name_from_an_scp_like_ssh_origin_url() -> None:
    with provisioning_env() as env:
        container = env.container()
        result = provision(
            container=container,
            origin_url=str(env.origin),
        )
        # Re-point origin at an scp-like SSH URL whose repository basename still
        # equals the main checkout; `git remote get-url` reads config only, so no
        # network. A regression in the colon-form parse would mis-name the main
        # checkout and drop the pool to non-compliant.
        env.set_origin_url(result.bare_dir, f"git@github.com:acme/{env.repo_name}.git")

        assert classify(probe(result.main_worktree)) is Layout.POOL


def test_probe_classifies_a_pool_with_a_misnamed_main_checkout_as_non_compliant() -> (
    None
):
    with provisioning_env() as env:
        container = env.container()
        result = provision(
            container=container,
            origin_url=str(env.origin),
        )
        # Move the main checkout to a basename that does not match the origin
        # repository name: probe reads a repository name from origin but finds no
        # sibling worktree matching it, so it identifies no main checkout.
        env.move_worktree(result.bare_dir, result.main_worktree, container / "misnamed")

        assert classify(probe(container / "misnamed")) is Layout.NON_COMPLIANT


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
                "--from",
                str(prior),
            ]
        )

        assert exit_code == 0
        assert is_bare_repo(container / f"{env.repo_name}.git")
        carried = container / ".spx" / "marker.txt"
        assert carried.read_text(encoding="utf-8") == "carried"
        assert classify(probe(container / env.repo_name)) is Layout.POOL


def test_provision_cli_origin_builds_pool() -> None:
    with provisioning_env() as env:
        container = env.container()

        exit_code = main(
            [
                "provision",
                "--container",
                str(container),
                "--origin",
                str(env.origin),
                "--worktree",
                "worktree-a",
            ]
        )

        assert exit_code == 0
        assert is_bare_repo(container / f"{env.repo_name}.git")
        assert classify(probe(container / env.repo_name)) is Layout.POOL
        assert (container / "worktree-a").is_dir()


def test_provision_refuses_a_container_that_already_holds_spx() -> None:
    with provisioning_env() as env:
        prior = env.single_checkout("prior")
        (prior / ".spx").mkdir()
        container = env.container()
        (container / ".spx").mkdir()

        with pytest.raises(FileExistsError):
            provision(
                container=container,
                origin_url=str(env.origin),
                carry_spx=prior / ".spx",
            )
