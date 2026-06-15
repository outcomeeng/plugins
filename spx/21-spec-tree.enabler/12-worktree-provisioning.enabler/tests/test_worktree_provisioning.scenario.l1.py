"""Level 1 scenario tests for init-worktrees provisioning over real git.

The scenarios run the provisioning module against a throwaway bare remote in a
temporary directory (L1: git plus tmp dirs). They prove a prior checkout's
gitignored state is carried to its layout-correct home — ``.spx/`` beside the
git-common-dir byte-for-byte, other gitignored paths into the main checkout;
that an in-place migration renames the prior checkout aside to a husk and builds
the pool at the original path; that local-only branches and tags are pushed to
the remote; that a fresh provision produces a bare repository, a sibling main
checkout at the repository-name path tracking the git-resolved default branch,
and N pool worktrees detached at that tip; that the repository name is derived
from the origin URL rather than a separate input; and that the designation is
branch-agnostic — a repository whose default branch is not ``main`` provisions
and classifies identically.
"""

from __future__ import annotations

import json
import subprocess

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


def test_prior_gitignored_state_is_carried_to_layout_correct_homes() -> None:
    with provisioning_env() as env:
        prior = env.single_checkout("prior")
        env.ignore(prior, ".spx/", "node_modules/")
        payload = b"queued-session\x00\x01\x02 not-ascii\n"
        env.write_ignored(prior, ".spx/sessions/todo/session.md", payload)
        dep = b"built-dependency\n"
        env.write_ignored(prior, "node_modules/.bin/tool", dep)
        container = env.container()

        result = provision(container=container, from_checkout=prior)

        # .spx/ lands beside the git-common-dir at the container level, byte-for-byte.
        assert result.spx_dir == container / ".spx"
        carried_spx = result.spx_dir / "sessions" / "todo" / "session.md"
        assert carried_spx.read_bytes() == payload
        # Every other gitignored path lands inside the main checkout working tree.
        carried_dep = result.main_worktree / "node_modules" / ".bin" / "tool"
        assert carried_dep.read_bytes() == dep
        # The carried paths are moved out of the prior checkout, not copied.
        assert not (prior / ".spx").exists()
        assert not (prior / "node_modules").exists()
        # A standard provision builds beside the prior checkout, renaming nothing
        # aside, so it reports no husk for the operator to remove.
        assert result.prior_husk is None


def test_in_place_migration_renames_prior_aside_and_builds_pool_at_origin_path() -> (
    None
):
    with provisioning_env() as env:
        # A checkout whose basename equals the repository name occupies the
        # target container path, so provisioning must vacate it before building.
        prior = env.single_checkout(env.repo_name)
        env.ignore(prior, ".spx/", "node_modules/")
        env.write_ignored(prior, ".spx/marker.txt", b"carried")
        env.write_ignored(prior, "node_modules/.bin/tool", b"built-dependency\n")

        result = provision(container=prior, from_checkout=prior)

        # The prior checkout is renamed aside to a husk reported for removal.
        assert result.prior_husk == prior.with_name(f"{env.repo_name}.migrate")
        assert result.prior_husk.exists()
        # The pool is built at the original path, nested as <repo>/<repo>.
        assert result.container == prior
        assert result.bare_dir == prior / f"{env.repo_name}.git"
        assert result.main_worktree == prior / env.repo_name
        # .spx/ lands at the container level; other gitignored paths in the main
        # checkout — the in-place rename path carries both, not just .spx/.
        assert result.spx_dir == prior / ".spx"
        assert (result.spx_dir / "marker.txt").read_text(encoding="utf-8") == "carried"
        carried_dep = result.main_worktree / "node_modules" / ".bin" / "tool"
        assert carried_dep.read_bytes() == b"built-dependency\n"
        assert classify(probe(result.main_worktree)) is Layout.POOL


def test_provision_pushes_local_only_refs_to_the_remote() -> None:
    with provisioning_env() as env:
        prior = env.single_checkout("prior")
        env.create_local_branch(prior, "feature-x")
        env.create_local_tag(prior, "v9.9.9")
        container = env.container()

        result = provision(container=container, from_checkout=prior)

        assert "feature-x" in env.origin_branches()
        assert "v9.9.9" in env.origin_tags()
        # The new pool's bare clone fetched the pushed branch via origin/*, so the
        # ref is reachable from the pool, not merely present on the remote.
        assert "origin/feature-x" in env.pool_tracking_refs(result.bare_dir)


def test_provision_refuses_when_the_migrate_husk_path_already_exists() -> None:
    with provisioning_env() as env:
        # An in-place migration renames the prior checkout to <repo>.migrate; a
        # pre-existing husk at that path would be clobbered, so provision refuses.
        prior = env.single_checkout(env.repo_name)
        prior.with_name(f"{env.repo_name}.migrate").mkdir()

        with pytest.raises(FileExistsError):
            provision(container=prior, from_checkout=prior)
        # The rename was blocked, so the prior checkout is intact and unbuilt.
        assert prior.exists()
        assert not (prior / f"{env.repo_name}.git").exists()


def test_provision_refuses_a_container_not_named_for_the_repository() -> None:
    with provisioning_env() as env:
        # The pool nests as <repo>/<repo>; a container not named for the
        # repository would scatter it across the workspace, so provision refuses.
        wrong = env.tmp / "workspace"
        wrong.mkdir()

        with pytest.raises(ValueError):
            provision(container=wrong, origin_url=str(env.origin))


def test_provision_fails_fast_when_a_local_branch_diverges_from_the_remote() -> None:
    with provisioning_env() as env:
        # Clone the prior checkout, then advance the remote's default branch from
        # an independent checkout and add a different commit locally, so the prior
        # checkout's default branch diverges (non-fast-forward) from the remote.
        prior = env.single_checkout("prior")
        other = env.single_checkout("other")
        env.commit_file(other, "remote-change.txt")
        env.push_default(other)
        env.commit_file(prior, "local-change.txt")

        # The push of every local branch is rejected; provision propagates the
        # non-zero git exit rather than silently dropping the diverged branch.
        with pytest.raises(subprocess.CalledProcessError):
            provision(container=env.container(), from_checkout=prior)


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
        env.ignore(prior, ".spx/")
        env.write_ignored(prior, ".spx/marker.txt", b"carried")
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


def test_provision_cli_in_place_reports_the_husk_path_and_carries_state(capsys) -> None:
    with provisioning_env() as env:
        # In-place migration: the prior checkout occupies the container path, so
        # the CLI must serialize the renamed-aside husk for the operator to remove
        # and carry the prior checkout's gitignored state across.
        prior = env.single_checkout(env.repo_name)
        env.ignore(prior, ".spx/")
        env.write_ignored(prior, ".spx/marker.txt", b"carried")

        exit_code = main(["provision", "--container", str(prior), "--from", str(prior)])

        assert exit_code == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["prior_husk"] == str(prior.with_name(f"{env.repo_name}.migrate"))
        assert classify(probe(prior / env.repo_name)) is Layout.POOL
        # The CLI path carried gitignored state, not only serialized the husk.
        assert (prior / ".spx" / "marker.txt").read_text(encoding="utf-8") == "carried"


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


def test_provision_refuses_a_non_gitignored_spx_in_the_prior_checkout() -> None:
    with provisioning_env() as env:
        prior = env.single_checkout("prior")
        # .spx/ is present but not gitignored: the gitignore-driven carry would
        # skip it, so provision must refuse before any change rather than abandon
        # its session state with the removed husk.
        env.create_local_branch(prior, "feature-x")
        (prior / ".spx").mkdir()
        (prior / ".spx" / "marker.txt").write_text("precious", encoding="utf-8")

        with pytest.raises(ValueError):
            provision(container=env.container(), from_checkout=prior)
        # The guard fired before the push, so the local-only branch never reached
        # the remote.
        assert "feature-x" not in env.origin_branches()


def test_provision_carries_spx_when_gitignored_without_a_trailing_slash() -> None:
    with provisioning_env() as env:
        prior = env.single_checkout("prior")
        # `.spx` without a trailing slash is a common .gitignore variant. The
        # guard and carry both read git's own ignore enumeration, so the form of
        # the pattern does not matter — the directory is still carried.
        env.ignore(prior, ".spx")
        env.write_ignored(prior, ".spx/marker.txt", b"carried")
        container = env.container()

        result = provision(container=container, from_checkout=prior)

        assert (result.spx_dir / "marker.txt").read_text(encoding="utf-8") == "carried"


def test_provision_fails_before_building_when_the_container_holds_spx() -> None:
    with provisioning_env() as env:
        prior = env.single_checkout("prior")
        env.ignore(prior, ".spx/")
        env.write_ignored(prior, ".spx/marker.txt", b"x")
        container = env.container()
        (container / ".spx").mkdir()  # the .spx/ carry home is already occupied

        # The .spx/ pre-check in provision() fires before any building — the only
        # reachable carry collision (every other gitignored path lands in the
        # freshly-built main checkout, which cannot already hold it).
        with pytest.raises(FileExistsError):
            provision(container=container, from_checkout=prior)
        # Caught before building, so no half-built pool remains.
        assert not (container / f"{env.repo_name}.git").exists()
        assert not (container / env.repo_name).exists()
