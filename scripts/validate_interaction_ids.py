#!/usr/bin/env python3
"""Validate interaction IDs used by translated Hugo blog posts."""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path
from typing import Any


INTERACTION_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _display_path(path: Path, content_root: Path) -> str:
    try:
        return str(path.relative_to(content_root))
    except ValueError:
        return str(path)


def read_front_matter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "+++":
        raise ValueError("missing opening TOML +++ delimiter")

    try:
        closing_delimiter = lines.index("+++", 1)
    except ValueError as exc:
        raise ValueError("missing closing TOML +++ delimiter") from exc

    try:
        return tomllib.loads("\n".join(lines[1:closing_delimiter]))
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"invalid TOML front matter: {exc}") from exc


def validate_content(content_root: Path) -> list[str]:
    """Return validation errors for leaf-bundle blog post interaction IDs."""
    content_root = Path(content_root)
    if not content_root.is_dir():
        return [f"{content_root}: content root is not a directory"]

    errors: list[str] = []
    bundle_ids: dict[Path, set[str]] = {}
    id_bundles: dict[str, set[Path]] = {}

    for path in sorted(content_root.glob("blog/*/index.*.md")):
        display_path = _display_path(path, content_root)
        try:
            front_matter = read_front_matter(path)
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(f"{display_path}: {exc}")
            continue

        has_interaction_id = "interactionId" in front_matter
        if not has_interaction_id:
            if front_matter.get("draft") is not True:
                errors.append(
                    f"{display_path}: interactionId is required for published posts"
                )
            continue

        interaction_id = front_matter["interactionId"]
        if not isinstance(interaction_id, str):
            errors.append(f"{display_path}: interactionId must be a string")
            continue
        if not 1 <= len(interaction_id) <= 80:
            errors.append(
                f"{display_path}: interactionId must be 1 to 80 characters"
            )
            continue
        if INTERACTION_ID_PATTERN.fullmatch(interaction_id) is None:
            errors.append(
                f"{display_path}: interactionId must match "
                "^[a-z0-9]+(?:-[a-z0-9]+)*$"
            )
            continue

        bundle = path.parent
        bundle_ids.setdefault(bundle, set()).add(interaction_id)
        id_bundles.setdefault(interaction_id, set()).add(bundle)

    for bundle, interaction_ids in sorted(bundle_ids.items()):
        if len(interaction_ids) > 1:
            display_bundle = _display_path(bundle, content_root)
            joined_ids = ", ".join(sorted(interaction_ids))
            errors.append(
                f"translations in bundle {display_bundle} must share one "
                f"interactionId; found: {joined_ids}"
            )

    for interaction_id, bundles in sorted(id_bundles.items()):
        if len(bundles) > 1:
            joined_bundles = ", ".join(
                _display_path(bundle, content_root) for bundle in sorted(bundles)
            )
            errors.append(
                f"interactionId '{interaction_id}' is reused by bundles: "
                f"{joined_bundles}"
            )

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("content_root", nargs="?", type=Path, default=Path("content"))
    args = parser.parse_args(argv)

    errors = validate_content(args.content_root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(
            f"interaction ID validation failed with {len(errors)} error(s)",
            file=sys.stderr,
        )
        return 1

    print("interaction ID validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
