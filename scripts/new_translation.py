#!/usr/bin/env python3
"""Safely create one language file by copying an existing bundle translation."""

from __future__ import annotations

import argparse
from pathlib import Path
import re


SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LANGUAGES = {"en", "zh"}
SECTIONS = {"blog", "projects"}


def create_translation(
    content_root: Path,
    slug: str,
    source_language: str,
    target_language: str,
    *,
    section: str = "blog",
) -> Path:
    """Exclusively copy one leaf-bundle language file to another language."""
    if SLUG_PATTERN.fullmatch(slug) is None:
        raise ValueError(
            "slug must contain lowercase letters, numbers, or internal hyphens"
        )
    if source_language not in LANGUAGES or target_language not in LANGUAGES:
        raise ValueError("languages must be en or zh")
    if source_language == target_language:
        raise ValueError("source and target languages must differ")
    if section not in SECTIONS:
        raise ValueError("section must be blog or projects")

    resolved_content_root = Path(content_root).resolve()
    section_path = Path(content_root) / section
    section_root = section_path.resolve()
    try:
        section_root.relative_to(resolved_content_root)
    except ValueError as error:
        raise ValueError(
            f"{section} content root must resolve inside content root"
        ) from error
    bundle = section_path / slug
    resolved_bundle = bundle.resolve()
    try:
        resolved_bundle.relative_to(section_root)
    except ValueError as error:
        raise ValueError(
            f"slug must resolve inside the {section} content root"
        ) from error

    source = bundle / f"index.{source_language}.md"
    target = bundle / f"index.{target_language}.md"
    if not source.is_file():
        raise FileNotFoundError(f"source translation does not exist: {source}")

    resolved_source = source.resolve()
    try:
        resolved_source.relative_to(resolved_bundle)
    except ValueError as error:
        raise ValueError("source translation must resolve inside its bundle") from error

    payload = resolved_source.read_bytes()
    try:
        with target.open("xb") as destination:
            destination.write(payload)
    except FileExistsError:
        raise FileExistsError(f"target translation already exists: {target}") from None
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create a translation by safely copying a leaf-bundle page"
    )
    parser.add_argument("slug")
    parser.add_argument("source_language", choices=sorted(LANGUAGES))
    parser.add_argument("target_language", choices=sorted(LANGUAGES))
    parser.add_argument("--section", choices=sorted(SECTIONS), default="blog")
    parser.add_argument("--content-root", type=Path, default=Path("content"))
    arguments = parser.parse_args(argv)
    try:
        target = create_translation(
            arguments.content_root,
            arguments.slug,
            arguments.source_language,
            arguments.target_language,
            section=arguments.section,
        )
    except (FileNotFoundError, FileExistsError, ValueError) as error:
        parser.error(str(error))
    print(f"Created {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
