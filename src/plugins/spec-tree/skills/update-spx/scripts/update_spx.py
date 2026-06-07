"""Pure helpers for rendering a product's ``spx/CLAUDE.md`` from the spec-tree template.

The spx-level directory guide is generated, not hand-merged: its customization
surface is declarative frontmatter data — the product name and the enabled-language
list — and its body is rendered from the installed template (see the node's Guide
Render Model ADR). An update re-renders the new template with the guide's existing
config, so new template content propagates while the product name and language
selection are preserved.

Every function operates on document strings and returns document strings — no
filesystem, environment, or subprocess access. The skill's CLI edge reads the
template and guide files and writes the result.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
from dataclasses import dataclass

FRONTMATTER_DELIMITER = "---"
TEMPLATE_VERSION_KEY = "template_version"
TEMPLATE_SOURCE_KEY = "template_source"
PRODUCT_NAME_KEY = "product_name"
LANGUAGES_KEY = "languages"
PRODUCT_NAME_PLACEHOLDER = "{product-name}"
DEFAULT_TEMPLATE_SOURCE = "spec-tree"

_LANG_BLOCK = re.compile(
    r"[ \t]*<!-- lang:(?P<lang>[a-z0-9-]+) -->\n(?P<body>.*?)\n[ \t]*<!-- /lang:(?P=lang) -->\n?",
    re.DOTALL,
)
_BLANK_RUN = re.compile(r"\n{3,}")


@dataclass(frozen=True)
class GuideConfig:
    """The declared customization surface of a rendered guide."""

    product_name: str
    languages: tuple[str, ...]


def _split_frontmatter(text: str) -> tuple[list[str], str]:
    """Split a document into its frontmatter lines and the remaining body."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
        return [], text
    for index in range(1, len(lines)):
        if lines[index].strip() == FRONTMATTER_DELIMITER:
            return lines[1:index], "\n".join(lines[index + 1 :])
    return [], text


def _unquote(value: str) -> str:
    """Strip exactly one matching pair of surrounding quotes, preserving inner quotes."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _frontmatter_value(frontmatter: list[str], key: str) -> str | None:
    """Return the value of ``key`` from frontmatter lines, or None."""
    prefix = f"{key}:"
    for line in frontmatter:
        stripped = line.strip()
        if stripped.startswith(prefix):
            return _unquote(stripped[len(prefix) :].strip())
    return None


def _frontmatter_block(frontmatter: list[str]) -> str:
    return "\n".join([FRONTMATTER_DELIMITER, *frontmatter, FRONTMATTER_DELIMITER])


def _parse_languages(value: str | None) -> tuple[str, ...]:
    """Parse a ``languages`` frontmatter value (``[a, b]`` or ``a, b``) into a tuple."""
    if not value:
        return ()
    inner = value.strip().removeprefix("[").removesuffix("]")
    return tuple(item.strip() for item in inner.split(",") if item.strip())


def parse_template_version(text: str) -> str | None:
    """Return the ``template_version`` value from a document's frontmatter, or None."""
    frontmatter, _ = _split_frontmatter(text)
    return _frontmatter_value(frontmatter, TEMPLATE_VERSION_KEY)


def parse_config(text: str) -> GuideConfig:
    """Read the declared customization config from a guide's frontmatter."""
    frontmatter, _ = _split_frontmatter(text)
    name = _frontmatter_value(frontmatter, PRODUCT_NAME_KEY) or PRODUCT_NAME_PLACEHOLDER
    languages = _parse_languages(_frontmatter_value(frontmatter, LANGUAGES_KEY))
    return GuideConfig(product_name=name, languages=languages)


def has_config(text: str) -> bool:
    """Whether a guide carries the render-model config (a ``product_name`` frontmatter key).

    A guide predating the schema holds the product name in its body, not frontmatter;
    re-rendering it from an empty config would discard the name and language sections.
    """
    frontmatter, _ = _split_frontmatter(text)
    return _frontmatter_value(frontmatter, PRODUCT_NAME_KEY) is not None


def _version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def is_stale(product_version: str, template_version: str) -> bool:
    """Report whether the product version is numerically below the template version.

    A version that is not dotted-numeric is treated as stale rather than crashing — an
    update then normalizes it to the installed version.
    """
    try:
        return _version_tuple(product_version) < _version_tuple(template_version)
    except ValueError:
        return True


def _filter_languages(body: str, languages: tuple[str, ...]) -> str:
    """Keep each ``lang:NAME`` block whose NAME is enabled; drop the rest, markers and all."""

    def replace(match: re.Match[str]) -> str:
        if match.group("lang") in languages:
            return match.group("body") + "\n"
        return ""

    return _LANG_BLOCK.sub(replace, body)


def render(template_text: str, config: GuideConfig, installed_version: str) -> str:
    """Render a guide from the template and the declared config.

    Language-conditional blocks render only for enabled languages, the product-name
    placeholder is substituted, and the output frontmatter records the version,
    source, product name, and enabled-language list so a later update reads them back.
    """
    template_frontmatter, template_body = _split_frontmatter(template_text)
    source = (
        _frontmatter_value(template_frontmatter, TEMPLATE_SOURCE_KEY)
        or DEFAULT_TEMPLATE_SOURCE
    )

    body = _filter_languages(template_body, config.languages)
    body = body.replace(PRODUCT_NAME_PLACEHOLDER, config.product_name)
    body = _BLANK_RUN.sub("\n\n", body)

    out_frontmatter = [
        f'{TEMPLATE_VERSION_KEY}: "{installed_version}"',
        f"{TEMPLATE_SOURCE_KEY}: {source}",
        f'{PRODUCT_NAME_KEY}: "{config.product_name}"',
        f"{LANGUAGES_KEY}: [{', '.join(config.languages)}]",
    ]
    # `_split_frontmatter` uses `str.splitlines()`, which drops the template's
    # trailing newline; normalize so the output always ends with exactly one.
    rendered = f"{_frontmatter_block(out_frontmatter)}\n{body}"
    return rendered.rstrip("\n") + "\n"


def main(argv: list[str] | None = None) -> int:
    """Thin CLI edge: read the template and guide files, run the pure core, emit the result."""
    parser = argparse.ArgumentParser(
        description="Render a product's spx/CLAUDE.md from the spec-tree template."
    )
    parser.add_argument(
        "--template", required=True, help="Path to the canonical template."
    )
    parser.add_argument("--product", help="Path to the product's spx/CLAUDE.md.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Print staleness status only; emit no content.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write the result to --product instead of stdout.",
    )
    parser.add_argument(
        "--name", help="Product name for a scaffold (when the guide is absent)."
    )
    parser.add_argument(
        "--languages", help="Comma-separated enabled languages for a scaffold."
    )
    args = parser.parse_args(argv)

    template_text = pathlib.Path(args.template).read_text(encoding="utf-8")
    installed = parse_template_version(template_text)
    if installed is None:
        print("error: template has no template_version", file=sys.stderr)
        return 2

    product_path = pathlib.Path(args.product) if args.product else None
    product_text = (
        product_path.read_text(encoding="utf-8")
        if product_path is not None and product_path.is_file()
        else None
    )

    if args.check:
        if product_text is None:
            print("absent")
            return 0
        product_version = parse_template_version(product_text)
        print(
            "stale"
            if product_version is None or is_stale(product_version, installed)
            else "current"
        )
        return 0

    if args.write and product_path is None:
        print("error: --write requires --product", file=sys.stderr)
        return 2

    cli_languages = _parse_languages(args.languages) if args.languages else None
    if product_text is None:
        config = GuideConfig(
            product_name=args.name or PRODUCT_NAME_PLACEHOLDER,
            languages=cli_languages or (),
        )
    elif has_config(product_text):
        config = parse_config(product_text)
    elif args.name is not None:
        # Migrate a guide that predates the config schema, using the supplied config.
        config = GuideConfig(product_name=args.name, languages=cli_languages or ())
    else:
        print(
            "error: guide predates the config schema (no product_name); "
            "rerun with --name and --languages",
            file=sys.stderr,
        )
        return 2
    result = render(template_text, config, installed)

    if args.write and product_path is not None:
        product_path.write_text(result, encoding="utf-8")
    else:
        sys.stdout.write(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
