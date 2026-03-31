"""Distribute skills from the monorepo to downstream repos.

Reads distribution.yml for the mapping of downstream repos
to source plugins, then copies skill directories to each repo.

Usage::

    uv run python -m outcomeeng.scripts.distribute_skills --dry-run
    uv run python -m outcomeeng.scripts.distribute_skills --repo foundation
    uv run python -m outcomeeng.scripts.distribute_skills  # distribute all repos
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

MONOREPO_ROOT = Path(__file__).resolve().parents[2]
DISTRIBUTION_CONFIG = MONOREPO_ROOT / "scripts" / "distribution.yml"
README_TEMPLATE = MONOREPO_ROOT / "scripts" / "templates" / "README.md.tpl"
LICENSE_FILE = MONOREPO_ROOT / "LICENSE"

# Directories inside a plugin that are NOT distributed (Claude-specific)
SKIP_DIRS = {"commands", "agents", ".claude-plugin"}


def load_config() -> dict:
    with open(DISTRIBUTION_CONFIG) as f:
        return yaml.safe_load(f)


def parse_skill_frontmatter(skill_md: Path) -> dict[str, str]:
    """Extract name and description from SKILL.md YAML frontmatter."""
    text = skill_md.read_text()
    if not text.startswith("---"):
        return {}
    end = text.index("---", 3)
    frontmatter = yaml.safe_load(text[3:end])
    return {
        "name": frontmatter.get("name", skill_md.parent.name),
        "description": frontmatter.get("description", ""),
    }


def collect_skills(plugins: list[str]) -> list[dict]:
    """Collect all skill directories from the given plugins."""
    skills = []
    for plugin_name in plugins:
        skills_dir = MONOREPO_ROOT / "plugins" / plugin_name / "skills"
        if not skills_dir.is_dir():
            print(f"  Warning: {skills_dir} does not exist, skipping")
            continue
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                print(f"  Warning: {skill_dir} has no SKILL.md, skipping")
                continue
            meta = parse_skill_frontmatter(skill_md)
            skills.append(
                {
                    "source": skill_dir,
                    "name": meta.get("name", skill_dir.name),
                    "description": meta.get("description", ""),
                    "dir_name": skill_dir.name,
                }
            )
    return skills


def clean_description(desc: str) -> str:
    """Extract a short description from the directive-style description."""
    # Remove ALWAYS/NEVER directives, keep just the core description
    desc = desc.strip()
    # Try to extract just the action part from "ALWAYS invoke ... when X. NEVER Y."
    match = re.match(
        r"ALWAYS invoke this skill when (.+?)\.\s*NEVER",
        desc,
        re.DOTALL,
    )
    if match:
        return match.group(1).strip()
    # Try "ALWAYS invoke ... when X."
    match = re.match(r"ALWAYS invoke this skill when (.+?)\.", desc, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Fallback: return first sentence
    first_sentence = desc.split(".")[0].strip()
    return first_sentence if first_sentence else desc


def generate_readme(
    repo_name: str,
    repo_config: dict,
    skills: list[dict],
    github_org: str,
) -> str:
    """Generate README.md content for a downstream repo."""
    template_path = README_TEMPLATE
    if template_path.exists():
        template = template_path.read_text()
    else:
        template = DEFAULT_README_TEMPLATE

    # Build skill table
    skill_rows = []
    for skill in skills:
        desc = clean_description(skill["description"])
        skill_rows.append(f"| `{skill['name']}` | {desc} |")
    skill_table = "\n".join(skill_rows)

    # Build prerequisites section
    prereqs = repo_config.get("prerequisites", [])
    prereq_section = ""
    if prereqs:
        prereq_lines = "\n".join(
            f"- `npx skills add {p.split(' (')[0]}`" for p in prereqs
        )
        prereq_notes = "\n".join(f"  - {p}" for p in prereqs)
        prereq_section = f"""## Prerequisites

Install these first:

{prereq_lines}

{prereq_notes}
"""

    return template.format(
        repo_name=repo_name,
        description=repo_config["description"],
        github_org=github_org,
        skill_table=skill_table,
        skill_count=len(skills),
        prerequisites=prereq_section,
    )


DEFAULT_README_TEMPLATE = """# {repo_name}

{description}

> This repo is auto-generated from [outcomeeng/claude](https://github.com/{github_org}/claude).
> For the Claude Code plugin marketplace, use `claude plugin marketplace add {github_org}/claude`.

## Install

```bash
npx skills add {github_org}/{repo_name}
```

{prerequisites}## Skills ({skill_count})

| Skill | Description |
| ----- | ----------- |
{skill_table}

## License

MIT
"""


def clone_or_fetch(
    repo_name: str,
    github_org: str,
    checkout_dir: Path,
) -> Path:
    """Clone the downstream repo, or fetch if already cloned."""
    repo_path = checkout_dir / repo_name
    repo_url = f"https://github.com/{github_org}/{repo_name}.git"

    if repo_path.exists() and (repo_path / ".git").exists():
        print(f"  Fetching {repo_url}")
        subprocess.run(
            ["git", "fetch", "origin"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        # Reset to match remote
        subprocess.run(
            ["git", "reset", "--hard", "origin/main"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
    else:
        print(f"  Cloning {repo_url}")
        repo_path.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["git", "clone", repo_url, str(repo_path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            # Repo might be empty — init it
            print(f"  Clone failed (empty repo?), initializing fresh")
            subprocess.run(
                ["git", "init"], cwd=repo_path, check=True, capture_output=True
            )
            subprocess.run(
                ["git", "remote", "add", "origin", repo_url],
                cwd=repo_path,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "checkout", "-b", "main"],
                cwd=repo_path,
                check=True,
                capture_output=True,
            )

    return repo_path


def clear_repo_contents(repo_path: Path) -> None:
    """Remove all files except .git directory."""
    for item in repo_path.iterdir():
        if item.name == ".git":
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def _ignore_broken_symlinks(directory: str, contents: list[str]) -> set[str]:
    """Ignore broken symlinks during copytree."""
    ignored = set()
    for item in contents:
        path = Path(directory) / item
        if path.is_symlink() and not path.resolve().exists():
            print(f"    Skipping broken symlink: {path}")
            ignored.add(item)
    return ignored


def copy_skill(skill: dict, dest_dir: Path) -> None:
    """Copy a skill directory to the destination, skipping broken symlinks."""
    source = skill["source"]
    target = dest_dir / skill["dir_name"]
    shutil.copytree(source, target, dirs_exist_ok=True, ignore=_ignore_broken_symlinks)


def has_changes(repo_path: Path) -> bool:
    """Check if the repo has any changes (staged or unstaged)."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())


def commit_and_push(repo_path: Path, message: str) -> None:
    """Stage all changes, commit, and push."""
    subprocess.run(["git", "add", "-A"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    result = subprocess.run(
        ["git", "push", "-u", "origin", "main"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode,
            result.args,
            output=result.stdout,
            stderr=result.stderr,
        )


def distribute_repo(
    repo_name: str,
    repo_config: dict,
    github_org: str,
    checkout_dir: Path,
    dry_run: bool,
    source_sha: str,
) -> None:
    """Distribute skills to a single downstream repo."""
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Distributing: {repo_name}")

    plugins = repo_config["plugins"]
    skills = collect_skills(plugins)

    if not skills:
        print(f"  No skills found for plugins: {plugins}")
        return

    print(f"  Found {len(skills)} skills from plugins: {', '.join(plugins)}")
    for skill in skills:
        print(f"    - {skill['name']} ({skill['dir_name']}/)")

    if dry_run:
        return

    # Clone or fetch
    repo_path = clone_or_fetch(repo_name, github_org, checkout_dir)

    # Clear existing content
    clear_repo_contents(repo_path)

    # Copy skills
    for skill in skills:
        copy_skill(skill, repo_path)

    # Generate README
    readme_content = generate_readme(repo_name, repo_config, skills, github_org)
    (repo_path / "README.md").write_text(readme_content)

    # Copy LICENSE
    if LICENSE_FILE.exists():
        shutil.copy2(LICENSE_FILE, repo_path / "LICENSE")

    # Check for changes and commit
    if has_changes(repo_path):
        message = f"Update skills from outcomeeng/claude@{source_sha[:7]}"
        commit_and_push(repo_path, message)
        print(f"  Pushed changes to {github_org}/{repo_name}")
    else:
        print(f"  No changes to push")


def get_source_sha() -> str:
    """Get the current HEAD SHA of the monorepo."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=MONOREPO_ROOT,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Distribute skills to downstream repos"
    )
    parser.add_argument("--repo", help="Distribute only this repo (default: all)")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done"
    )
    parser.add_argument(
        "--checkout-dir",
        type=Path,
        help="Directory for downstream repo checkouts (default: temp dir)",
    )
    args = parser.parse_args()

    config = load_config()
    github_org = config["github_org"]
    repos = config["repos"]
    source_sha = get_source_sha()

    print(f"Source: outcomeeng/claude @ {source_sha[:7]}")

    # Determine checkout directory
    if args.checkout_dir:
        checkout_dir = args.checkout_dir.resolve()
        checkout_dir.mkdir(parents=True, exist_ok=True)
        cleanup = False
    elif args.dry_run:
        checkout_dir = Path(tempfile.mkdtemp())
        cleanup = True
    else:
        checkout_dir = Path(tempfile.mkdtemp())
        cleanup = False  # Keep for inspection after push
        print(f"Checkout dir: {checkout_dir}")

    # Filter repos if --repo specified
    if args.repo:
        if args.repo not in repos:
            print(f"Error: unknown repo '{args.repo}'. Available: {', '.join(repos)}")
            sys.exit(1)
        target_repos = {args.repo: repos[args.repo]}
    else:
        target_repos = repos

    # Distribute
    for repo_name, repo_config in target_repos.items():
        distribute_repo(
            repo_name,
            repo_config,
            github_org,
            checkout_dir,
            args.dry_run,
            source_sha,
        )

    if cleanup and checkout_dir.exists():
        shutil.rmtree(checkout_dir)

    print("\nDone.")


if __name__ == "__main__":
    main()
