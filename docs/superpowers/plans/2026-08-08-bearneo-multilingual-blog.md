# Bear Neo Multilingual Blog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a locally runnable, GitHub Pages-ready Hugo blog using the pinned Bear Neo theme, optional English/Chinese post translations, localized Home/Posts/Tags navigation, language-specific RSS, automatic browser color matching, Giscus comments, and shared registration-free Kudos upvotes.

**Architecture:** Vendor Bear Neo unchanged at its inspected revision and place every customization in the site-level `layouts`, `assets`, and `i18n` directories. Model posts as multilingual leaf bundles, resolve shared assets through page resources, use an immutable `interactionId` to join translations across Giscus and Kudos, and verify both root-hosted and GitHub project-subpath output with standard-library tests and a focused generated-site base-path verifier.

**Tech Stack:** Hugo Extended 0.164.0, Go templates, TOML, HTML/CSS, browser-native JavaScript modules, Python 3.11+ standard library tests, Node.js 22+ standard library tests, Playwright browser verification, GitHub Actions, GitHub Pages, Giscus, and Kudos/Cloudflare Workers+D1.

---

## Execution preflight

The workspace is not currently a Git repository. Before Task 1, ask for explicit authorization to run `git init -b main`. If authorization is granted, run every commit step below. If authorization is declined, perform the implementation but skip commit commands and report that all changes remain uncommitted. Do not create a GitHub repository, add a remote, push, configure Discussions, or deploy a Cloudflare Worker during this plan.

A Git worktree cannot be created before a repository exists. After an authorized `git init`, the current workspace is the initial isolated working tree; do not relocate the user's source files.

## File map

### Project configuration and documentation

- `hugo.toml`: Hugo version assumptions, language sites, localized menus, permalinks, taxonomies, output formats, and disabled-by-default Giscus/Kudos settings.
- `.gitignore`: generated Hugo and local test output.
- `README.md`: local preview, authoring, validation, GitHub Pages activation, Giscus activation, and Kudos deployment handoff.
- `themes/hugo-bearneo/`: upstream snapshot at commit `f5c57c5ea39a091f0167af6312f4d4e385df2e6c` with no nested Git metadata.
- `themes/hugo-bearneo/UPSTREAM.md`: source URL, commit, vendoring date, and customization boundary.
- `static/.nojekyll`: marker retained in the Pages artifact.
- `.github/workflows/hugo.yml`: test, build, artifact upload, and default-branch Pages deployment.

### Content

- `content/_index.en.md`, `content/_index.zh.md`: minimal localized home content.
- `content/blog/_index.en.md`, `content/blog/_index.zh.md`: localized Posts sections.
- `content/tags/_index.en.md`, `content/tags/_index.zh.md`: localized Tags directory metadata.
- `content/blog/<slug>/index.en.md`: the three migrated English posts.
- `content/blog/<slug>/index.zh.md`: optional future Chinese translation, omitted when unavailable.
- `content/blog/<slug>/<resource>`: only resources referenced by that post.
- `archetypes/blog.md`: draft leaf-bundle front matter with an explicit stable interaction ID.

### Local theme overrides

- `layouts/baseof.html`: language-aware document shell and current-language RSS discovery.
- `layouts/_markup/render-image.html`: accessible localized image markup with URL-decoded page-resource lookup and preserved raw query/fragment suffixes.
- `layouts/_markup/render-link.html`: downloads/links that resolve either translation to the canonical page-resource permalink while preserving raw suffixes.
- `layouts/_shortcodes/bundle-image.html`: resource-aware image zoom with validated explicit width.
- `layouts/home.html`: minimal home renderer.
- `layouts/blog/page.html`: post title/date/content/tags/TOC and interaction composition.
- `layouts/blog/section.html`: Posts page.
- `layouts/taxonomy.html`: Tags overview.
- `layouts/term.html`: one tag's post archive.
- `layouts/home.rss.xml`: blog-only, language-specific feed.
- `layouts/sitemap.xml`: real translation alternates plus English `x-default` for translated sets.
- `layouts/404.html`: localized not-found page.
- `layouts/_partials/header.html`: language-safe home/title link plus a separately labelled real-translation switcher.
- `layouts/_partials/nav.html`: exactly the three localized Home, Posts, and Tags destinations.
- `layouts/_partials/footer.html`: localized current-language RSS and base-safe sitemap links.
- `layouts/_partials/seo_tags.html`: visible-page canonical/real-only alternates plus hidden-page `robots` `noindex` isolation.
- `layouts/_partials/toc.html`: localized accessible table of contents.
- `layouts/_partials/post-list.html`: reusable localized post list/search.
- `layouts/_partials/interaction-id.html`: template-side ID syntax guard and `post:<id>` entity derivation.
- `layouts/_partials/giscus.html`: fully configured, strict, lazy Giscus embed.
- `layouts/_partials/kudos.html`: Bear Neo upvote markup wired to the shared entity.
- `layouts/_partials/custom_head.html`: automatic color metadata and fingerprinted local CSS.
- `assets/css/site.css`: CJK font/line-height, focus, navigation, tags, WCAG-tested semantic colors, and optional-interaction refinements layered over Bear Neo.
- `assets/js/post-search.mjs`: localized, locale-neutral client-side title filtering.
- `assets/js/kudos.mjs`: testable Kudos API client and DOM state controller.
- `i18n/en.toml`, `i18n/zh.toml`: all site chrome in English and Simplified Chinese.

### Verification

- `scripts/__init__.py`: import marker for testable scripts.
- `scripts/validate_interaction_ids.py`: required/syntax/equality/uniqueness validation.
- `scripts/new_translation.py`: safely copies an existing leaf-bundle page to a new language without overwriting or following an escaping content/blog/source path.
- `scripts/check_site.py`: validates its site root and base URL, then reports malformed or base-escaping generated HTML/XML references, including decoded dot segments; it does not perform exhaustive target, fragment, CSS, or `srcset` validation.
- `tests/test_repository.py`: vendoring, provenance, and `.nojekyll` assertions.
- `tests/test_interaction_ids.py`: validator unit tests.
- `tests/test_check_site.py`: focused base-path-verifier unit tests.
- `tests/test_content.py`: exact migrated front matter, headings, links, and resource inventories.
- `tests/test_site.py`: root/project builds, multilingual paths, encoded resource suffixes, content, tags, RSS, hidden-page SEO, semantic contrast, and integration markup.
- `tests/test_authoring.py`: runs the documented `hugo new` and safe translation-copy workflow in an isolated temporary site.
- `tests/test_new_translation.py`: copy, missing-source, and no-overwrite tests for translation creation.
- `tests/post-search.test.mjs`: title-only filtering, hidden-year/count updates, localized no-result announcements, locale-neutral casing, and no-input behavior.
- `tests/kudos.test.mjs`: strict mock HTTP contract for GET/count/state and POST/DELETE toggle behavior.
- `tests/fixtures/content/blog/shared-article/index.en.md`, `index.zh.md`: non-production translation pair.
- `tests/fixtures/content/blog/shared-article/diagram.svg`, `notes.txt`: resources referenced from both fixture translations.
- `tests/fixtures/content/blog/chinese-only/index.zh.md`: non-production unpaired Chinese page.
- `tests/fixtures/interactions.toml`: non-secret Giscus/Kudos fixture configuration.
- `tests/fixtures/incomplete-interactions.toml`, `invalid-giscus*.toml`, `invalid-kudos*.toml`, `invalid-endpoint-*.toml`, `valid-endpoint-*.toml`, `trailing-slash-endpoint.toml`: optional-integration guard fixtures.
- `tests/fixtures/invalid-content/**`, `tests/fixtures/nonstring-content/**`, `tests/fixtures/overlong-content/**`, `tests/fixtures/mismatched-content/**`: dedicated Hugo-failure fixtures.
- `tests/fixtures/missing-id-content/**`, `tests/fixtures/site-id.toml`: prove site parameters cannot satisfy a page identity.

### Preserved source material

The root `beyond-the-cloud.md`, `lekythos-a-shape.md`, `the-miracle-of-istanbul.md`, and `writings-images/` remain untouched. They are migration inputs, not Hugo publishing directories.

---

### Task 1: Establish the vendored-theme and repository baseline

**Files:**
- Create: `tests/test_repository.py`
- Create: `.gitignore`
- Create: `static/.nojekyll`
- Create: `themes/hugo-bearneo/**`
- Create: `themes/hugo-bearneo/UPSTREAM.md`

- [ ] **Step 1: Write the failing repository-boundary test**

```python
# tests/test_repository.py
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "themes" / "hugo-bearneo"
PINNED_COMMIT = "f5c57c5ea39a091f0167af6312f4d4e385df2e6c"


class RepositoryBoundaryTests(unittest.TestCase):
    def test_theme_license_and_provenance_are_vendored(self):
        self.assertIn("MIT License", (THEME / "LICENSE").read_text())
        provenance = (THEME / "UPSTREAM.md").read_text()
        self.assertIn("https://github.com/rokcso/hugo-bearneo", provenance)
        self.assertIn(PINNED_COMMIT, provenance)

    def test_theme_has_no_nested_git_repository(self):
        self.assertFalse((THEME / ".git").exists())

    def test_pages_marker_is_source_controlled(self):
        self.assertTrue((ROOT / "static" / ".nojekyll").is_file())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m unittest tests/test_repository.py -v`

Expected: FAIL because the vendored theme and `.nojekyll` do not exist.

- [ ] **Step 3: Vendor the exact inspected Bear Neo revision**

Use the existing inspected clone when it is still available:

```bash
mkdir -p themes/hugo-bearneo
BEARNEO_VENDOR_TMP="$(mktemp -d)"
git -C /private/tmp/hugo-bearneo-research-20260808 archive --format=tar --output="$BEARNEO_VENDOR_TMP/hugo-bearneo.tar" f5c57c5ea39a091f0167af6312f4d4e385df2e6c
tar -xf "$BEARNEO_VENDOR_TMP/hugo-bearneo.tar" -C themes/hugo-bearneo
```

If that temporary clone is absent, obtain approval for network access, clone the upstream into a fresh `mktemp -d` directory, verify `git rev-parse HEAD` after checking out the pinned commit, and run the same `git archive` operation. Never copy the clone's `.git` directory.

- [ ] **Step 4: Add provenance, generated-file ignores, and the Pages marker**

```markdown
<!-- themes/hugo-bearneo/UPSTREAM.md -->
# Vendored Bear Neo source

- Upstream: https://github.com/rokcso/hugo-bearneo
- Commit: `f5c57c5ea39a091f0167af6312f4d4e385df2e6c`
- Vendored: 2026-08-08
- License: MIT; see `LICENSE` in this directory.

Files tracked by the upstream revision are vendored without modification.
`UPSTREAM.md` is site-owned provenance metadata and is not part of the upstream
snapshot. Site-specific templates, styles, scripts, and translations live at
the project root so a future theme refresh can be reviewed as a replacement of
this directory.
```

```gitignore
# .gitignore
/public/
/resources/
/.hugo_build.lock
.DS_Store
__pycache__/
*.py[cod]
/artifacts/
```

Create an empty `static/.nojekyll` with `apply_patch`.

- [ ] **Step 5: Run the repository-boundary test**

Run: `python3 -m unittest tests/test_repository.py -v`

Expected: 3 tests PASS.

- [ ] **Step 6: Commit the baseline if Git was authorized**

```bash
git add .gitignore static/.nojekyll themes/hugo-bearneo tests/test_repository.py
git commit -m "chore: vendor pinned Bear Neo theme"
```

---

### Task 2: Validate stable interaction identities

**Files:**
- Create: `scripts/__init__.py`
- Create: `scripts/validate_interaction_ids.py`
- Create: `tests/test_interaction_ids.py`

- [ ] **Step 1: Write failing validator tests**

```python
# tests/test_interaction_ids.py
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.validate_interaction_ids import validate_content


def write_post(root: Path, bundle: str, language: str, front_matter: str) -> None:
    target = root / "blog" / bundle / f"index.{language}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"+++\n{front_matter}\n+++\n\n## Body\n", encoding="utf-8")


class InteractionIdTests(unittest.TestCase):
    def validate(self, files: dict[tuple[str, str], str]) -> list[str]:
        with TemporaryDirectory() as temporary:
            content = Path(temporary)
            for (bundle, language), front_matter in files.items():
                write_post(content, bundle, language, front_matter)
            return validate_content(content)

    def test_missing_content_root_is_rejected(self):
        with TemporaryDirectory() as temporary:
            missing = Path(temporary) / "missing"
            self.assertTrue(any("does not exist" in error for error in validate_content(missing)))

    def test_valid_translation_pair_shares_one_id(self):
        errors = self.validate({
            ("shared", "en"): 'draft = false\ninteractionId = "shared-article"',
            ("shared", "zh"): 'draft = false\ninteractionId = "shared-article"',
        })
        self.assertEqual([], errors)

    def test_published_post_requires_id(self):
        errors = self.validate({("missing", "en"): "draft = false"})
        self.assertTrue(any("missing interactionId" in error for error in errors))

    def test_draft_may_omit_id(self):
        self.assertEqual([], self.validate({("draft", "en"): "draft = true"}))

    def test_draft_cannot_supply_an_empty_id(self):
        errors = self.validate({
            ("draft", "en"): 'draft = true\ninteractionId = ""',
        })
        self.assertTrue(any("must match" in error for error in errors))

    def test_rejects_malformed_id(self):
        errors = self.validate({
            ("bad", "en"): 'draft = false\ninteractionId = "Bad ID"',
        })
        self.assertTrue(any("must match" in error for error in errors))

    def test_rejects_non_string_id(self):
        errors = self.validate({
            ("bad-type", "en"): "draft = false\ninteractionId = 42",
        })
        self.assertTrue(any("must be a string" in error for error in errors))

    def test_rejects_overlong_id(self):
        overlong = "a" * 81
        errors = self.validate({
            ("long", "en"): f'draft = false\ninteractionId = "{overlong}"',
        })
        self.assertTrue(any("at most 80" in error for error in errors))

    def test_rejects_mismatched_translation_ids(self):
        errors = self.validate({
            ("pair", "en"): 'draft = false\ninteractionId = "english-id"',
            ("pair", "zh"): 'draft = false\ninteractionId = "chinese-id"',
        })
        self.assertTrue(any("translation mismatch" in error for error in errors))

    def test_rejects_duplicate_id_across_unrelated_bundles(self):
        errors = self.validate({
            ("first", "en"): 'draft = false\ninteractionId = "shared-id"',
            ("second", "en"): 'draft = false\ninteractionId = "shared-id"',
        })
        self.assertTrue(any("reused by unrelated bundles" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest tests/test_interaction_ids.py -v`

Expected: ERROR importing `scripts.validate_interaction_ids`.

- [ ] **Step 3: Implement the validator**

Create an empty `scripts/__init__.py`, then add:

```python
# scripts/validate_interaction_ids.py
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import re
import sys
import tomllib


ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def read_front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("+++\n"):
        raise ValueError("front matter must use TOML +++ delimiters")
    closing = text.find("\n+++\n", 4)
    if closing == -1:
        raise ValueError("front matter has no closing +++ delimiter")
    return tomllib.loads(text[4:closing])


def validate_content(content_root: Path) -> list[str]:
    errors: list[str] = []
    if not content_root.is_dir():
        return [f"content root does not exist or is not a directory: {content_root}"]
    ids_by_bundle: dict[Path, set[str]] = defaultdict(set)
    bundles_by_id: dict[str, set[Path]] = defaultdict(set)

    for path in sorted(content_root.glob("blog/*/index.*.md")):
        relative = path.relative_to(content_root)
        try:
            front_matter = read_front_matter(path)
        except (OSError, ValueError, tomllib.TOMLDecodeError) as error:
            errors.append(f"{relative}: {error}")
            continue

        has_interaction_id = "interactionId" in front_matter
        interaction_id = front_matter.get("interactionId")
        is_draft = bool(front_matter.get("draft", False))
        if not has_interaction_id:
            if not is_draft:
                errors.append(f"{relative}: missing interactionId")
            continue
        if not isinstance(interaction_id, str):
            errors.append(f"{relative}: interactionId must be a string")
            continue
        if not (1 <= len(interaction_id) <= 80) or not ID_PATTERN.fullmatch(interaction_id):
            errors.append(
                f"{relative}: interactionId must match "
                "^[a-z0-9]+(?:-[a-z0-9]+)*$ and be at most 80 characters"
            )
            continue

        bundle = relative.parent
        ids_by_bundle[bundle].add(interaction_id)
        bundles_by_id[interaction_id].add(bundle)

    for bundle, identifiers in sorted(ids_by_bundle.items(), key=lambda item: str(item[0])):
        if len(identifiers) > 1:
            errors.append(
                f"{bundle}: translation mismatch: "
                f"{', '.join(sorted(identifiers))}"
            )

    for interaction_id, bundles in sorted(bundles_by_id.items()):
        if len(bundles) > 1:
            names = ", ".join(str(bundle) for bundle in sorted(bundles, key=str))
            errors.append(
                f"{interaction_id}: reused by unrelated bundles: {names}"
            )

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Hugo post interaction IDs")
    parser.add_argument("content_root", nargs="?", default="content", type=Path)
    arguments = parser.parse_args(argv)
    errors = validate_content(arguments.content_root)
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        print(f"interaction ID validation failed with {len(errors)} error(s)", file=sys.stderr)
        return 1
    print("interaction ID validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the validator tests**

Run: `python3 -m unittest tests/test_interaction_ids.py -v`

Expected: 10 tests PASS, including the missing-content-root regression so an invalid validation target cannot report a false success.

- [ ] **Step 5: Commit the validator if Git was authorized**

```bash
git add scripts tests/test_interaction_ids.py
git commit -m "test: validate shared post interaction ids"
```

---

### Task 3: Scaffold the multilingual Hugo routes

**Files:**
- Create: `hugo.toml`
- Create: `content/_index.en.md`
- Create: `content/_index.zh.md`
- Create: `content/blog/_index.en.md`
- Create: `content/blog/_index.zh.md`
- Create: `content/tags/_index.en.md`
- Create: `content/tags/_index.zh.md`
- Create: `tests/test_site.py`

- [ ] **Step 1: Write a failing localized-route build test**

```python
# tests/test_site.py
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]


def build_site(destination: Path, base_url: str, *extra_arguments: str) -> None:
    # Markup tests stay unminified; Task 13 passes --minify in its production matrix.
    command = [
        "hugo",
        "--source", str(ROOT),
        "--destination", str(destination),
        "--baseURL", base_url,
        "--cleanDestinationDir",
        "--gc",
        *extra_arguments,
    ]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)


class GeneratedSiteTests(unittest.TestCase):
    def test_localized_core_routes_exist(self):
        with TemporaryDirectory() as temporary:
            public = Path(temporary) / "public"
            build_site(public, "https://example.test/")
            expected = [
                "index.html",
                "blog/index.html",
                "tags/index.html",
                "zh/index.html",
                "zh/blog/index.html",
                "zh/tags/index.html",
            ]
            for relative in expected:
                self.assertTrue((public / relative).is_file(), relative)
            self.assertIn("Wenxuan Zhao", (public / "index.html").read_text())
            self.assertIn("赵文轩", (public / "zh/index.html").read_text())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the route test to verify it fails**

Run: `python3 -m unittest tests/test_site.py -v`

Expected: ERROR because `hugo.toml` and content routes do not exist.

- [ ] **Step 3: Create the Hugo configuration**

```toml
# hugo.toml
baseURL = "https://example.org/"
theme = "hugo-bearneo"
defaultContentLanguage = "en"
defaultContentLanguageInSubdir = false
enableRobotsTXT = true
enableGitInfo = false
capitalizeListTitles = false

[taxonomies]
  tag = "tags"

[permalinks.page]
  blog = "/p/:contentbasename/"

[outputs]
  home = ["HTML", "RSS"]
  page = ["HTML"]
  section = ["HTML"]
  taxonomy = ["HTML"]
  term = ["HTML"]

[services.rss]
  limit = 10

[markup.tableOfContents]
  startLevel = 2
  endLevel = 3

[params]
  groupByYear = true
  showPostCount = true
  postSearch = true
  toc = true
  imageZoom = true
  externalLinksNewTab = false

[params.giscus]
  enabled = false
  repo = ""
  repoId = ""
  category = ""
  categoryId = ""

[params.kudos]
  enabled = false
  endpoint = ""

[languages.en]
  direction = "ltr"
  label = "English"
  locale = "en-US"
  title = "Wenxuan Zhao"
  weight = 1

  [languages.en.params]
    description = "Posts by Wenxuan Zhao"
    giscusLanguage = "en"
    dateFormat = ":date_long"

  [[languages.en.menus.main]]
    identifier = "home"
    name = "Home"
    pageRef = "/"
    weight = 10

  [[languages.en.menus.main]]
    identifier = "posts"
    name = "Posts"
    pageRef = "/blog"
    weight = 20

  [[languages.en.menus.main]]
    identifier = "tags"
    name = "Tags"
    pageRef = "/tags"
    weight = 30

[languages.zh]
  direction = "ltr"
  hasCJKLanguage = true
  label = "简体中文"
  locale = "zh-CN"
  title = "赵文轩"
  weight = 2

  [languages.zh.params]
    description = "赵文轩的文章"
    giscusLanguage = "zh-CN"
    dateFormat = ":date_long"

  [[languages.zh.menus.main]]
    identifier = "home"
    name = "首页"
    pageRef = "/"
    weight = 10

  [[languages.zh.menus.main]]
    identifier = "posts"
    name = "文章"
    pageRef = "/blog"
    weight = 20

  [[languages.zh.menus.main]]
    identifier = "tags"
    name = "标签"
    pageRef = "/tags"
    weight = 30
```

- [ ] **Step 4: Create the localized home, Posts, and Tags content roots**

```markdown
+++
title = "Wenxuan Zhao"
+++

[Browse posts]({{< relref "/blog" >}}) · [Browse tags]({{< relref "/tags" >}})
```

Save that as `content/_index.en.md`.

```markdown
+++
title = "赵文轩"
+++

[浏览文章]({{< relref "/blog" >}}) · [浏览标签]({{< relref "/tags" >}})
```

Save that as `content/_index.zh.md`.

```toml
+++
title = "Posts"
+++
```

Save as `content/blog/_index.en.md`; save the same front matter with `title = "文章"` as `content/blog/_index.zh.md`.

```toml
+++
title = "Tags"
+++
```

Save as `content/tags/_index.en.md`; save the same front matter with `title = "标签"` as `content/tags/_index.zh.md`.

- [ ] **Step 5: Run the localized-route test**

Run: `python3 -m unittest tests/test_site.py -v`

Expected: PASS with all six logical pages generated.

- [ ] **Step 6: Confirm Hugo selects the intended language sites without template warnings**

Run: `hugo --gc --minify --printI18nWarnings --printPathWarnings --printUnusedTemplates`

Expected: exit 0; English is emitted at the base, Chinese beneath `/zh/`, and the theme is loaded from the vendored directory.

- [ ] **Step 7: Commit the multilingual scaffold if Git was authorized**

```bash
git add hugo.toml content tests/test_site.py
git commit -m "feat: scaffold English and Chinese Hugo routes"
```

---

### Task 4: Localize the document shell, primary navigation, footer, TOC, and image control

**Files:**
- Create: `i18n/en.toml`
- Create: `i18n/zh.toml`
- Create: `layouts/baseof.html`
- Create: `layouts/_markup/render-image.html`
- Create: `layouts/_markup/render-link.html`
- Create: `layouts/_partials/header.html`
- Create: `layouts/_partials/nav.html`
- Create: `layouts/_partials/footer.html`
- Create: `layouts/_partials/toc.html`
- Create: `layouts/_partials/custom_head.html`
- Create: `layouts/404.html`
- Create: `assets/css/site.css`
- Modify: `tests/test_site.py`

- [ ] **Step 1: Add a failing chrome and automatic-appearance test**

Add imports and helpers to `tests/test_site.py`:

```python
from html.parser import HTMLParser
import re


def read_html(public: Path, relative: str) -> str:
    return (public / relative).read_text(encoding="utf-8")


class PrimaryNavigationParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_primary = False
        self.active_href: str | None = None
        self.active_text: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attributes: list[tuple[str, str | None]]) -> None:
        values = dict(attributes)
        if tag == "nav" and "data-primary-navigation" in values:
            self.in_primary = True
        elif self.in_primary and tag == "a" and "data-primary-link" in values:
            self.active_href = values.get("href")
            self.active_text = []

    def handle_data(self, data: str) -> None:
        if self.active_href is not None:
            self.active_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.active_href is not None:
            self.links.append((self.active_href, "".join(self.active_text).strip()))
            self.active_href = None
            self.active_text = []
        elif tag == "nav" and self.in_primary:
            self.in_primary = False


def primary_navigation(html: str) -> list[tuple[str, str]]:
    parser = PrimaryNavigationParser()
    parser.feed(html)
    return parser.links
```

Add this method to `GeneratedSiteTests`:

```python
    def test_chrome_is_localized_and_uses_browser_color_preference(self):
        with TemporaryDirectory() as temporary:
            public = Path(temporary) / "public"
            build_site(public, "https://example.test/")
            english = read_html(public, "index.html")
            chinese = read_html(public, "zh/index.html")
            self.assertEqual(
                [("/", "Home"), ("/blog/", "Posts"), ("/tags/", "Tags")],
                primary_navigation(english),
            )
            self.assertEqual(
                [("/zh/", "首页"), ("/zh/blog/", "文章"), ("/zh/tags/", "标签")],
                primary_navigation(chinese),
            )
            self.assertIn('<html lang="en-US"', english)
            self.assertIn('<html lang="zh-CN"', chinese)
            self.assertIn('name="color-scheme" content="light dark"', english)
            self.assertIn('name="referrer" content="strict-origin-when-cross-origin"', english)
            self.assertIn('media="(prefers-color-scheme: light)"', english)
            self.assertIn('media="(prefers-color-scheme: dark)"', english)
            self.assertNotIn("theme-toggle", english)
            primary = re.search(r'<nav[^>]*data-primary-navigation[^>]*>(.*?)</nav>', english, re.DOTALL)
            self.assertIsNotNone(primary)
            self.assertNotIn("language-switcher", primary.group(1))
            self.assertIn('class="language-switcher"', english)
```

- [ ] **Step 2: Run the new test to verify it fails**

Run: `python3 -m unittest tests/test_site.py -v`

Expected: FAIL because Bear Neo still renders hardcoded Home/Blog chrome and has no local color metadata.

- [ ] **Step 3: Add complete English and Chinese UI catalogs**

```toml
# i18n/en.toml
[primaryNavigation]
other = "Primary navigation"
[languageNavigation]
other = "Language navigation"
[switchLanguageTo]
other = "Switch language to {{ . }}"
[subscribeVia]
other = "Subscribe via"
[rss]
other = "RSS"
[sitemap]
other = "Sitemap"
[madeWith]
other = "Made with"
[tableOfContents]
other = "Table of contents"
[zoomImage]
other = "Enlarge image: {{ . }}"
[notFound]
other = "Page not found"
[publishedOn]
other = "Published {{ . }}"
[searchPosts]
other = "Search posts"
[noSearchResults]
other = "No matching posts"
[postCount]
one = "{{ . }} post"
other = "{{ . }} posts"
[noPosts]
other = "No posts yet"
[noTags]
other = "No tags yet"
[filteringFor]
other = "Posts tagged “{{ . }}”"
[allTags]
other = "All tags"
[upvoteAdd]
other = "Upvote this post"
[upvoteRemove]
other = "Remove your upvote"
[upvoteLoading]
other = "Loading upvotes"
[upvoteUnavailable]
other = "Upvotes are unavailable"
[upvoteUpdateFailed]
other = "The upvote could not be saved; try again"
[comments]
other = "Comments"
[rssDescription]
other = "Recent posts from {{ . }}"
```

```toml
# i18n/zh.toml
[primaryNavigation]
other = "主导航"
[languageNavigation]
other = "语言导航"
[switchLanguageTo]
other = "切换语言至{{ . }}"
[subscribeVia]
other = "订阅"
[rss]
other = "RSS"
[sitemap]
other = "网站地图"
[madeWith]
other = "网站主题"
[tableOfContents]
other = "目录"
[zoomImage]
other = "放大图片：{{ . }}"
[notFound]
other = "页面未找到"
[publishedOn]
other = "发布于{{ . }}"
[searchPosts]
other = "搜索文章"
[noSearchResults]
other = "没有匹配的文章"
[postCount]
one = "{{ . }} 篇文章"
other = "{{ . }} 篇文章"
[noPosts]
other = "暂无文章"
[noTags]
other = "暂无标签"
[filteringFor]
other = "标签“{{ . }}”下的文章"
[allTags]
other = "全部标签"
[upvoteAdd]
other = "赞同这篇文章"
[upvoteRemove]
other = "取消赞同"
[upvoteLoading]
other = "正在加载赞同数"
[upvoteUnavailable]
other = "赞同功能暂不可用"
[upvoteUpdateFailed]
other = "未能保存赞同，请重试"
[comments]
other = "评论"
[rssDescription]
other = "{{ . }}的最新文章"
```

- [ ] **Step 4: Override the document shell and chrome**

```html
{{- /* Derived from rokcso/hugo-bearneo@f5c57c5ea39a091f0167af6312f4d4e385df2e6c: layouts/_default/baseof.html */ -}}
<!doctype html>
<html lang="{{ .Language.Locale }}" dir="{{ .Language.Direction }}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="referrer" content="strict-origin-when-cross-origin">
  <meta http-equiv="X-Clacks-Overhead" content="GNU Terry Pratchett">
  {{ partial "favicon.html" . }}
  <title>{{ block "title" . }}{{ with .Title }}{{ . }} | {{ end }}{{ .Site.Title }}{{ end }}</title>
  {{ partial "seo_tags.html" . }}
  {{ with .Site.Home.OutputFormats.Get "RSS" }}
    <link rel="alternate" type="{{ .MediaType.Type }}" href="{{ .Permalink }}" title="{{ $.Site.Title }}">
  {{ end }}
  {{ partial "style.html" . }}
  {{ partial "custom_head.html" . }}
</head>
<body>
  <header>{{ partial "header.html" . }}</header>
  <main>{{ block "main" . }}{{ end }}</main>
  <footer>{{ partial "footer.html" . }}</footer>
  {{ partial "custom_body.html" . }}
</body>
</html>
```

```html
{{- /* Derived from rokcso/hugo-bearneo@f5c57c5ea39a091f0167af6312f4d4e385df2e6c: layouts/partials/header.html */ -}}
<a href="{{ .Site.Home.RelPermalink }}" class="title">
  <h1>{{ .Site.Title }}</h1>
</a>
<nav aria-label="{{ T "primaryNavigation" }}" data-primary-navigation>
  {{ partial "nav.html" . }}
</nav>
{{- $currentPage := . -}}
{{- $visibleTranslations := where .AllTranslations "Params.hidden" "ne" true -}}
{{- if and (ge (len $visibleTranslations) 2) (ne .Kind "term") }}
  <nav class="language-switcher" aria-label="{{ T "languageNavigation" }}">
    {{- range $visibleTranslations }}
      {{- if ne .RelPermalink $currentPage.RelPermalink }}
        <a href="{{ .RelPermalink }}" hreflang="{{ .Language.Locale }}" lang="{{ .Language.Locale }}" aria-label="{{ T "switchLanguageTo" .Language.Label }}">{{ .Language.Label }}</a>
      {{- end }}
    {{- end }}
  </nav>
{{- end }}
```

```html
{{- /* Derived from rokcso/hugo-bearneo@f5c57c5ea39a091f0167af6312f4d4e385df2e6c: layouts/partials/nav.html */ -}}
{{- range .Site.Menus.main }}
  <a data-primary-link href="{{ .URL }}"{{ if $.IsMenuCurrent "main" . }} aria-current="page"{{ end }}>{{ .Name }}</a>
{{- end }}
```

```html
{{- /* Derived from rokcso/hugo-bearneo@f5c57c5ea39a091f0167af6312f4d4e385df2e6c: layouts/partials/footer.html */ -}}
{{ with .Site.Home.OutputFormats.Get "RSS" }}
  {{ T "subscribeVia" }} <a href="{{ .RelPermalink }}">{{ T "rss" }}</a>.
  <br>
{{ end }}
{{ T "madeWith" }} <a href="https://github.com/rokcso/hugo-bearneo">Hugo Bear Neo</a>.
<br>
<a href="{{ "sitemap.xml" | relURL }}">{{ T "sitemap" }}</a>.
```

```html
{{- /* Derived from rokcso/hugo-bearneo@f5c57c5ea39a091f0167af6312f4d4e385df2e6c: layouts/partials/toc.html */ -}}
{{ if and .TableOfContents (ne .TableOfContents "<nav id=\"TableOfContents\"></nav>") }}
  <aside class="toc-nav" role="navigation" aria-label="{{ T "tableOfContents" }}">
    {{ .TableOfContents }}
  </aside>
{{ end }}
```

```html
{{- /* Derived from rokcso/hugo-bearneo@f5c57c5ea39a091f0167af6312f4d4e385df2e6c: layouts/404.html */ -}}
{{ define "title" }}404 | {{ .Site.Title }}{{ end }}
{{ define "main" }}
  <h2>404</h2>
  <p>{{ T "notFound" }}</p>
{{ end }}
```

- [ ] **Step 5: Add automatic appearance metadata and local CSS**

```html
{{- /* Derived from rokcso/hugo-bearneo@f5c57c5ea39a091f0167af6312f4d4e385df2e6c: layouts/partials/custom_head.html */ -}}
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#fdfdfd" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#121212" media="(prefers-color-scheme: dark)">
{{ $siteCSS := resources.Get "css/site.css" | minify | fingerprint }}
<link rel="stylesheet" href="{{ $siteCSS.RelPermalink }}" integrity="{{ $siteCSS.Data.Integrity }}">
```

```css
/* assets/css/site.css */
:root {
  color-scheme: light dark;
  --font-primary:
    Verdana,
    "PingFang SC",
    "Hiragino Sans GB",
    "Microsoft YaHei",
    "Noto Sans CJK SC",
    sans-serif;
}

@media (prefers-color-scheme: light) {
  :root {
    --text-color-tertiary: #707070;
    --upvoted-color: #b9473a;
  }
}

html:lang(zh-CN) body {
  line-height: 1.65;
}

html:lang(zh-CN) content {
  line-height: 1.75;
  letter-spacing: normal;
}

a:focus-visible,
button:focus-visible,
input:focus-visible,
.image-zoom-label:focus-visible {
  outline: 2px solid var(--link-color);
  outline-offset: 3px;
}

[data-primary-navigation] {
  align-items: baseline;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

[data-primary-navigation] a {
  margin-right: 0;
}

[aria-current="page"] {
  text-decoration: underline;
  text-underline-offset: 3px;
}

.language-switcher {
  border-left: 1px solid var(--border-color);
  margin-left: 0.25rem;
  padding-left: 0.75rem;
}

.image-zoom-toggle {
  display: block;
  height: 1px;
  opacity: 0;
  position: absolute;
  width: 1px;
}

.image-zoom-toggle:focus-visible + .image-zoom-label {
  outline: 2px solid var(--link-color);
  outline-offset: 3px;
}

.tag-list {
  padding-left: 1.25rem;
}

.tag-list-count {
  color: var(--text-color-secondary);
  margin-left: 0.4rem;
}

.post-interaction {
  margin-top: 2rem;
}

button.upvoted svg {
  fill: currentColor;
}

[data-kudos-state="loading"] button.upvote-btn:disabled,
[data-kudos-state="writing"] button.upvote-btn:disabled {
  cursor: wait;
  opacity: 0.65;
}

[data-kudos-state="error"] button.upvote-btn:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}
```

Add generated-site regressions that merge the effective theme and site custom properties for each browser scheme. Require both `--text-color-tertiary` and `--upvoted-color` to reach at least 4.5:1 against `--bg-color-primary`; require the light overrides above while preserving Bear Neo's dark `#a0a0a0` and `#ff6b6b`; and require the upvoted outline icon to gain the solid `currentColor` fill as a non-color pressed cue.

- [ ] **Step 6: Localize the Bear Neo image render hook**

```html
{{- /* Derived from rokcso/hugo-bearneo@f5c57c5ea39a091f0167af6312f4d4e385df2e6c: layouts/_default/_markup/render-image.html */ -}}
{{- $destination := .Destination -}}
{{- $parsedDestination := urls.Parse $destination -}}
{{- $resourcePath := $parsedDestination.Path -}}
{{- $rawPath := replaceRE `[?#].*$` "" $destination -}}
{{- $suffix := strings.TrimPrefix $rawPath $destination -}}
{{- $src := $destination -}}
{{- with .Page.Resources.Get $resourcePath -}}
  {{- $src = printf "%s%s" .RelPermalink $suffix -}}
{{- end -}}
<figure class="image-caption{{ if .Page.Site.Params.imageZoom }} image-zoom-container{{ end }}">
  {{ if .Page.Site.Params.imageZoom }}
    {{ $controlId := printf "img-%s" (substr (md5 .Destination) 0 8) }}
    <input type="checkbox" id="{{ $controlId }}" class="image-zoom-toggle" aria-label="{{ T "zoomImage" .Text }}">
    <label for="{{ $controlId }}" class="image-zoom-label">
      <img src="{{ $src | safeURL }}" alt="{{ .Text }}" loading="lazy" class="zoomable-image">
    </label>
    <label for="{{ $controlId }}" class="image-zoom-overlay" aria-hidden="true">
      <img src="{{ $src | safeURL }}" alt="" class="zoomable-image">
    </label>
  {{ else }}
    <img src="{{ $src | safeURL }}" alt="{{ .Text }}" loading="lazy">
  {{ end }}
  {{ with .Text }}<figcaption>{{ . }}</figcaption>{{ end }}
</figure>
```

Add a resource-aware link hook. Like the image hook, it parses the destination's URL-decoded path for resource lookup, preserves its raw query/fragment suffix, preserves ordinary/external destinations, and resolves a bundle-local download through its canonical default-language page-resource URL:

```html
{{- /* Derived from rokcso/hugo-bearneo@f5c57c5ea39a091f0167af6312f4d4e385df2e6c: layouts/_default/_markup/render-link.html */ -}}
{{- $destination := .Destination -}}
{{- $parsedDestination := urls.Parse $destination -}}
{{- $resourcePath := $parsedDestination.Path -}}
{{- $rawPath := replaceRE `[?#].*$` "" $destination -}}
{{- $suffix := strings.TrimPrefix $rawPath $destination -}}
{{- $href := $destination -}}
{{- with .Page.Resources.Get $resourcePath -}}
  {{- $href = printf "%s%s" .RelPermalink $suffix -}}
{{- end -}}
{{- $newTabEnabled := .Page.Site.Params.externalLinksNewTab | default false -}}
{{- $isExternal := or (hasPrefix $href "http://") (hasPrefix $href "https://") -}}
{{- $isInternal := and $isExternal (hasPrefix $href .Page.Site.BaseURL) -}}
{{- $attributes := printf "href=%q" $href | safeHTMLAttr -}}
{{- if and $isExternal (not $isInternal) -}}
  {{- if $newTabEnabled -}}
    {{- $attributes = printf "%s target=\"_blank\"" $attributes | safeHTMLAttr -}}
  {{- end -}}
  {{- $attributes = printf "%s rel=\"noopener noreferrer\"" $attributes | safeHTMLAttr -}}
{{- end -}}
{{- with .Title -}}
  {{- $attributes = printf "%s title=%q" $attributes . | safeHTMLAttr -}}
{{- end -}}
<a {{ $attributes }}>{{ .Text | safeHTML }}</a>
```

Cover both hooks with root and project-subpath builds containing English and Chinese pages that reference filenames with percent-encoded spaces, a raw query plus fragment, and `#minipic`. Assert that lookup succeeds against the decoded filename, both languages emit the same default-language resource `.RelPermalink`, the authored suffix is unchanged, and the canonical resource files are published.

- [ ] **Step 7: Run the chrome and route tests**

Run: `python3 -m unittest tests/test_site.py -v`

Expected: all site tests PASS; the primary navigation has exactly three localized destinations, the language switch is outside the primary destination set, encoded resource destinations retain their suffixes, both effective color schemes meet the contrast threshold, and the upvoted icon has a solid-fill cue.

- [ ] **Step 8: Commit the localized shell if Git was authorized**

```bash
git add assets i18n layouts tests/test_site.py
git commit -m "feat: localize Bear Neo chrome and appearance"
```

---

### Task 5: Render Home, Posts, Tags, tag archives, and post pages

**Files:**
- Create: `layouts/home.html`
- Create: `layouts/blog/page.html`
- Create: `layouts/blog/section.html`
- Create: `layouts/taxonomy.html`
- Create: `layouts/term.html`
- Create: `layouts/_partials/post-list.html`
- Create: `assets/js/post-search.mjs`
- Create: `tests/post-search.test.mjs`
- Modify: `tests/test_site.py`

- [ ] **Step 1: Add failing tests for localized empty lists and tag overview behavior**

Add this method to `GeneratedSiteTests`:

```python
    def test_initial_chinese_lists_are_valid_and_empty(self):
        with TemporaryDirectory() as temporary:
            public = Path(temporary) / "public"
            build_site(public, "https://example.test/")
            posts = read_html(public, "zh/blog/index.html")
            tags = read_html(public, "zh/tags/index.html")
            self.assertIn("暂无文章", posts)
            self.assertIn("暂无标签", tags)
            self.assertNotIn("No posts yet", posts)
            self.assertNotIn("No tags yet", tags)

    def test_post_search_has_localized_no_match_feedback(self):
        with TemporaryDirectory() as temporary:
            public = Path(temporary) / "public"
            build_site(public, "https://example.test/")
            english = read_html(public, "blog/index.html")
            self.assertIn('data-search-empty', english)
            self.assertIn("No matching posts", english)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m unittest tests/test_site.py -v`

Expected: FAIL because Bear Neo's fallback list has hardcoded English empty states and no dedicated Tags overview.

- [ ] **Step 3: Add the home and reusable post-list templates**

```html
{{- /* Site-local template; no Bear Neo counterpart. */ -}}
{{ define "main" }}
  <content>{{ .Content }}</content>
{{ end }}
```

```html
{{- /* Derived from rokcso/hugo-bearneo@f5c57c5ea39a091f0167af6312f4d4e385df2e6c: layouts/_default/list.html */ -}}
{{ $page := .Page }}
{{ $pages := (where .Pages "Params.hidden" "ne" true).ByDate.Reverse }}
{{ $count := len $pages }}
<section class="post-list" data-post-list
  data-count-one="{{ replace (T "postCount" 1) "1" "{count}" }}"
  data-count-many="{{ replace (T "postCount" 2) "2" "{count}" }}">
  {{ if and $page.Site.Params.postSearch (gt $count 0) }}
    <label>
      <span class="visually-hidden">{{ T "searchPosts" }}</span>
      <input type="search" data-post-search placeholder="{{ T "searchPosts" }}" autocomplete="off">
    </label>
  {{ end }}
  {{ if $page.Site.Params.showPostCount }}
    <p data-post-count>{{ T "postCount" $count }}</p>
  {{ end }}
  <p data-search-empty hidden>{{ T "noSearchResults" }}</p>
  <ul class="blog-posts">
    {{ range $pages.GroupByDate "2006" }}
      {{ if $page.Site.Params.groupByYear }}<li class="post-year" data-post-year="{{ .Key }}"><strong>{{ .Key }}</strong></li>{{ end }}
      {{ range .Pages }}
        <li data-post-item data-post-year="{{ .Date.Year }}" data-post-title="{{ .Title }}">
          <span class="{{ if $page.Site.Params.groupByYear }}grouped{{ else }}ungrouped{{ end }}">
            <time datetime="{{ .Date.Format "2006-01-02" }}">{{ .Date | time.Format $page.Site.Params.dateFormat }}</time>
          </span>
          <a href="{{ .RelPermalink }}">{{ .Title }}</a>
        </li>
      {{ end }}
    {{ else }}
      <li data-empty-state>{{ T "noPosts" }}</li>
    {{ end }}
  </ul>
</section>
{{ if and $page.Site.Params.postSearch (gt $count 0) }}
  {{ $search := resources.Get "js/post-search.mjs" | fingerprint }}
  <script type="module" src="{{ $search.RelPermalink }}" integrity="{{ $search.Data.Integrity }}"></script>
{{ end }}
```

```javascript
// assets/js/post-search.mjs
for (const root of document.querySelectorAll("[data-post-list]")) {
  const input = root.querySelector("[data-post-search]");
  if (!input) continue;
  const items = [...root.querySelectorAll("[data-post-item]")];
  const years = [...root.querySelectorAll("[data-post-year].post-year")];
  const count = root.querySelector("[data-post-count]");
  const empty = root.querySelector("[data-search-empty]");

  input.addEventListener("input", () => {
    const query = input.value.trim().toLowerCase();
    const visibleYears = new Set();
    let visible = 0;
    for (const item of items) {
      const matches = item.dataset.postTitle.toLowerCase().includes(query);
      item.hidden = !matches;
      if (matches) {
        visible += 1;
        visibleYears.add(item.dataset.postYear);
      }
    }
    for (const year of years) year.hidden = !visibleYears.has(year.dataset.postYear);
    if (empty) empty.hidden = query === "" || visible !== 0;
    if (count) {
      const template = visible === 1 ? root.dataset.countOne : root.dataset.countMany;
      count.textContent = template.replace("{count}", String(visible));
    }
  });
}
```

Use locale-neutral `toLowerCase()` deliberately: title matching must not change with the reader's runtime locale. Add a regression that makes `toLocaleLowerCase()` apply Turkish casing and still requires `istanbul` to match `The Miracle of Istanbul`, proving the search path does not depend on that locale-sensitive method.

- [ ] **Step 4: Add section, taxonomy, term, and page renderers**

```html
{{- /* Derived from rokcso/hugo-bearneo@f5c57c5ea39a091f0167af6312f4d4e385df2e6c: layouts/_default/list.html */ -}}
{{ define "main" }}
  <content>
    <h2>{{ .Title }}</h2>
    {{ partial "post-list.html" (dict "Page" . "Pages" .Pages) }}
  </content>
{{ end }}
```

```html
{{- /* Site-local tag-overview template; Bear Neo has no dedicated counterpart. */ -}}
{{ define "main" }}
  <content>
    <h2>{{ .Title }}</h2>
    <ul class="tag-list">
      {{ range .Data.Terms.Alphabetical }}
        <li><a href="{{ .Page.RelPermalink }}">#{{ .Page.LinkTitle }}</a><span class="tag-list-count">{{ .Count }}</span></li>
      {{ else }}
        <li>{{ T "noTags" }}</li>
      {{ end }}
    </ul>
  </content>
{{ end }}
```

```html
{{- /* Site-local Hugo 0.164 term template. */ -}}
{{ define "main" }}
  <content>
    <h2>{{ T "filteringFor" .Title }}</h2>
    {{ with .Site.GetPage "/tags" }}<p><a href="{{ .RelPermalink }}">{{ T "allTags" }}</a></p>{{ end }}
    {{ partial "post-list.html" (dict "Page" . "Pages" .Pages) }}
  </content>
{{ end }}
```

```html
{{- /* Derived from rokcso/hugo-bearneo@f5c57c5ea39a091f0167af6312f4d4e385df2e6c: layouts/_default/single.html */ -}}
{{ define "main" }}
  <article data-word-count="{{ .WordCount }}">
    <header>
      <h2>{{ .Title }}</h2>
      {{ if not .Date.IsZero }}
        <p><time datetime="{{ .Date.Format "2006-01-02" }}">{{ T "publishedOn" (.Date | time.Format .Site.Params.dateFormat) }}</time></p>
      {{ end }}
    </header>
    <content>{{ .Content }}</content>
    {{ with .GetTerms "tags" }}
      <p class="post-tags">
        {{ range . }}<a href="{{ .RelPermalink }}">#{{ .LinkTitle }}</a> {{ end }}
      </p>
    {{ end }}
    {{ if .Site.Params.toc }}<div class="toc">{{ partial "toc.html" . }}</div>{{ end }}
  </article>
{{ end }}
```

- [ ] **Step 5: Add a utility class for the accessible search label**

Append to `assets/css/site.css`:

```css
.visually-hidden {
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  height: 1px;
  overflow: hidden;
  position: absolute;
  white-space: nowrap;
  width: 1px;
}
```

- [ ] **Step 6: Run the localized list tests and check template selection**

Run: `python3 -m unittest tests/test_site.py -v`

Expected: all site tests PASS.

Run: `node --test tests/post-search.test.mjs`

Expected: 4 tests PASS, covering title-only matching, hidden year/count updates, localized no-results announcements, locale-neutral casing, and safe no-input behavior.

Run: `hugo --gc --minify --printUnusedTemplates`

Expected: Hugo selects `home.html`, `blog/section.html`, `taxonomy.html`, and `term.html`; no local template intended for these kinds is reported unused.

- [ ] **Step 7: Commit the page renderers if Git was authorized**

```bash
git add assets layouts tests/post-search.test.mjs tests/test_site.py
git commit -m "feat: add localized posts and tags pages"
```

---

### Task 6: Migrate “Beyond the Cloud” as an English leaf bundle

**Files:**
- Create: `tests/test_content.py`
- Create: `content/blog/beyond-the-cloud/index.en.md`
- Create: `content/blog/beyond-the-cloud/beyond_the_cloud.v5.pdf`

- [ ] **Step 1: Write the failing migration test**

```python
# tests/test_content.py
from pathlib import Path
import unittest

from scripts.validate_interaction_ids import read_front_matter


ROOT = Path(__file__).resolve().parents[1]
BLOG = ROOT / "content" / "blog"


def body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    closing = text.find("\n+++\n", 4)
    return text[closing + 5:]


class MigratedContentTests(unittest.TestCase):
    def test_beyond_the_cloud_bundle(self):
        post = BLOG / "beyond-the-cloud" / "index.en.md"
        metadata = read_front_matter(post)
        self.assertEqual("Beyond the Cloud: A Perceptual Illusion in Overlaid Bar Charts", metadata["title"])
        self.assertEqual("beyond-the-cloud", metadata["interactionId"])
        self.assertEqual(["visualization", "perception", "research"], metadata["tags"])
        self.assertEqual("2024-05-30", str(metadata["date"]))
        self.assertEqual("2024-05-30", str(metadata["lastmod"]))
        self.assertFalse(metadata["draft"])
        article = body(post)
        self.assertNotIn("\n# Beyond the Cloud", article)
        self.assertIn("## Abstract", article)
        self.assertIn("## Poster", article)
        self.assertIn("[View or download the poster (PDF", article)
        self.assertNotIn("![poster]", article)
        self.assertTrue((post.parent / "beyond_the_cloud.v5.pdf").is_file())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m unittest tests/test_content.py -v`

Expected: ERROR because the destination bundle does not exist.

- [ ] **Step 3: Copy the source post and referenced PDF**

```bash
mkdir -p content/blog/beyond-the-cloud
cp beyond-the-cloud.md content/blog/beyond-the-cloud/index.en.md
cp writings-images/beyond_the_cloud.v5.pdf content/blog/beyond-the-cloud/beyond_the_cloud.v5.pdf
```

- [ ] **Step 4: Normalize front matter and document structure**

Apply this exact patch to the copied Markdown:

```diff
----
-type: writing
-title: "Beyond the Cloud: A Perceptual Illusion in Overlaid Bar Charts"
-status: published
-created: 2024-05-30
-updated: 2024-05-30
-published_at: 2024-05-30
-tags: ["visualization", "perception", "research"]
-related: []
----
-
-# Beyond the Cloud: A Perceptual Illusion in Overlaid Bar Charts
++++
+title = "Beyond the Cloud: A Perceptual Illusion in Overlaid Bar Charts"
+date = 2024-05-30
+lastmod = 2024-05-30
+draft = false
+tags = ["visualization", "perception", "research"]
+interactionId = "beyond-the-cloud"
++++

 [Wenxuan Zhao](https://jov.arvojournals.org/solr/searchresults.aspx?author=Wenxuan+Zhao); [Karen B. Schloss](https://jov.arvojournals.org/solr/searchresults.aspx?author=Karen+B.+Schloss)

-# Abstract
+## Abstract
@@
-# Poster
-![poster](../../_media/writings-images/beyond_the_cloud.v5.pdf)
+## Poster
+[View or download the poster (PDF, 3.7 MB)](beyond_the_cloud.v5.pdf)
```

- [ ] **Step 5: Run content and ID tests**

Run: `python3 -m unittest tests/test_content.py tests/test_interaction_ids.py -v`

Expected: all tests PASS.

Run: `python3 scripts/validate_interaction_ids.py content`

Expected: `interaction ID validation passed`.

- [ ] **Step 6: Commit the first migrated post if Git was authorized**

```bash
git add content/blog/beyond-the-cloud tests/test_content.py
git commit -m "content: migrate Beyond the Cloud"
```

---

### Task 7: Migrate “Shapes and Functions of the Lekythos”

**Files:**
- Modify: `tests/test_content.py`
- Create: `content/blog/lekythos-a-shape/index.en.md`
- Create: `content/blog/lekythos-a-shape/front.jpeg`
- Create: `content/blog/lekythos-a-shape/detail.jpeg`
- Create: `content/blog/lekythos-a-shape/inner.jpg`
- Create: `layouts/_shortcodes/bundle-image.html`
- Modify: `tests/test_site.py`

- [ ] **Step 1: Add a failing Lekythos migration test**

Add this method to `MigratedContentTests`:

```python
    def test_lekythos_bundle(self):
        post = BLOG / "lekythos-a-shape" / "index.en.md"
        metadata = read_front_matter(post)
        self.assertEqual("Shapes and Functions of the Lekythos", metadata["title"])
        self.assertEqual("lekythos-a-shape", metadata["interactionId"])
        self.assertEqual(["Greek", "Pottery"], metadata["tags"])
        self.assertEqual("2022-11-08", str(metadata["date"]))
        self.assertEqual("2023-11-05", str(metadata["lastmod"]))
        self.assertFalse(metadata["draft"])
        article = body(post)
        self.assertNotIn("\n# Shapes and Functions", article)
        self.assertNotIn("<img", article)
        self.assertIn('src="front.jpeg" alt="Front view of the lekythos beside another vessel" width="400"', article)
        self.assertIn('src="detail.jpeg" alt="Detail of the painted scene" width="400"', article)
        self.assertIn('src="inner.jpg" alt="Interior vessel inside the lekythos" width="200"', article)
        self.assertIn("http://www.beazley.ox.ac.uk", article)
        resources = {path.name for path in post.parent.iterdir() if path.name != "index.en.md"}
        self.assertEqual({"front.jpeg", "detail.jpeg", "inner.jpg"}, resources)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m unittest tests/test_content.py -v`

Expected: ERROR because the Lekythos bundle does not exist.

- [ ] **Step 3: Copy the source post and its three referenced images**

```bash
mkdir -p content/blog/lekythos-a-shape
cp lekythos-a-shape.md content/blog/lekythos-a-shape/index.en.md
cp writings-images/front.jpeg content/blog/lekythos-a-shape/front.jpeg
cp writings-images/detail.jpeg content/blog/lekythos-a-shape/detail.jpeg
cp writings-images/inner.jpg content/blog/lekythos-a-shape/inner.jpg
```

- [ ] **Step 4: Normalize the copied front matter and remove the duplicate title**

```diff
----
-type: writing
-title: "Shapes and Functions of the Lekythos"
-status: published
-created: 2022-11-08
-updated: 2023-11-05
-published_at: 2022-11-08
-tags: ["Greek", "Pottery"]
-related: []
-source: myBlog/posts/lekythos_a_shape
----
-
-# Shapes and Functions of the Lekythos
++++
+title = "Shapes and Functions of the Lekythos"
+date = 2022-11-08
+lastmod = 2023-11-05
+draft = false
+tags = ["Greek", "Pottery"]
+interactionId = "lekythos-a-shape"
++++
```

- [ ] **Step 5: Replace raw images/captions and repair the archived URL**

```diff
-<img src="front.jpeg" alt="front view" width="400"/>
-
-__Front view (note its size from the other lekythos)__
+{{< bundle-image src="front.jpeg" alt="Front view of the lekythos beside another vessel" width="400" >}}

-<img src="detail.jpeg" alt="detailed view" width="400"/>
-
-__A detailed view on the painting__
+{{< bundle-image src="detail.jpeg" alt="Detail of the painted scene" width="400" >}}
@@
-<img src="inner.jpg" alt="the innovation inside" width="200"/>
+{{< bundle-image src="inner.jpg" alt="Interior vessel inside the lekythos" width="200" >}}
@@
-[^45]: Beazley [Archive](https://web.archive.org/web/20161201195122/http:/www.beazley.ox.ac.uk/tools/pottery/shapes/lekythos.htm), Lekythos.
+[^45]: Beazley [Archive](https://web.archive.org/web/20161201195122/http://www.beazley.ox.ac.uk/tools/pottery/shapes/lekythos.htm), Lekythos.
```

The URL substitution occurs inside the existing Wayback Machine URL; preserve the surrounding archive prefix and link text.

- [ ] **Step 6: Add the validated resource-aware width shortcode and rendered-width test**

```html
{{- /* Site-local shortcode; preserves source-authored image widths. */ -}}
{{- $src := strings.TrimSpace (printf "%v" (default "" (.Get "src"))) -}}
{{- $alt := strings.TrimSpace (printf "%v" (default "" (.Get "alt"))) -}}
{{- $width := strings.TrimSpace (printf "%v" (default "" (.Get "width"))) -}}
{{- $resource := .Page.Resources.Get $src -}}
{{- $validWidth := gt (len (findRE `^[1-9][0-9]*$` $width)) 0 -}}
{{- if not $resource -}}
  {{- errorf "%s: bundle-image resource %q was not found" .Page.File.Path $src -}}
{{- end -}}
{{- if not $alt -}}
  {{- errorf "%s: bundle-image %q requires nonempty alt text" .Page.File.Path $src -}}
{{- end -}}
{{- if not $validWidth -}}
  {{- errorf "%s: bundle-image %q width must be a positive integer" .Page.File.Path $src -}}
{{- end -}}
{{- if and $resource $alt $validWidth -}}
{{- $controlId := printf "img-%s" (substr (md5 (printf "%s-%s" .Page.RelPermalink $src)) 0 8) -}}
<figure class="image-caption{{ if .Page.Site.Params.imageZoom }} image-zoom-container{{ end }}">
  {{ if .Page.Site.Params.imageZoom }}
    <input type="checkbox" id="{{ $controlId }}" class="image-zoom-toggle" aria-label="{{ T "zoomImage" $alt }}">
    <label for="{{ $controlId }}" class="image-zoom-label">
      <img src="{{ $resource.RelPermalink }}" alt="{{ $alt }}" width="{{ $width }}" loading="lazy" class="zoomable-image">
    </label>
    <label for="{{ $controlId }}" class="image-zoom-overlay" aria-hidden="true">
      <img src="{{ $resource.RelPermalink }}" alt="" width="{{ $width }}" class="zoomable-image">
    </label>
  {{ else }}
    <img src="{{ $resource.RelPermalink }}" alt="{{ $alt }}" width="{{ $width }}" loading="lazy">
  {{ end }}
  <figcaption>{{ $alt }}</figcaption>
</figure>
{{- end -}}
```

Add this method to `GeneratedSiteTests` in `tests/test_site.py`:

```python
    def test_lekythos_preserves_resource_urls_and_authored_widths(self):
        with TemporaryDirectory() as temporary:
            public = Path(temporary) / "public"
            build_site(public, "https://example.test/")
            html = read_html(public, "p/lekythos-a-shape/index.html")
            for filename, width in {
                "front.jpeg": "400",
                "detail.jpeg": "400",
                "inner.jpg": "200",
            }.items():
                image = re.compile(
                    rf'<img(?=[^>]*src="/p/lekythos-a-shape/{re.escape(filename)}")'
                    rf'(?=[^>]*width="{width}")[^>]*>'
                )
                self.assertRegex(html, image)
```

- [ ] **Step 7: Run content, rendered-width, footnote, and ID validation**

Run: `python3 -m unittest tests/test_content.py tests/test_interaction_ids.py tests/test_site.py -v`

Expected: all tests PASS, including the exact three-resource inventory and the rendered 400/400/200 widths.

Run: `python3 scripts/validate_interaction_ids.py content`

Expected: `interaction ID validation passed`.

- [ ] **Step 8: Commit the Lekythos migration if Git was authorized**

```bash
git add content/blog/lekythos-a-shape layouts/_shortcodes/bundle-image.html tests/test_content.py tests/test_site.py
git commit -m "content: migrate Lekythos essay"
```

---

### Task 8: Migrate “The Miracle of Istanbul” and its 21 resources

**Files:**
- Modify: `tests/test_content.py`
- Create: `content/blog/the-miracle-of-istanbul/index.en.md`
- Create: `content/blog/the-miracle-of-istanbul/2021-03-04-The-Miracle-of-Istanbul.Rmd`
- Create: `content/blog/the-miracle-of-istanbul/timeline.png`
- Create: `content/blog/the-miracle-of-istanbul/unnamed-chunk-3-1.png`
- Create: `content/blog/the-miracle-of-istanbul/unnamed-chunk-3-2.png`
- Create: `content/blog/the-miracle-of-istanbul/unnamed-chunk-9-1.png`
- Create: `content/blog/the-miracle-of-istanbul/unnamed-chunk-10-1.png`
- Create: `content/blog/the-miracle-of-istanbul/unnamed-chunk-11-1.png`
- Create: `content/blog/the-miracle-of-istanbul/unnamed-chunk-12-1.png`
- Create: `content/blog/the-miracle-of-istanbul/unnamed-chunk-12-2.png`
- Create: `content/blog/the-miracle-of-istanbul/unnamed-chunk-12-3.png`
- Create: `content/blog/the-miracle-of-istanbul/unnamed-chunk-12-4.png`
- Create: `content/blog/the-miracle-of-istanbul/unnamed-chunk-13-1.png`
- Create: `content/blog/the-miracle-of-istanbul/unnamed-chunk-13-2.png`
- Create: `content/blog/the-miracle-of-istanbul/unnamed-chunk-13-3.png`
- Create: `content/blog/the-miracle-of-istanbul/unnamed-chunk-13-4.png`
- Create: `content/blog/the-miracle-of-istanbul/unnamed-chunk-14-1.png`
- Create: `content/blog/the-miracle-of-istanbul/unnamed-chunk-14-2.png`
- Create: `content/blog/the-miracle-of-istanbul/unnamed-chunk-15-1.png`
- Create: `content/blog/the-miracle-of-istanbul/unnamed-chunk-15-2.png`
- Create: `content/blog/the-miracle-of-istanbul/unnamed-chunk-16-1.png`
- Create: `content/blog/the-miracle-of-istanbul/unnamed-chunk-16-2.png`

- [ ] **Step 1: Add a failing Istanbul migration test**

Add constants and this method to `tests/test_content.py`:

```python
ISTANBUL_RESOURCES = {
    "2021-03-04-The-Miracle-of-Istanbul.Rmd",
    "timeline.png",
    "unnamed-chunk-3-1.png", "unnamed-chunk-3-2.png",
    "unnamed-chunk-9-1.png", "unnamed-chunk-10-1.png", "unnamed-chunk-11-1.png",
    "unnamed-chunk-12-1.png", "unnamed-chunk-12-2.png",
    "unnamed-chunk-12-3.png", "unnamed-chunk-12-4.png",
    "unnamed-chunk-13-1.png", "unnamed-chunk-13-2.png",
    "unnamed-chunk-13-3.png", "unnamed-chunk-13-4.png",
    "unnamed-chunk-14-1.png", "unnamed-chunk-14-2.png",
    "unnamed-chunk-15-1.png", "unnamed-chunk-15-2.png",
    "unnamed-chunk-16-1.png", "unnamed-chunk-16-2.png",
}


    def test_istanbul_bundle(self):
        post = BLOG / "the-miracle-of-istanbul" / "index.en.md"
        metadata = read_front_matter(post)
        self.assertEqual("The Miracle of Istanbul", metadata["title"])
        self.assertEqual("the-miracle-of-istanbul", metadata["interactionId"])
        self.assertEqual(["football", "data visualization", "r"], metadata["tags"])
        self.assertEqual("2021-03-04", str(metadata["date"]))
        self.assertEqual("2023-11-05", str(metadata["lastmod"]))
        self.assertFalse(metadata["draft"])
        article = body(post)
        self.assertNotIn("\n# The Miracle of Istanbul", article)
        self.assertNotIn("../../_media", article)
        self.assertNotIn("<!-- -->", article)
        self.assertNotIn("![](", article)
        self.assertIn(
            "[Download the R Markdown source](2021-03-04-The-Miracle-of-Istanbul.Rmd)",
            article,
        )
        resources = {path.name for path in post.parent.iterdir() if path.name != "index.en.md"}
        self.assertEqual(ISTANBUL_RESOURCES, resources)
        self.assertNotIn("cover.png", resources)
        self.assertNotIn("3-3.jpeg", resources)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m unittest tests/test_content.py -v`

Expected: ERROR because the Istanbul bundle does not exist.

- [ ] **Step 3: Copy the authoritative Markdown, archival Rmd, and every referenced image**

```bash
mkdir -p content/blog/the-miracle-of-istanbul
cp the-miracle-of-istanbul.md content/blog/the-miracle-of-istanbul/index.en.md
cp writings-images/2021-03-04-The-Miracle-of-Istanbul.Rmd content/blog/the-miracle-of-istanbul/2021-03-04-The-Miracle-of-Istanbul.Rmd
cp writings-images/timeline.png content/blog/the-miracle-of-istanbul/timeline.png
cp writings-images/unnamed-chunk-3-1.png content/blog/the-miracle-of-istanbul/unnamed-chunk-3-1.png
cp writings-images/unnamed-chunk-3-2.png content/blog/the-miracle-of-istanbul/unnamed-chunk-3-2.png
cp writings-images/unnamed-chunk-9-1.png content/blog/the-miracle-of-istanbul/unnamed-chunk-9-1.png
cp writings-images/unnamed-chunk-10-1.png content/blog/the-miracle-of-istanbul/unnamed-chunk-10-1.png
cp writings-images/unnamed-chunk-11-1.png content/blog/the-miracle-of-istanbul/unnamed-chunk-11-1.png
cp writings-images/unnamed-chunk-12-1.png content/blog/the-miracle-of-istanbul/unnamed-chunk-12-1.png
cp writings-images/unnamed-chunk-12-2.png content/blog/the-miracle-of-istanbul/unnamed-chunk-12-2.png
cp writings-images/unnamed-chunk-12-3.png content/blog/the-miracle-of-istanbul/unnamed-chunk-12-3.png
cp writings-images/unnamed-chunk-12-4.png content/blog/the-miracle-of-istanbul/unnamed-chunk-12-4.png
cp writings-images/unnamed-chunk-13-1.png content/blog/the-miracle-of-istanbul/unnamed-chunk-13-1.png
cp writings-images/unnamed-chunk-13-2.png content/blog/the-miracle-of-istanbul/unnamed-chunk-13-2.png
cp writings-images/unnamed-chunk-13-3.png content/blog/the-miracle-of-istanbul/unnamed-chunk-13-3.png
cp writings-images/unnamed-chunk-13-4.png content/blog/the-miracle-of-istanbul/unnamed-chunk-13-4.png
cp writings-images/unnamed-chunk-14-1.png content/blog/the-miracle-of-istanbul/unnamed-chunk-14-1.png
cp writings-images/unnamed-chunk-14-2.png content/blog/the-miracle-of-istanbul/unnamed-chunk-14-2.png
cp writings-images/unnamed-chunk-15-1.png content/blog/the-miracle-of-istanbul/unnamed-chunk-15-1.png
cp writings-images/unnamed-chunk-15-2.png content/blog/the-miracle-of-istanbul/unnamed-chunk-15-2.png
cp writings-images/unnamed-chunk-16-1.png content/blog/the-miracle-of-istanbul/unnamed-chunk-16-1.png
cp writings-images/unnamed-chunk-16-2.png content/blog/the-miracle-of-istanbul/unnamed-chunk-16-2.png
```

Do not copy `writings-images/cover.png`, `writings-images/3-3.jpeg`, or `.DS_Store`.

- [ ] **Step 4: Normalize front matter and remove only the body title H1**

```diff
----
-type: writing
-title: "The Miracle of Istanbul"
-status: published
-created: 2021-03-04
-updated: 2023-11-05
-published_at: 2021-03-04
-tags: ["football", "data visualization", "r"]
-related: []
-source: myBlog/posts/the-miracle-of-istanbul
----
-
-# The Miracle of Istanbul
++++
+title = "The Miracle of Istanbul"
+date = 2021-03-04
+lastmod = 2023-11-05
+draft = false
+tags = ["football", "data visualization", "r"]
+interactionId = "the-miracle-of-istanbul"
++++
```

Do not remove lines beginning with `#` inside fenced R code blocks; they are code comments.

- [ ] **Step 5: Rewrite the bundle paths and remove empty knitr comments mechanically**

Run this bulk rewrite only on the copied destination file:

```bash
perl -0pi -e 's#\.\./\.\./_media/writings-images/##g; s/<!-- -->//g' content/blog/the-miracle-of-istanbul/index.en.md
```

- [ ] **Step 6: Give all 20 images meaningful alternative text and repair the source link**

Apply these exact replacements to `content/blog/the-miracle-of-istanbul/index.en.md`:

```diff
-![](unnamed-chunk-3-1.png)
+![Starting-eleven market values for AC Milan and Liverpool](unnamed-chunk-3-1.png)
-![](unnamed-chunk-3-2.png)
+![Ten highest-valued players across both starting elevens](unnamed-chunk-3-2.png)
-![](timeline.png)
+![Timeline of the 2005 Champions League final](timeline.png)
-![](unnamed-chunk-9-1.png)
+![First-half shot map for AC Milan and Liverpool](unnamed-chunk-9-1.png)
-![](unnamed-chunk-10-1.png)
+![Second-half shot map for Liverpool and AC Milan](unnamed-chunk-10-1.png)
-![](unnamed-chunk-11-1.png)
+![Extra-time shot map for Liverpool and AC Milan](unnamed-chunk-11-1.png)
-![](unnamed-chunk-12-1.png)
+![Picture 1: AC Milan passing map for minutes 1 through 24](unnamed-chunk-12-1.png)
-![](unnamed-chunk-12-2.png)
+![Picture 2: AC Milan passing map after minute 24](unnamed-chunk-12-2.png)
-![](unnamed-chunk-12-3.png)
+![Picture 3: Liverpool passing map for minutes 1 through 24](unnamed-chunk-12-3.png)
-![](unnamed-chunk-12-4.png)
+![Picture 4: Liverpool passing map after minute 24](unnamed-chunk-12-4.png)
-![](unnamed-chunk-13-1.png)
+![Picture 1: AC Milan passing network during the six-minute spell](unnamed-chunk-13-1.png)
-![](unnamed-chunk-13-2.png)
+![Picture 2: AC Milan individual passes during the six-minute spell](unnamed-chunk-13-2.png)
-![](unnamed-chunk-13-3.png)
+![Picture 3: Liverpool passing network during the six-minute spell](unnamed-chunk-13-3.png)
-![](unnamed-chunk-13-4.png)
+![Picture 4: Liverpool individual passes during the six-minute spell](unnamed-chunk-13-4.png)
-![](unnamed-chunk-14-1.png)
+![Picture 1: Liverpool defensive actions during the six-minute spell](unnamed-chunk-14-1.png)
-![](unnamed-chunk-14-2.png)
+![Picture 2: AC Milan defensive actions during the six-minute spell](unnamed-chunk-14-2.png)
-![](unnamed-chunk-15-1.png)
+![Picture 1: AC Milan average first-half positions](unnamed-chunk-15-1.png)
-![](unnamed-chunk-15-2.png)
+![Picture 2: Liverpool average first-half positions](unnamed-chunk-15-2.png)
-![](unnamed-chunk-16-1.png)
+![Picture 1: AC Milan average early second-half positions](unnamed-chunk-16-1.png)
-![](unnamed-chunk-16-2.png)
+![Picture 2: Liverpool average early second-half positions](unnamed-chunk-16-2.png)
@@
-- [code](2021-03-04-The-Miracle-of-Istanbul.Rmd)
+- [Download the R Markdown source](2021-03-04-The-Miracle-of-Istanbul.Rmd)
```

- [ ] **Step 7: Run content, ID, and production-build tests**

Run: `python3 -m unittest tests/test_content.py tests/test_interaction_ids.py tests/test_site.py -v`

Expected: all tests PASS.

Run: `python3 scripts/validate_interaction_ids.py content`

Expected: `interaction ID validation passed`.

Run: `hugo --gc --minify --panicOnWarning`

Expected: exit 0 and all three English posts render under `/p/<slug>/`.

- [ ] **Step 8: Commit the Istanbul migration if Git was authorized**

```bash
git add content/blog/the-miracle-of-istanbul tests/test_content.py
git commit -m "content: migrate Miracle of Istanbul"
```

---

### Task 9: Generate one localized RSS feed per language

**Files:**
- Create: `layouts/home.rss.xml`
- Create: `tests/fixtures/rss-limit.toml`
- Modify: `tests/test_site.py`

- [ ] **Step 1: Add a failing language-feed test**

Add the import and test method to `tests/test_site.py`:

```python
import xml.etree.ElementTree as ET
import tomllib


    def test_rss_is_separate_and_localized(self):
        configuration = tomllib.loads((ROOT / "hugo.toml").read_text())
        self.assertEqual(10, configuration["services"]["rss"]["limit"])
        with TemporaryDirectory() as temporary:
            public = Path(temporary) / "public"
            build_site(public, "https://example.test/")
            english = ET.parse(public / "index.xml").getroot().find("channel")
            chinese = ET.parse(public / "zh/index.xml").getroot().find("channel")
            self.assertIsNotNone(english)
            self.assertIsNotNone(chinese)
            self.assertEqual("en-US", english.findtext("language"))
            self.assertEqual("zh-CN", chinese.findtext("language"))
            english_titles = {item.findtext("title") for item in english.findall("item")}
            self.assertEqual(
                {
                    "Beyond the Cloud: A Perceptual Illusion in Overlaid Bar Charts",
                    "Shapes and Functions of the Lekythos",
                    "The Miracle of Istanbul",
                },
                english_titles,
            )
            self.assertEqual([], chinese.findall("item"))
            self.assertIn("Recent posts from Wenxuan Zhao", english.findtext("description"))
            self.assertIn("赵文轩的最新文章", chinese.findtext("description"))
            self.assertIn("30 May 2024", english.findtext("lastBuildDate"))
            zh_home = read_html(public, "zh/index.html")
            self.assertIn('href="https://example.test/zh/index.xml"', zh_home)
            self.assertIn('href="/zh/index.xml"', zh_home)

            limited = Path(temporary) / "limited"
            build_site(
                limited,
                "https://example.test/",
                "--config", "hugo.toml,tests/fixtures/rss-limit.toml",
            )
            limited_channel = ET.parse(limited / "index.xml").getroot().find("channel")
            self.assertEqual(2, len(limited_channel.findall("item")))
```

Create `tests/fixtures/rss-limit.toml`:

```toml
[services.rss]
  limit = 2
```

- [ ] **Step 2: Run the feed test to verify it fails**

Run: `python3 -m unittest tests/test_site.py -v`

Expected: FAIL because the upstream RSS description is hardcoded in English and is not constrained explicitly to blog pages.

- [ ] **Step 3: Implement the localized, blog-only home feed**

```xml
{{- /* Derived from rokcso/hugo-bearneo@f5c57c5ea39a091f0167af6312f4d4e385df2e6c: layouts/_default/rss.xml */ -}}
{{- $pages := where .Site.RegularPages "Section" "blog" -}}
{{- $pages = where $pages "Params.hidden" "ne" true -}}
{{- $pages = $pages.ByPublishDate.Reverse -}}
{{- $limit := .Site.Config.Services.RSS.Limit -}}
{{- if ge $limit 1 -}}
  {{- $pages = first $limit $pages -}}
{{- end -}}
{{- $updated := $pages.ByLastmod.Reverse -}}
{{- printf "<?xml version=\"1.0\" encoding=\"utf-8\" standalone=\"yes\"?>" | safeHTML }}
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{{ .Site.Title }}</title>
    <link>{{ .Site.Home.Permalink }}</link>
    <description>{{ T "rssDescription" .Site.Title }}</description>
    <generator>Hugo</generator>
    <language>{{ .Language.Locale }}</language>
    {{ with $updated }}<lastBuildDate>{{ (index . 0).Lastmod.Format "Mon, 02 Jan 2006 15:04:05 -0700" | safeHTML }}</lastBuildDate>{{ end }}
    {{ with .OutputFormats.Get "RSS" }}<atom:link href="{{ .Permalink }}" rel="self" type="{{ .MediaType.Type }}" />{{ end }}
    {{ range $pages }}
      <item>
        <title>{{ .Title }}</title>
        <link>{{ .Permalink }}</link>
        <pubDate>{{ .PublishDate.Format "Mon, 02 Jan 2006 15:04:05 -0700" | safeHTML }}</pubDate>
        <guid isPermaLink="true">{{ .Permalink }}</guid>
        <description>{{ .Summary | plainify | transform.HTMLUnescape | transform.XMLEscape | safeHTML }}</description>
      </item>
    {{ end }}
  </channel>
</rss>
```

- [ ] **Step 4: Run feed and full site tests**

Run: `python3 -m unittest tests/test_site.py -v`

Expected: all tests PASS; English has three items and Chinese has zero. Ordered-limit coverage proves hidden posts are excluded before sorting/limiting, and entity-rich summaries are HTML-unescaped and XML-escaped exactly once.

- [ ] **Step 5: Commit RSS if Git was authorized**

```bash
git add layouts/home.rss.xml tests/fixtures/rss-limit.toml tests/test_site.py
git commit -m "feat: add separate localized RSS feeds"
```

---

### Task 10: Emit real-only SEO alternates and multilingual sitemap entries

**Files:**
- Create: `layouts/_partials/seo_tags.html`
- Create: `layouts/sitemap.xml`
- Create: `tests/fixtures/content/blog/shared-article/index.en.md`
- Create: `tests/fixtures/content/blog/shared-article/index.zh.md`
- Create: `tests/fixtures/content/blog/shared-article/diagram.svg`
- Create: `tests/fixtures/content/blog/shared-article/notes.txt`
- Create: `tests/fixtures/content/blog/chinese-only/index.zh.md`
- Create: `tests/fixtures/interactions.toml`
- Modify: `tests/test_site.py`

- [ ] **Step 1: Create non-production translation fixtures**

```toml
+++
title = "Shared article"
date = 2026-08-08
lastmod = 2026-08-08
draft = false
tags = ["fixture", "same-spelling"]
interactionId = "shared-article"
+++

## Fixture

English fixture content.

![Shared fixture diagram](diagram.svg)

[Download shared fixture notes](notes.txt)
```

Save as `tests/fixtures/content/blog/shared-article/index.en.md`.

```toml
+++
title = "共享文章"
date = 2026-08-08
lastmod = 2026-08-08
draft = false
tags = ["测试"]
interactionId = "shared-article"
+++

## 测试

中文测试内容。

![共享测试图](diagram.svg)

[下载共享测试说明](notes.txt)
```

Save as `tests/fixtures/content/blog/shared-article/index.zh.md`.

```toml
+++
title = "仅中文文章"
date = 2026-08-08
lastmod = 2026-08-08
draft = false
tags = ["测试", "same-spelling"]
interactionId = "chinese-only"
+++

天地玄黄宇宙洪荒日月盈

昃辰宿列张寒来暑往秋收冬藏尾标
```

Save as `tests/fixtures/content/blog/chinese-only/index.zh.md`.

The first paragraph intentionally contains 11 CJK characters while the whole body remains exactly 26. With `summaryLength = 10`, Hugo 0.164 stops an automatic CJK summary at the first paragraph boundary only after the boundary exceeds the configured length; a boundary of exactly ten characters includes the following punctuation-free paragraph.

Create the two shared fixture resources:

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32" role="img" aria-label="Fixture square">
  <rect width="32" height="32" fill="#4b6b88"/>
</svg>
```

Save as `tests/fixtures/content/blog/shared-article/diagram.svg`. Save the UTF-8 text `Shared multilingual fixture resource.` followed by a newline as `tests/fixtures/content/blog/shared-article/notes.txt`.

Create `tests/fixtures/interactions.toml` with non-secret fixture values:

```toml
summaryLength = 10

[params.giscus]
  enabled = true
  repo = "fixture-owner/fixture-repository"
  repoId = "R_fixture"
  category = "Fixture category"
  categoryId = "DIC_fixture"

[params.kudos]
  enabled = true
  endpoint = "http://127.0.0.1:4174"
```

- [ ] **Step 2: Add failing SEO fixture tests**

Add these helpers and test method to `tests/test_site.py`:

```python
def alternate_link_entries(html: str) -> list[tuple[str, str]]:
    return re.findall(
        r'<link[^>]+rel="alternate"[^>]+hreflang="([^"]+)"[^>]+href="([^"]+)"',
        html,
    )


def alternate_links(html: str) -> set[tuple[str, str]]:
    return set(alternate_link_entries(html))


    def test_seo_uses_only_real_translations(self):
        with TemporaryDirectory() as temporary:
            public = Path(temporary) / "public"
            build_site(public, "https://example.test/")
            unpaired = read_html(public, "p/beyond-the-cloud/index.html")
            self.assertEqual(set(), alternate_links(unpaired))

            fixture = Path(temporary) / "fixture"
            build_site(
                fixture,
                "https://example.test/",
                "--config", "hugo.toml,tests/fixtures/interactions.toml",
                "--contentDir", "tests/fixtures/content",
            )
            english = read_html(fixture, "p/shared-article/index.html")
            chinese = read_html(fixture, "zh/p/shared-article/index.html")
            english_posts = read_html(fixture, "blog/index.html")
            chinese_posts = read_html(fixture, "zh/blog/index.html")
            self.assertIn('<p data-post-count>1 post</p>', english_posts)
            self.assertIn('data-count-one="{count} post"', english_posts)
            self.assertIn('data-count-many="{count} posts"', english_posts)
            self.assertIn('<p data-post-count>2 篇文章</p>', chinese_posts)
            self.assertIn('data-count-one="{count} 篇文章"', chinese_posts)
            self.assertIn('data-count-many="{count} 篇文章"', chinese_posts)
            expected = {
                ("en-US", "https://example.test/p/shared-article/"),
                ("zh-CN", "https://example.test/zh/p/shared-article/"),
                ("x-default", "https://example.test/p/shared-article/"),
            }
            self.assertEqual(expected, alternate_links(english))
            self.assertEqual(expected, alternate_links(chinese))
            self.assertIn('class="language-switcher"', english)
            self.assertIn('href="/zh/p/shared-article/"', english)
            self.assertIn('href="/p/shared-article/"', chinese)
            for html in [english, chinese]:
                self.assertIn('src="/p/shared-article/diagram.svg"', html)
                self.assertIn('href="/p/shared-article/notes.txt"', html)
            self.assertTrue((fixture / "p/shared-article/diagram.svg").is_file())
            self.assertTrue((fixture / "p/shared-article/notes.txt").is_file())
            chinese_only = read_html(fixture, "zh/p/chinese-only/index.html")
            self.assertEqual(set(), alternate_links(chinese_only))
            self.assertIn('<link rel="canonical" href="https://example.test/zh/p/chinese-only/">', chinese_only)
            word_count = re.search(r'data-word-count="(\d+)"', chinese_only)
            self.assertIsNotNone(word_count)
            self.assertEqual(26, int(word_count.group(1)))
            description = re.search(r'<meta name="description" content="([^"]*)"', chinese_only)
            self.assertIsNotNone(description)
            self.assertEqual("天地玄黄宇宙洪荒日月盈", description.group(1).strip())
            self.assertNotIn("尾标", description.group(1))
            english_tags = read_html(fixture, "tags/index.html")
            chinese_tags = read_html(fixture, "zh/tags/index.html")
            self.assertIn("#fixture", english_tags)
            self.assertNotIn("#测试", english_tags)
            self.assertIn("#测试", chinese_tags)
            self.assertNotIn("#fixture", chinese_tags)
            self.assertIn('href="/zh/tags/%E6%B5%8B%E8%AF%95/"', chinese_tags)
            self.assertTrue((fixture / "zh/tags/测试/index.html").is_file())
            chinese_term = read_html(fixture, "zh/tags/测试/index.html")
            self.assertIn("共享文章", chinese_term)
            self.assertIn("仅中文文章", chinese_term)
            self.assertNotIn("Shared article", chinese_term)
            english_same_term = read_html(fixture, "tags/same-spelling/index.html")
            chinese_same_term = read_html(fixture, "zh/tags/same-spelling/index.html")
            for term_html in [english_same_term, chinese_same_term]:
                self.assertNotIn('class="language-switcher"', term_html)
                self.assertEqual(set(), alternate_links(term_html))
            self.assertIn("Shared article", english_same_term)
            self.assertNotIn("仅中文文章", english_same_term)
            self.assertIn("仅中文文章", chinese_same_term)
            self.assertNotIn("Shared article", chinese_same_term)
            sitemap_index = ET.parse(fixture / "sitemap.xml").getroot()
            locations = {node.text for node in sitemap_index.findall("{*}sitemap/{*}loc")}
            self.assertEqual(
                {"https://example.test/en/sitemap.xml", "https://example.test/zh/sitemap.xml"},
                locations,
            )
            english_sitemap = ET.parse(fixture / "en/sitemap.xml").getroot()
            shared_entry = next(
                node for node in english_sitemap.findall("{*}url")
                if node.findtext("{*}loc") == "https://example.test/p/shared-article/"
            )
            sitemap_alternates = {
                (link.attrib["hreflang"], link.attrib["href"])
                for link in shared_entry.findall("{http://www.w3.org/1999/xhtml}link")
            }
            self.assertEqual(expected, sitemap_alternates)
            chinese_sitemap = ET.parse(fixture / "zh/sitemap.xml").getroot()
            for sitemap, location in [
                (english_sitemap, "https://example.test/tags/same-spelling/"),
                (chinese_sitemap, "https://example.test/zh/tags/same-spelling/"),
            ]:
                term_entry = next(
                    node for node in sitemap.findall("{*}url")
                    if node.findtext("{*}loc") == location
                )
                self.assertEqual(
                    [],
                    term_entry.findall("{http://www.w3.org/1999/xhtml}link"),
                )

            project = Path(temporary) / "project"
            build_site(
                project,
                "https://example.test/example-blog/",
                "--config", "hugo.toml,tests/fixtures/interactions.toml",
                "--contentDir", "tests/fixtures/content",
            )
            project_chinese = read_html(project, "zh/p/shared-article/index.html")
            self.assertIn('src="/example-blog/p/shared-article/diagram.svg"', project_chinese)
            self.assertIn('href="/example-blog/p/shared-article/notes.txt"', project_chinese)
            self.assertTrue((project / "zh/tags/测试/index.html").is_file())
```

The final test also parses the standard, Open Graph, Twitter, and schema description elements and requires one equal, entity-correct value containing Beyond's abstract prose. It asserts exactly three non-duplicated alternates for each translated page and sitemap entry, inspects both project-site child sitemaps, proves a visible page does not advertise or switch to a `hidden = true` translation, and proves a term backed only by hidden posts is absent while home, section, and taxonomy entries remain. Inspect the generated hidden translation itself as well: it must emit exactly one `<meta name="robots" content="noindex">` and no canonical or `hreflang` link, while its visible counterpart retains its canonical and has no `noindex` directive.

- [ ] **Step 3: Run the SEO test to verify it fails**

Run: `python3 -m unittest tests/test_site.py -v`

Expected: FAIL because Bear Neo emits canonical metadata but no reciprocal `hreflang` or `x-default` links.

- [ ] **Step 4: Implement canonical and alternate metadata**

```html
{{- /* Derived from rokcso/hugo-bearneo@f5c57c5ea39a091f0167af6312f4d4e385df2e6c: layouts/partials/seo_tags.html */ -}}
{{- $description := .Site.Params.description -}}
{{- with .Description -}}
  {{- $description = . -}}
{{- else -}}
  {{- if .IsPage -}}
    {{- $description = .Summary | plainify | transform.HTMLUnescape | strings.TrimSpace -}}
  {{- end -}}
{{- end -}}
<meta name="title" content="{{ with .Title }}{{ . }}{{ else }}{{ .Site.Title }}{{ end }}">
<meta name="description" content="{{ $description }}">
{{ with .Params.tags }}<meta name="keywords" content="{{ delimit . "," }}">{{ end }}
{{ if .Params.hidden }}
  <meta name="robots" content="noindex">
{{ else }}
  <link rel="canonical" href="{{ .Permalink }}">
  {{ $visibleTranslations := where .AllTranslations "Params.hidden" "ne" true }}
  {{ if and (ge (len $visibleTranslations) 2) (ne .Kind "term") }}
    {{ range $visibleTranslations }}<link rel="alternate" hreflang="{{ .Language.Locale }}" href="{{ .Permalink }}">{{ end }}
    {{ range where $visibleTranslations "Language.Name" "en" }}<link rel="alternate" hreflang="x-default" href="{{ .Permalink }}">{{ end }}
  {{ end }}
{{ end }}
{{ partial "opengraph.html" . }}
{{ partial "twitter_cards.html" . }}
{{ partial "schema.html" . }}
```

- [ ] **Step 5: Extend the per-language sitemap with the same real translation set**

```xml
{{- /* Site-local multilingual sitemap template. */ -}}
{{- printf "<?xml version=\"1.0\" encoding=\"utf-8\" standalone=\"yes\"?>" | safeHTML }}
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">
  {{ $pages := where .Pages "Params.hidden" "ne" true }}
  {{ range $pages }}
    {{ $includePage := true }}
    {{ if eq .Kind "term" }}
      {{ $includePage = gt (len (where .Pages "Params.hidden" "ne" true)) 0 }}
    {{ end }}
    {{ if $includePage }}
      <url>
        <loc>{{ .Permalink }}</loc>
        {{ if not .Lastmod.IsZero }}<lastmod>{{ .Lastmod.Format "2006-01-02T15:04:05-07:00" | safeHTML }}</lastmod>{{ end }}
        {{ $visibleTranslations := where .AllTranslations "Params.hidden" "ne" true }}
        {{ if and (ge (len $visibleTranslations) 2) (ne .Kind "term") }}
          {{ range $visibleTranslations }}<xhtml:link rel="alternate" hreflang="{{ .Language.Locale }}" href="{{ .Permalink }}" />{{ end }}
          {{ range where $visibleTranslations "Language.Name" "en" }}<xhtml:link rel="alternate" hreflang="x-default" href="{{ .Permalink }}" />{{ end }}
        {{ end }}
      </url>
    {{ end }}
  {{ end }}
</urlset>
```

Leave Hugo's built-in root sitemap-index renderer in place; this template handles each per-language sitemap.

- [ ] **Step 6: Run SEO, sitemap, RSS, and production tests**

Run: `python3 -m unittest tests/test_site.py -v`

Expected: all tests PASS; unpaired visible pages have canonical only, the visible fixture pair has reciprocal alternates and English `x-default`, and a hidden generated page has one `robots` `noindex` directive with no canonical or alternate links.

- [ ] **Step 7: Commit SEO and fixtures if Git was authorized**

```bash
git add layouts/_partials/header.html layouts/_partials/seo_tags.html layouts/sitemap.xml tests/fixtures tests/test_site.py docs/superpowers/plans/2026-08-08-bearneo-multilingual-blog.md
git commit -m "feat: add multilingual SEO metadata"
```

---

### Task 11: Add shared-thread Giscus comments with graceful configuration failure

**Files:**
- Create: `layouts/_partials/interaction-id.html`
- Create: `layouts/_partials/giscus.html`
- Create: `tests/fixtures/incomplete-interactions.toml`
- Create: `tests/fixtures/invalid-content/blog/invalid-id/index.en.md`
- Create: `tests/fixtures/nonstring-content/blog/nonstring-id/index.en.md`
- Create: `tests/fixtures/overlong-content/blog/overlong-id/index.en.md`
- Create: `tests/fixtures/mismatched-content/blog/shared/index.en.md`
- Create: `tests/fixtures/mismatched-content/blog/shared/index.zh.md`
- Create: `tests/fixtures/missing-id-content/blog/missing/index.en.md`
- Create: `tests/fixtures/site-id.toml`
- Create: `tests/fixtures/language-id.toml`
- Create: `tests/fixtures/invalid-giscus-repo.toml`
- Create: `tests/fixtures/invalid-giscus-whitespace.toml`
- Create: `tests/fixtures/invalid-giscus-enabled.toml`
- Create: `tests/fixtures/invalid-giscus-types.toml`
- Create: `tests/fixtures/invalid-giscus-container-scalar.toml`
- Create: `tests/fixtures/invalid-giscus-container-list.toml`
- Create: `tests/fixtures/padded-giscus.toml`
- Modify: `layouts/blog/page.html`
- Modify: `tests/test_site.py`

- [ ] **Step 1: Add incomplete and invalid-ID fixtures**

```toml
# tests/fixtures/incomplete-interactions.toml
[params.giscus]
  enabled = true
  repo = "fixture-owner/fixture-repository"
  repoId = ""
  category = "Fixture category"
  categoryId = "DIC_fixture"

[params.kudos]
  enabled = true
  endpoint = ""
```

```toml
+++
title = "Invalid identity fixture"
date = 2026-08-08
lastmod = 2026-08-08
draft = false
tags = ["fixture"]
interactionId = "Invalid ID"
+++

## Fixture

This page proves that a direct Hugo build fails even when the command-line validator is bypassed.
```

Save the second block as `tests/fixtures/invalid-content/blog/invalid-id/index.en.md`.

Save this as `tests/fixtures/nonstring-content/blog/nonstring-id/index.en.md`:

```toml
+++
title = "Non-string identity fixture"
date = 2026-08-08
draft = false
interactionId = 42
+++

## Fixture
```

Save this as `tests/fixtures/overlong-content/blog/overlong-id/index.en.md`; its ID is exactly 81 ASCII characters:

```toml
+++
title = "Overlong identity fixture"
date = 2026-08-08
draft = false
interactionId = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
+++

## Fixture
```

Create a mismatched translation fixture. Save this as `tests/fixtures/mismatched-content/blog/shared/index.en.md`:

```toml
+++
title = "Mismatched English fixture"
date = 2026-08-08
draft = false
interactionId = "english-identity"
+++

## Fixture
```

Save the same content with `title = "不匹配的中文测试"` and `interactionId = "chinese-identity"` as `tests/fixtures/mismatched-content/blog/shared/index.zh.md`.

Save this as `tests/fixtures/missing-id-content/blog/missing/index.en.md`:

```toml
+++
title = "Missing identity fixture"
date = 2026-08-08
draft = false
+++

## Fixture
```

Create `tests/fixtures/site-id.toml` to prove that Hugo's site-parameter fallback cannot satisfy page-local front matter:

```toml
[params]
  interactionId = "site-fallback-must-not-count"
```

Create the equivalent `tests/fixtures/language-id.toml` beneath `languages.en.params` to prove that a language-level fallback also cannot satisfy page-local front matter.

Create invalid optional-integration field fixtures:

```toml
# tests/fixtures/invalid-giscus-repo.toml
[params.giscus]
  enabled = true
  repo = "not-a-repository"
  repoId = "R_fixture"
  category = "Fixture category"
  categoryId = "DIC_fixture"
```

Also create scalar and list `params.giscus` container fixtures. Both must build without a warning or widget. Create `padded-giscus.toml` with surrounding whitespace around every required string and invalid free-form `giscusLanguage` values; the rendered values must be trimmed and the interface locale must still derive from the page language.

```toml
# tests/fixtures/invalid-giscus-whitespace.toml
[params.giscus]
  enabled = true
  repo = "fixture-owner/fixture-repository"
  repoId = "   "
  category = "Fixture category"
  categoryId = "DIC_fixture"
```

```toml
# tests/fixtures/invalid-giscus-enabled.toml
[params.giscus]
  enabled = "true"
  repo = "fixture-owner/fixture-repository"
  repoId = "R_fixture"
  category = "Fixture category"
  categoryId = "DIC_fixture"
```

```toml
# tests/fixtures/invalid-giscus-types.toml
[params.giscus]
  enabled = true
  repo = "fixture-owner/fixture-repository"
  repoId = 42
  category = "Fixture category"
  categoryId = true
```

- [ ] **Step 2: Add failing Giscus markup tests**

Add this method to `GeneratedSiteTests`:

```python
    def test_giscus_uses_one_strict_thread_and_hides_when_incomplete(self):
        with TemporaryDirectory() as temporary:
            production = Path(temporary) / "production"
            build_site(production, "https://example.test/")
            production_post = read_html(production, "p/beyond-the-cloud/index.html")
            self.assertNotIn("giscus.app/client.js", production_post)

            fixture = Path(temporary) / "fixture"
            build_site(
                fixture,
                "https://example.test/",
                "--config", "hugo.toml,tests/fixtures/interactions.toml",
                "--contentDir", "tests/fixtures/content",
            )
            english = read_html(fixture, "p/shared-article/index.html")
            chinese = read_html(fixture, "zh/p/shared-article/index.html")
            common = [
                'data-mapping="specific"',
                'data-term="post:shared-article"',
                'data-strict="1"',
                'data-reactions-enabled="1"',
                'data-emit-metadata="0"',
                'data-theme="preferred_color_scheme"',
                'data-loading="lazy"',
                'crossorigin="anonymous"',
            ]
            for attribute in common:
                self.assertIn(attribute, english)
                self.assertIn(attribute, chinese)
            self.assertRegex(english, r'<script[^>]*\sasync(?:\s|>)')
            self.assertRegex(chinese, r'<script[^>]*\sasync(?:\s|>)')
            self.assertIn('data-lang="en"', english)
            self.assertIn('data-lang="zh-CN"', chinese)

            incomplete = Path(temporary) / "incomplete"
            build_site(
                incomplete,
                "https://example.test/",
                "--config", "hugo.toml,tests/fixtures/incomplete-interactions.toml",
                "--contentDir", "tests/fixtures/content",
            )
            self.assertNotIn("giscus.app/client.js", read_html(incomplete, "p/shared-article/index.html"))

            for index, config in enumerate([
                "tests/fixtures/invalid-giscus-repo.toml",
                "tests/fixtures/invalid-giscus-whitespace.toml",
                "tests/fixtures/invalid-giscus-enabled.toml",
                "tests/fixtures/invalid-giscus-types.toml",
            ]):
                invalid = Path(temporary) / f"invalid-giscus-{index}"
                build_site(
                    invalid,
                    "https://example.test/",
                    "--config", f"hugo.toml,{config}",
                    "--contentDir", "tests/fixtures/content",
                )
                self.assertNotIn("giscus.app/client.js", read_html(invalid, "p/shared-article/index.html"))

    def test_hugo_rejects_invalid_published_interaction_ids(self):
        cases = [
            ("tests/fixtures/invalid-content", "hugo.toml", "interactionId"),
            ("tests/fixtures/nonstring-content", "hugo.toml", "interactionId must be a string"),
            ("tests/fixtures/overlong-content", "hugo.toml", "at most 80 characters"),
            ("tests/fixtures/mismatched-content", "hugo.toml", "translations must share interactionId"),
            (
                "tests/fixtures/missing-id-content",
                "hugo.toml,tests/fixtures/site-id.toml",
                "published blog posts require interactionId",
            ),
        ]
        with TemporaryDirectory() as temporary:
            for index, (content_dir, config, message) in enumerate(cases):
                with self.subTest(content_dir=content_dir):
                    with self.assertRaises(subprocess.CalledProcessError) as failure:
                        build_site(
                            Path(temporary) / str(index),
                            "https://example.test/",
                            "--config", config,
                            "--contentDir", content_dir,
                        )
                    self.assertIn(message, failure.exception.stderr)
```

- [ ] **Step 3: Run the Giscus test to verify it fails**

Run: `python3 -m unittest tests/test_site.py -v`

Expected: FAIL because the interaction entity and Giscus partial do not exist.

- [ ] **Step 4: Implement the shared interaction entity guard**

```html
{{- /* Site-local identity validation shared by Giscus and Kudos. */ -}}
{{- $page := . -}}
{{- $hasValue := isset $page.Params "interactionid" -}}
{{- $value := index $page.Params "interactionid" -}}
{{- $isString := eq (printf "%T" $value) "string" -}}
{{- $raw := "" -}}
{{- if $isString }}{{ $raw = $value }}{{ end -}}
{{- $mustValidate := or (not $page.Draft) $hasValue -}}
{{- $result := "" -}}
{{- if $mustValidate -}}
  {{- if not $hasValue -}}
    {{- errorf "%s: published blog posts require interactionId" $page.File.Path -}}
  {{- else if not $isString -}}
    {{- errorf "%s: interactionId must be a string" $page.File.Path -}}
  {{- else if or (lt (len $raw) 1) (gt (len $raw) 80) (eq (len (findRE `^[a-z0-9]+(-[a-z0-9]+)*$` $raw)) 0) -}}
    {{- errorf "%s: interactionId %q must match ^[a-z0-9]+(?:-[a-z0-9]+)*$ and be at most 80 characters" $page.File.Path $raw -}}
  {{- else -}}
    {{- $translationSetValid := true -}}
      {{- range $translation := $page.Translations -}}
      {{- $otherHasValue := isset $translation.Params "interactionid" -}}
      {{- $otherValue := index $translation.Params "interactionid" -}}
      {{- $otherIsString := and $otherHasValue (eq (printf "%T" $otherValue) "string") -}}
      {{- $otherRaw := "" -}}
      {{- if $otherIsString }}{{ $otherRaw = $otherValue }}{{ end -}}
      {{- if or (not $otherIsString) (ne $otherRaw $raw) -}}
        {{- $translationSetValid = false -}}
        {{- errorf "%s and %s: translations must share interactionId %q" $page.File.Path $translation.File.Path $raw -}}
      {{- end -}}
    {{- end -}}
    {{- if $translationSetValid }}{{ $result = printf "post:%s" $raw }}{{ end -}}
  {{- end -}}
{{- end -}}
{{- return $result -}}
```

- [ ] **Step 5: Implement Giscus and compose it into blog pages**

```html
{{- /* Site-local optional Giscus integration. */ -}}
{{- $page := .Page -}}
{{- $entity := .Entity -}}
{{- $giscus := dict -}}
{{- if isset $page.Site.Params "giscus" -}}
  {{- $configured := index $page.Site.Params "giscus" -}}
  {{- if reflect.IsMap $configured }}{{ $giscus = $configured }}{{ end -}}
{{- end -}}
{{- $enabled := false -}}
{{- if isset $giscus "enabled" -}}
  {{- $value := index $giscus "enabled" -}}
  {{- if eq (printf "%T" $value) "bool" }}{{ $enabled = $value }}{{ end -}}
{{- end -}}
{{- $repo := "" -}}
{{- if isset $giscus "repo" -}}
  {{- $value := index $giscus "repo" -}}
  {{- if eq (printf "%T" $value) "string" }}{{ $repo = strings.TrimSpace $value }}{{ end -}}
{{- end -}}
{{- $repoID := "" -}}
{{- if isset $giscus "repoid" -}}
  {{- $value := index $giscus "repoid" -}}
  {{- if eq (printf "%T" $value) "string" }}{{ $repoID = strings.TrimSpace $value }}{{ end -}}
{{- end -}}
{{- $category := "" -}}
{{- if isset $giscus "category" -}}
  {{- $value := index $giscus "category" -}}
  {{- if eq (printf "%T" $value) "string" }}{{ $category = strings.TrimSpace $value }}{{ end -}}
{{- end -}}
{{- $categoryID := "" -}}
{{- if isset $giscus "categoryid" -}}
  {{- $value := index $giscus "categoryid" -}}
  {{- if eq (printf "%T" $value) "string" }}{{ $categoryID = strings.TrimSpace $value }}{{ end -}}
{{- end -}}
{{- $locale := "" -}}
{{- if eq $page.Language.Lang "en" -}}
  {{- $locale = "en" -}}
{{- else if eq $page.Language.Lang "zh" -}}
  {{- $locale = "zh-CN" -}}
{{- end -}}
{{- $validRepo := gt (len (findRE `^[^[:space:]/]+/[^[:space:]/]+$` $repo)) 0 -}}
{{- if and $entity $enabled $validRepo $repoID $category $categoryID $locale -}}
  <section class="post-interaction comments" aria-label="{{ T "comments" }}">
    <h3>{{ T "comments" }}</h3>
    <script src="https://giscus.app/client.js"
      data-repo="{{ $repo }}"
      data-repo-id="{{ $repoID }}"
      data-category="{{ $category }}"
      data-category-id="{{ $categoryID }}"
      data-mapping="specific"
      data-term="{{ $entity }}"
      data-strict="1"
      data-reactions-enabled="1"
      data-emit-metadata="0"
      data-input-position="bottom"
      data-theme="preferred_color_scheme"
      data-lang="{{ $locale }}"
      data-loading="lazy"
      crossorigin="anonymous"
      async></script>
  </section>
{{- end -}}
```

Compute the identity once, unconditionally, after the TOC in `layouts/blog/page.html`, then pass it to Giscus. This makes invalid published content fail even while Giscus is disabled:

```html
{{ $interactionEntity := partial "interaction-id.html" . }}
{{ partial "giscus.html" (dict "Page" . "Entity" $interactionEntity) }}
```

- [ ] **Step 6: Run Giscus, SEO, and ID tests**

Run: `python3 -m unittest tests/test_site.py tests/test_interaction_ids.py -v`

Expected: all valid tests PASS. Production, incomplete, non-map, whitespace-only, mistyped, and malformed configuration emit no script; padded valid strings are trimmed; the locale derives from the page rather than a free-form parameter; missing, non-string, empty, malformed, overlong, and mismatched published IDs make Hugo exit nonzero even when a site- or language-level fallback exists and integrations are disabled. An exact 80-character ID remains valid, a standalone draft may omit the ID, and a translated draft cannot silently disagree with its published counterpart. Both valid translations emit the same `data-term` with different Giscus locales.

- [ ] **Step 7: Commit Giscus if Git was authorized**

```bash
git add layouts tests/fixtures tests/test_site.py
git commit -m "feat: add shared multilingual Giscus threads"
```

---

### Task 12: Wire Bear Neo upvotes to one shared Kudos entity

**Files:**
- Create: `tests/kudos.test.mjs`
- Create: `assets/js/kudos.mjs`
- Create: `layouts/_partials/kudos.html`
- Create: `tests/fixtures/disabled-kudos.toml`
- Create: `tests/fixtures/invalid-endpoint-relative.toml`
- Create: `tests/fixtures/invalid-endpoint-whitespace.toml`
- Create: `tests/fixtures/invalid-endpoint-http.toml`
- Create: `tests/fixtures/invalid-endpoint-path.toml`
- Create: `tests/fixtures/invalid-endpoint-query.toml`
- Create: `tests/fixtures/invalid-endpoint-fragment.toml`
- Create: `tests/fixtures/invalid-endpoint-port.toml`
- Create: `tests/fixtures/invalid-endpoint-port-zero.toml`
- Create: `tests/fixtures/invalid-endpoint-port-high.toml`
- Create: `tests/fixtures/invalid-endpoint-credentials.toml`
- Create: `tests/fixtures/invalid-endpoint-host.toml`
- Create: `tests/fixtures/invalid-endpoint-label.toml`
- Create: `tests/fixtures/invalid-endpoint-unicode-host.toml`
- Create: `tests/fixtures/invalid-kudos-enabled.toml`
- Create: `tests/fixtures/invalid-kudos-types.toml`
- Create: `tests/fixtures/invalid-kudos-container-scalar.toml`
- Create: `tests/fixtures/invalid-kudos-container-list.toml`
- Create: `tests/fixtures/valid-endpoint-https.toml`
- Create: `tests/fixtures/valid-endpoint-port-min.toml`
- Create: `tests/fixtures/valid-endpoint-port-max.toml`
- Create: `tests/fixtures/valid-endpoint-whitespace.toml`
- Create: `tests/fixtures/valid-endpoint-localhost.toml`
- Create: `tests/fixtures/valid-endpoint-loopback.toml`
- Create: `tests/fixtures/trailing-slash-endpoint.toml`
- Modify: `layouts/blog/page.html`
- Modify: `tests/test_site.py`

- [ ] **Step 1: Write a failing strict mock-API test**

```javascript
// tests/kudos.test.mjs
import assert from "node:assert/strict";
import { createServer } from "node:http";
import test from "node:test";

import { createKudosClient, mountKudos, renderKudos } from "../assets/js/kudos.mjs";


function listen(server) {
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => resolve(server.address()));
  });
}


function close(server) {
  return new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
}


function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}


function jsonResponse(body, status = 200) {
  return { ok: status >= 200 && status < 300, status, json: async () => body };
}


function kudosDom() {
  const attributes = new Map();
  const listeners = new Map();
  const button = {
    disabled: false,
    classList: { toggle: (name, value) => attributes.set(`class:${name}`, value) },
    setAttribute: (name, value) => attributes.set(name, value),
    removeAttribute: (name) => attributes.delete(name),
    addEventListener: (name, handler) => listeners.set(name, handler),
  };
  const count = { textContent: "—" };
  const status = { textContent: "Loading" };
  const root = {
    hidden: true,
    dataset: {
      addLabel: "Upvote",
      removeLabel: "Remove upvote",
      unavailableLabel: "Unavailable",
      updateFailedLabel: "Try again",
      kudosEndpoint: "https://kudos.example.test",
      kudosEntity: "post:shared-article",
      kudosState: "loading",
    },
    setAttribute: (name, value) => attributes.set(`root:${name}`, value),
    querySelector: (selector) => ({
      "[data-kudos-button]": button,
      "[data-kudos-count]": count,
      "[data-kudos-status]": status,
    })[selector],
  };
  return { root, button, count, status, attributes, click: () => listeners.get("click")() };
}


test("Kudos rendering updates count, pressed state, color class, and label", () => {
  const attributes = new Map();
  const button = {
    classList: { toggle: (name, enabled) => attributes.set(`class:${name}`, enabled) },
    setAttribute: (name, value) => attributes.set(name, value),
  };
  const count = { textContent: "—" };
  const status = { textContent: "Loading" };
  const root = {
    dataset: { addLabel: "Upvote", removeLabel: "Remove upvote", kudosState: "loading" },
    setAttribute: (name, value) => attributes.set(`root:${name}`, value),
    querySelector: (selector) => ({
      "[data-kudos-button]": button,
      "[data-kudos-count]": count,
      "[data-kudos-status]": status,
    })[selector],
  };
  renderKudos(root, { count: 8, hasKudos: true });
  assert.equal(count.textContent, "8");
  assert.equal(status.textContent, "");
  assert.equal(attributes.get("aria-pressed"), "true");
  assert.equal(attributes.get("aria-label"), "Remove upvote");
  assert.equal(attributes.get("class:upvoted"), true);
  assert.equal(attributes.get("root:aria-busy"), "false");
  assert.equal(root.dataset.kudosState, "ready");
});


test("Kudos ignores clicks until the initial voter state is known", async () => {
  const requests = [];
  const pending = [];
  let click;
  const attributes = new Map();
  const button = {
    disabled: false,
    classList: { toggle() {} },
    setAttribute: (name, value) => attributes.set(name, value),
    removeAttribute: (name) => attributes.delete(name),
    addEventListener: (name, handler) => { if (name === "click") click = handler; },
  };
  const count = { textContent: "—" };
  const status = { textContent: "Loading" };
  const root = {
    hidden: true,
    dataset: {
      addLabel: "Upvote",
      removeLabel: "Remove upvote",
      unavailableLabel: "Unavailable",
      updateFailedLabel: "Try again",
      kudosEndpoint: "https://kudos.example.test",
      kudosEntity: "post:shared-article",
      kudosState: "loading",
    },
    setAttribute: (name, value) => attributes.set(`root:${name}`, value),
    querySelector: (selector) => ({
      "[data-kudos-button]": button,
      "[data-kudos-count]": count,
      "[data-kudos-status]": status,
    })[selector],
  };
  const fetchImpl = (url, options) => {
    requests.push([options?.method ?? "GET", url]);
    return new Promise((resolve) => pending.push(resolve));
  };

  const controller = mountKudos(root, fetchImpl, { error() {} });
  assert.equal(root.hidden, false);
  assert.equal(button.disabled, true);
  await click();
  assert.deepEqual(requests.map(([method]) => method), ["GET", "GET"]);

  pending[0](jsonResponse({ entity: "post:shared-article", count: 7 }));
  pending[1](jsonResponse({ entity: "post:shared-article", hasKudos: true }));
  await controller.ready;
  assert.equal(button.disabled, false);
  assert.equal(root.dataset.kudosState, "ready");
});


test("Kudos coalesces clicks while one mutation is pending", async () => {
  const dom = kudosDom();
  const mutation = deferred();
  const methods = [];
  const fetchImpl = (url, options) => {
    const method = options?.method ?? "GET";
    methods.push(method);
    if (methods.length === 1) return Promise.resolve(jsonResponse({ entity: "post:shared-article", count: 7 }));
    if (methods.length === 2) return Promise.resolve(jsonResponse({ entity: "post:shared-article", hasKudos: false }));
    return mutation.promise;
  };
  const controller = mountKudos(dom.root, fetchImpl, { error() {} });
  await controller.ready;
  const first = dom.click();
  await dom.click();
  assert.deepEqual(methods, ["GET", "GET", "POST"]);
  mutation.resolve(jsonResponse({ entity: "post:shared-article", count: 8, hasKudos: true }));
  await first;
  assert.equal(dom.count.textContent, "8");
  assert.equal(dom.attributes.get("aria-pressed"), "true");
  assert.equal(dom.button.disabled, false);
});


test("Kudos load failure shows unavailable without a false zero", async () => {
  const dom = kudosDom();
  const controller = mountKudos(
    dom.root,
    async () => { throw new Error("offline"); },
    { error() {} },
  );
  await controller.ready;
  assert.equal(dom.count.textContent, "—");
  assert.equal(dom.status.textContent, "Unavailable");
  assert.equal(dom.button.disabled, true);
  assert.equal(dom.attributes.has("aria-pressed"), false);
  assert.equal(dom.attributes.get("root:aria-busy"), "false");
  assert.equal(dom.root.dataset.kudosState, "error");
});


test("Kudos mutation failure preserves state and permits one retry", async () => {
  const dom = kudosDom();
  let mutationAttempts = 0;
  const fetchImpl = async (url, options) => {
    if (!options?.method && url.endsWith("/kudos")) return jsonResponse({ entity: "post:shared-article", hasKudos: false });
    if (!options?.method) return jsonResponse({ entity: "post:shared-article", count: 7 });
    mutationAttempts += 1;
    if (mutationAttempts === 1) throw new Error("write failed");
    return jsonResponse({ entity: "post:shared-article", count: 8, hasKudos: true });
  };
  const controller = mountKudos(dom.root, fetchImpl, { error() {} });
  await controller.ready;
  await dom.click();
  assert.equal(dom.count.textContent, "7");
  assert.equal(dom.attributes.get("aria-pressed"), "false");
  assert.equal(dom.status.textContent, "Try again");
  assert.equal(dom.button.disabled, false);
  await dom.click();
  assert.equal(mutationAttempts, 2);
  assert.equal(dom.count.textContent, "8");
  assert.equal(dom.attributes.get("aria-pressed"), "true");
});


test("Kudos uses one encoded entity for count, state, add, and remove", async () => {
  const requests = [];
  let count = 7;
  let hasKudos = false;
  const entityPath = "/post%3Ashared-article";
  const server = createServer((request, response) => {
    requests.push([request.method, request.url]);
    response.setHeader("content-type", "application/json");
    response.setHeader("access-control-allow-origin", "*");
    if (request.method === "GET" && request.url === entityPath) {
      response.end(JSON.stringify({ entity: "post:shared-article", count }));
      return;
    }
    if (request.url === `${entityPath}/kudos` && request.method === "GET") {
      response.end(JSON.stringify({ entity: "post:shared-article", hasKudos }));
      return;
    }
    if (request.url === `${entityPath}/kudos` && request.method === "POST") {
      hasKudos = true;
      count += 1;
      response.end(JSON.stringify({ entity: "post:shared-article", count, hasKudos, changed: true }));
      return;
    }
    if (request.url === `${entityPath}/kudos` && request.method === "DELETE") {
      hasKudos = false;
      count -= 1;
      response.end(JSON.stringify({ entity: "post:shared-article", count, hasKudos, changed: true }));
      return;
    }
    response.statusCode = 404;
    response.end(JSON.stringify({ error: "unexpected route" }));
  });

  const address = await listen(server);
  try {
    const client = createKudosClient({
      baseUrl: `http://127.0.0.1:${address.port}`,
      entity: "post:shared-article",
      fetchImpl: fetch,
    });
    assert.deepEqual(await client.load(), { count: 7, hasKudos: false });
    assert.deepEqual(await client.toggle(false), { count: 8, hasKudos: true });
    assert.deepEqual(await client.toggle(true), { count: 7, hasKudos: false });
    assert.deepEqual(requests, [
      ["GET", entityPath],
      ["GET", `${entityPath}/kudos`],
      ["POST", `${entityPath}/kudos`],
      ["DELETE", `${entityPath}/kudos`],
    ]);
  } finally {
    await close(server);
  }
});
```

Extend this skeleton with table-driven successful-response rejection cases. Count and voter-state responses must be objects for the exact requested entity; counts must be nonnegative safe integers; voter state must be a real boolean; and invalid JSON, non-2xx responses, and malformed mutation payloads must fail closed without replacing the last good UI state.

- [ ] **Step 2: Run the Node test to verify it fails**

Run: `node --test tests/kudos.test.mjs`

Expected: ERROR because `assets/js/kudos.mjs` does not exist.

- [ ] **Step 3: Implement a testable Kudos API client and DOM controller**

```javascript
// assets/js/kudos.mjs
function requireEntity(data, entity) {
  if (data === null || typeof data !== "object" || Array.isArray(data)) {
    throw new Error("Kudos returned an invalid payload");
  }
  if (data.entity !== entity) throw new Error("Kudos returned the wrong entity");
  return data;
}

function requireCount(data, entity) {
  requireEntity(data, entity);
  if (!Number.isSafeInteger(data.count) || data.count < 0) {
    throw new Error("Kudos returned an invalid count");
  }
  return data.count;
}

function requireVoterState(data, entity) {
  requireEntity(data, entity);
  if (typeof data.hasKudos !== "boolean") {
    throw new Error("Kudos returned an invalid voter state");
  }
  return data.hasKudos;
}

export function createKudosClient({ baseUrl, entity, fetchImpl = globalThis.fetch }) {
  const root = `${baseUrl.replace(/\/+$/, "")}/${encodeURIComponent(entity)}`;

  async function request(url, options = undefined) {
    const response = await fetchImpl(url, options);
    let data;
    try {
      data = await response.json();
    } catch {
      throw new Error(`Kudos returned invalid JSON (${response.status})`);
    }
    if (!response.ok) {
      const message = (
        data !== null
        && typeof data === "object"
        && !Array.isArray(data)
        && typeof data.error === "string"
      ) ? data.error : `Kudos request failed (${response.status})`;
      throw new Error(message);
    }
    return data;
  }

  return {
    async load() {
      const [count, state] = await Promise.all([
        request(root),
        request(`${root}/kudos`),
      ]);
      return {
        count: requireCount(count, entity),
        hasKudos: requireVoterState(state, entity),
      };
    },
    async toggle(hasKudos) {
      const state = await request(`${root}/kudos`, { method: hasKudos ? "DELETE" : "POST" });
      return {
        count: requireCount(state, entity),
        hasKudos: requireVoterState(state, entity),
      };
    },
  };
}


function setBusy(root, busy) {
  root.setAttribute("aria-busy", String(busy));
}


export function renderKudos(root, state) {
  const button = root.querySelector("[data-kudos-button]");
  const count = root.querySelector("[data-kudos-count]");
  const status = root.querySelector("[data-kudos-status]");
  const hasKudos = state.hasKudos;
  count.textContent = String(state.count);
  button.classList.toggle("upvoted", hasKudos);
  button.setAttribute("aria-pressed", String(hasKudos));
  button.setAttribute("aria-label", hasKudos ? root.dataset.removeLabel : root.dataset.addLabel);
  status.textContent = "";
  root.dataset.kudosState = "ready";
  setBusy(root, false);
}


function renderLoadFailure(root) {
  const button = root.querySelector("[data-kudos-button]");
  root.querySelector("[data-kudos-count]").textContent = "—";
  root.querySelector("[data-kudos-status]").textContent = root.dataset.unavailableLabel;
  button.removeAttribute("aria-pressed");
  button.setAttribute("aria-label", root.dataset.unavailableLabel);
  button.disabled = true;
  root.dataset.kudosState = "error";
  setBusy(root, false);
}


export function mountKudos(root, fetchImpl = globalThis.fetch, logger = console) {
  const button = root.querySelector("[data-kudos-button]");
  const status = root.querySelector("[data-kudos-status]");
  const client = createKudosClient({
    baseUrl: root.dataset.kudosEndpoint,
    entity: root.dataset.kudosEntity,
    fetchImpl,
  });
  let hasKudos = false;
  let loaded = false;
  let writing = false;
  root.hidden = false;
  button.disabled = true;
  setBusy(root, true);

  function render(state) {
    hasKudos = state.hasKudos;
    renderKudos(root, state);
  }

  async function load() {
    try {
      render(await client.load());
      loaded = true;
      button.disabled = false;
    } catch (error) {
      renderLoadFailure(root);
      logger.error("Failed to load Kudos", error);
    }
  }

  button.addEventListener("click", async () => {
    if (!loaded || writing) return;
    writing = true;
    button.disabled = true;
    root.dataset.kudosState = "writing";
    setBusy(root, true);
    try {
      render(await client.toggle(hasKudos));
    } catch (error) {
      status.textContent = root.dataset.updateFailedLabel;
      root.dataset.kudosState = "error";
      logger.error("Failed to update Kudos", error);
    } finally {
      writing = false;
      button.disabled = false;
      setBusy(root, false);
    }
  });

  return { ready: load() };
}


function mountAll() {
  for (const root of document.querySelectorAll("[data-kudos]")) mountKudos(root);
}


if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountAll, { once: true });
  } else {
    mountAll();
  }
}
```

- [ ] **Step 4: Run the strict API test**

Run: `node --test tests/kudos.test.mjs`

Expected: all 31 reported tests PASS (8 top-level cases plus 23 malformed-payload subtests); no false zero is exposed, pre-load and in-flight repeat clicks are ignored, failures are contained/retryable, malformed successful responses are rejected, and the request log proves the colon is encoded exactly once. Node's HTTP mock verifies the API contract but does not enforce browser CORS; live CORS remains a post-deployment check.

- [ ] **Step 5: Add failing generated-markup assertions**

Create each endpoint fixture with this shape, substituting the listed endpoint:

```toml
[params.kudos]
  enabled = true
  endpoint = "VALUE FROM THE TABLE"
```

| Fixture | Endpoint | Expected |
| --- | --- | --- |
| `invalid-endpoint-relative.toml` | `/worker` | suppressed: relative URL |
| `invalid-endpoint-whitespace.toml` | whitespace only | suppressed: empty after trimming |
| `invalid-endpoint-http.toml` | `http://worker.example` | suppressed: non-loopback HTTP |
| `invalid-endpoint-path.toml` | `https://worker.example/api` | suppressed: API is not at the origin root |
| `invalid-endpoint-query.toml` | `https://worker.example/?token=x` | suppressed: query present |
| `invalid-endpoint-fragment.toml` | `https://worker.example/#token` | suppressed: fragment present |
| `invalid-endpoint-port.toml` | `https://worker.example:abc` | suppressed: nonnumeric port |
| `invalid-endpoint-port-zero.toml` | `https://worker.example:0` | suppressed: port below range |
| `invalid-endpoint-port-high.toml` | `https://worker.example:65536` | suppressed: port above range |
| `invalid-endpoint-credentials.toml` | `https://user@worker.example` | suppressed: credentials present |
| `invalid-endpoint-host.toml` | `https://:bad` | suppressed: malformed host |
| `invalid-endpoint-label.toml` | `https://-worker.example` | suppressed: invalid DNS label |
| `invalid-endpoint-unicode-host.toml` | `https://例子.example` | suppressed: non-ASCII host |
| `valid-endpoint-https.toml` | `https://worker.example` | rendered: HTTPS root origin |
| `valid-endpoint-port-min.toml` | `https://worker.example:1` | rendered: minimum valid port |
| `valid-endpoint-port-max.toml` | `https://worker.example:65535/` | rendered: maximum valid port |
| `trailing-slash-endpoint.toml` | `https://worker.example/` | rendered: valid HTTPS root origin |
| `valid-endpoint-whitespace.toml` | padded `https://worker.example/` | rendered after trimming |
| `valid-endpoint-localhost.toml` | `http://localhost:65535/` | rendered: loopback hostname |
| `valid-endpoint-loopback.toml` | `http://127.0.0.1/` | rendered: loopback address |

Create the malformed feature-flag fixture separately:

```toml
# tests/fixtures/invalid-kudos-enabled.toml
[params.kudos]
  enabled = "true"
  endpoint = "https://worker.example"
```

```toml
# tests/fixtures/invalid-kudos-types.toml
[params.kudos]
  enabled = true
  endpoint = 42
```

Add this method to `GeneratedSiteTests`:

```python
    def test_kudos_uses_one_entity_and_hides_when_unconfigured(self):
        with TemporaryDirectory() as temporary:
            production = Path(temporary) / "production"
            build_site(production, "https://example.test/")
            self.assertNotIn("data-kudos", read_html(production, "p/beyond-the-cloud/index.html"))

            fixture = Path(temporary) / "fixture"
            build_site(
                fixture,
                "https://example.test/",
                "--config", "hugo.toml,tests/fixtures/interactions.toml",
                "--contentDir", "tests/fixtures/content",
            )
            for relative in ["p/shared-article/index.html", "zh/p/shared-article/index.html"]:
                html = read_html(fixture, relative)
                self.assertIn('data-kudos-entity="post:shared-article"', html)
                self.assertIn("data-kudos-button", html)
                self.assertIn('data-kudos-state="loading"', html)
                self.assertIn('aria-busy="true"', html)
                self.assertRegex(html, r'<span[^>]*data-kudos-count[^>]*>—</span>')
                self.assertNotIn('aria-pressed=', html)
                self.assertRegex(html, r'<div[^>]*data-kudos[^>]*hidden')
                self.assertRegex(html, r'<button[^>]*data-kudos-button[^>]*disabled')

            incomplete = Path(temporary) / "incomplete"
            build_site(
                incomplete,
                "https://example.test/",
                "--config", "hugo.toml,tests/fixtures/incomplete-interactions.toml",
                "--contentDir", "tests/fixtures/content",
            )
            self.assertNotIn("data-kudos", read_html(incomplete, "p/shared-article/index.html"))

            invalid_configs = [
                "disabled-kudos.toml",
                "invalid-endpoint-relative.toml",
                "invalid-endpoint-whitespace.toml",
                "invalid-endpoint-http.toml",
                "invalid-endpoint-path.toml",
                "invalid-endpoint-query.toml",
                "invalid-endpoint-fragment.toml",
                "invalid-endpoint-port.toml",
                "invalid-endpoint-port-zero.toml",
                "invalid-endpoint-port-high.toml",
                "invalid-endpoint-credentials.toml",
                "invalid-endpoint-host.toml",
                "invalid-endpoint-label.toml",
                "invalid-endpoint-unicode-host.toml",
                "invalid-kudos-enabled.toml",
                "invalid-kudos-types.toml",
                "invalid-kudos-container-scalar.toml",
                "invalid-kudos-container-list.toml",
            ]
            for index, config in enumerate(invalid_configs):
                invalid_endpoint = Path(temporary) / f"invalid-endpoint-{index}"
                build_site(
                    invalid_endpoint,
                    "https://example.test/",
                    "--config", f"hugo.toml,tests/fixtures/{config}",
                    "--contentDir", "tests/fixtures/content",
                )
                self.assertNotIn("data-kudos", read_html(invalid_endpoint, "p/shared-article/index.html"))

            valid_configs = {
                "valid-endpoint-https.toml": "https://worker.example",
                "valid-endpoint-port-min.toml": "https://worker.example:1",
                "valid-endpoint-port-max.toml": "https://worker.example:65535/",
                "trailing-slash-endpoint.toml": "https://worker.example/",
                "valid-endpoint-whitespace.toml": "https://worker.example/",
                "valid-endpoint-localhost.toml": "http://localhost:65535/",
                "valid-endpoint-loopback.toml": "http://127.0.0.1/",
            }
            for index, (config, endpoint) in enumerate(valid_configs.items()):
                valid_endpoint = Path(temporary) / f"valid-endpoint-{index}"
                build_site(
                    valid_endpoint,
                    "https://example.test/",
                    "--config", f"hugo.toml,tests/fixtures/{config}",
                    "--contentDir", "tests/fixtures/content",
                )
                self.assertIn(
                    f'data-kudos-endpoint="{endpoint}"',
                    read_html(valid_endpoint, "p/shared-article/index.html"),
                )
```

- [ ] **Step 6: Run the generated test to verify it fails**

Run: `python3 -m unittest tests/test_site.py -v`

Expected: FAIL because the Kudos partial is not composed into the post page.

- [ ] **Step 7: Render the Bear Neo upvote control only with a valid ID and endpoint**

```html
{{- /* Site-local Bear Neo-compatible Kudos integration. */ -}}
{{- $page := .Page -}}
{{- $entity := .Entity -}}
{{- $kudos := dict -}}
{{- if isset $page.Site.Params "kudos" -}}
  {{- $configured := index $page.Site.Params "kudos" -}}
  {{- if reflect.IsMap $configured }}{{ $kudos = $configured }}{{ end -}}
{{- end -}}
{{- $enabled := false -}}
{{- if isset $kudos "enabled" -}}
  {{- $value := index $kudos "enabled" -}}
  {{- if eq (printf "%T" $value) "bool" }}{{ $enabled = $value }}{{ end -}}
{{- end -}}
{{- $endpoint := "" -}}
{{- if isset $kudos "endpoint" -}}
  {{- $value := index $kudos "endpoint" -}}
  {{- if eq (printf "%T" $value) "string" }}{{ $endpoint = strings.TrimSpace $value }}{{ end -}}
{{- end -}}
{{- $validHTTPS := gt (len (findRE `^https://([A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?\.)*[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?(:[0-9]{1,5})?/?$` $endpoint)) 0 -}}
{{- $validLoopback := gt (len (findRE `^http://(127\.0\.0\.1|localhost)(:[0-9]{1,5})?/?$` $endpoint)) 0 -}}
{{- $validPort := true -}}
{{- if gt (len (findRE `:[0-9]{1,5}/?$` $endpoint)) 0 -}}
  {{- $port := int (replaceRE `^.*:([0-9]{1,5})/?$` "$1" $endpoint) -}}
  {{- $validPort = and (ge $port 1) (le $port 65535) -}}
{{- end -}}
{{- if and $entity $enabled $validPort (or $validHTTPS $validLoopback) -}}
  <div class="upvote-container post-interaction" data-kudos
    data-kudos-entity="{{ $entity }}" data-kudos-endpoint="{{ $endpoint }}"
    data-add-label="{{ T "upvoteAdd" }}" data-remove-label="{{ T "upvoteRemove" }}"
    data-loading-label="{{ T "upvoteLoading" }}"
    data-unavailable-label="{{ T "upvoteUnavailable" }}"
    data-update-failed-label="{{ T "upvoteUpdateFailed" }}"
    data-kudos-state="loading" aria-busy="true" hidden>
    <small class="upvote">
      <button class="upvote-btn" type="button" data-kudos-button aria-label="{{ T "upvoteLoading" }}" disabled>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <polyline points="17 11 12 6 7 11"></polyline>
          <polyline points="17 18 12 13 7 18"></polyline>
        </svg>
        <span class="upvote-count" data-kudos-count aria-live="polite">—</span>
      </button>
      <span class="visually-hidden" data-kudos-status role="status">{{ T "upvoteLoading" }}</span>
    </small>
  </div>
  {{ $script := resources.Get "js/kudos.mjs" | fingerprint "sha256" }}
  <script type="module" src="{{ $script.RelPermalink }}" integrity="{{ $script.Data.Integrity }}"></script>
{{- end -}}
```

Insert the Kudos partial immediately before the Giscus partial in `layouts/blog/page.html`:

```html
{{ partial "kudos.html" (dict "Page" . "Entity" $interactionEntity) }}
{{ partial "giscus.html" (dict "Page" . "Entity" $interactionEntity) }}
```

- [ ] **Step 8: Run both API and generated-site interaction tests**

Run: `node --test tests/kudos.test.mjs`

Expected: all 31 reported Kudos tests PASS (8 top-level cases plus 23 malformed-payload subtests), including load failure, mutation failure, strict successful-payload validation, and rapid-double-click coverage.

Run: `python3 -m unittest tests/test_site.py tests/test_interaction_ids.py -v`

Expected: all tests PASS; English and Chinese fixtures share one entity, the first real response replaces the initial em dash, the fingerprinted SHA-256 module remains base-path safe, production/incomplete/non-map/mistyped/invalid endpoint configurations emit no Kudos initialization, and trimmed HTTPS or loopback root origins—including both port boundaries—render exactly once.

- [ ] **Step 9: Commit Kudos if Git was authorized**

```bash
git add assets/js/kudos.mjs layouts tests/fixtures/invalid-endpoint-*.toml tests/fixtures/invalid-kudos-*.toml tests/fixtures/valid-endpoint-*.toml tests/fixtures/trailing-slash-endpoint.toml tests/kudos.test.mjs tests/test_site.py
git commit -m "feat: share Kudos counts across translations"
```

---

### Task 13: Verify generated base paths and the root/project-subpath build matrix

**Files:**
- Create: `scripts/check_site.py`
- Create: `tests/test_check_site.py`
- Modify: `tests/test_site.py`

- [ ] **Step 1: Write failing base-path-verifier unit tests**

```python
# tests/test_check_site.py
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.check_site import check_site


class GeneratedBasePathTests(unittest.TestCase):
    def test_accepts_relative_and_base_scoped_urls_across_html_and_xml(self):
        with TemporaryDirectory() as temporary:
            site = Path(temporary)
            (site / "blog").mkdir()
            (site / "tags").mkdir()
            (site / "tags" / "index.html").write_text("<h1 id='tags'>Tags</h1>")
            (site / "blog" / "image.png").write_bytes(b"png")
            (site / "blog" / "index.html").write_text(
                '<a href="/example-blog/tags/">Tags</a>'
                '<a href="https://example.test/example-blog/tags/#tags">Canonical tag</a>'
                '<img src="image.png" alt="fixture">',
                encoding="utf-8",
            )
            (site / "sitemap.xml").write_text(
                '<?xml version="1.0"?><urlset><url><loc>'
                'https://example.test/example-blog/tags/'
                '</loc></url></urlset>',
                encoding="utf-8",
            )
            self.assertEqual(
                [],
                check_site(site, "https://example.test/example-blog/"),
            )

    def test_reports_only_internal_urls_that_escape_the_configured_base(self):
        with TemporaryDirectory() as temporary:
            site = Path(temporary)
            (site / "index.html").write_text(
                '<a href="/tags/">Escapes project path</a>'
                '<a href="https://example.test/example-blog/#missing">Missing fragment</a>'
                '<img src="missing.png" alt="missing">'
                '<a href="https://external.example/tags/">External is ignored</a>',
                encoding="utf-8",
            )
            errors = check_site(site, "https://example.test/example-blog/")
            self.assertEqual(1, len(errors))
            self.assertIn("escapes configured base path", errors[0])
            self.assertIn("/tags/", errors[0])


if __name__ == "__main__":
    unittest.main()
```

Expand this initial red-phase skeleton to 16 focused tests: 12 API tests and four CLI tests. Cover missing, non-directory, and empty site roots; valid scoped and external URLs; default and explicit effective ports; scheme-relative references; strict-prefix collisions; percent-encoded CJK and repeatedly decoded dot segments; malformed references and XML, including unknown XML encodings; invalid base URL scheme/host/credentials/whitespace/port/query/fragment; navigable backslashes while opaque skipped schemes remain ignored; external Unicode IDNs; exact CLI success output; nonzero CLI failures; and an unknown-XML-codec CLI failure that reports a contained diagnostic without a traceback.

- [ ] **Step 2: Run the unit tests to verify they fail**

Run: `python3 -m unittest tests/test_check_site.py -v`

Expected: ERROR importing `scripts.check_site`.

- [ ] **Step 3: Implement the focused base-URL verifier**

```python
# scripts/check_site.py
from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
import sys
from urllib.parse import urljoin, urlsplit
import xml.etree.ElementTree as ET


SKIPPED_SCHEMES = {"data", "javascript", "mailto", "tel"}


class ReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.references: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attributes: list[tuple[str, str | None]]) -> None:
        for name, value in attributes:
            if not value:
                continue
            if name in {"href", "src", "poster", "data"}:
                self.references.append((name, value))


def normalize_base_url(base_url: str) -> tuple[str, str, str]:
    parsed = urlsplit(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("base URL must include an http(s) scheme and host")
    normalized_path = f"/{parsed.path.strip('/')}/"
    if normalized_path == "//":
        normalized_path = "/"
    return parsed.scheme.lower(), parsed.netloc.lower(), normalized_path


def reference_error(document_url: str, value: str, base_url: str) -> str | None:
    _, base_netloc, base_path = normalize_base_url(base_url)
    parsed = urlsplit(value)
    if parsed.scheme.lower() in SKIPPED_SCHEMES:
        return None
    resolved = urlsplit(urljoin(document_url, value))
    if resolved.scheme.lower() not in {"http", "https"}:
        return None
    if resolved.netloc.lower() != base_netloc:
        return None
    path = resolved.path or "/"
    if base_path == "/" or path == base_path.rstrip("/") or path.startswith(base_path):
        return None
    return f"{value!r} resolves to {path!r} and escapes configured base path {base_path!r}"


def parse_html(document: Path) -> list[tuple[str, str]]:
    parser = ReferenceParser()
    parser.feed(document.read_text(encoding="utf-8"))
    return parser.references


def parse_xml(document: Path) -> list[tuple[str, str]]:
    references: list[tuple[str, str]] = []
    for element in ET.parse(document).iter():
        local_name = element.tag.rsplit("}", 1)[-1]
        if local_name in {"guid", "link", "loc"} and element.text and element.text.strip():
            references.append((local_name, element.text.strip()))
        for name in {"href", "src", "url"}:
            if value := element.attrib.get(name):
                references.append((name, value))
    return references


def check_site(site_root: Path, base_url: str) -> list[str]:
    site_root = site_root.resolve()
    normalize_base_url(base_url)
    errors: list[str] = []
    documents = sorted([*site_root.rglob("*.html"), *site_root.rglob("*.xml")])
    for document in documents:
        try:
            if document.suffix == ".html":
                references = parse_html(document)
            else:
                references = parse_xml(document)
        except (ET.ParseError, OSError, UnicodeDecodeError) as error:
            errors.append(f"{document.relative_to(site_root)}: unable to parse: {error}")
            continue
        relative = document.relative_to(site_root).as_posix()
        if relative.endswith("index.html"):
            relative = relative[:-len("index.html")]
        document_url = urljoin(base_url, relative)
        for attribute, value in references:
            if error := reference_error(document_url, value, base_url):
                errors.append(f"{document.relative_to(site_root)}: {attribute}={value!r}: {error}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify generated URLs retain the configured base path")
    parser.add_argument("site_root", type=Path)
    parser.add_argument("--base-url", required=True)
    arguments = parser.parse_args(argv)
    errors = check_site(arguments.site_root, arguments.base_url)
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        print(f"base-path verification failed with {len(errors)} error(s)", file=sys.stderr)
        return 1
    print("base-path verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Harden this initial implementation before treating it as complete. Require at least one HTML/XML document; validate ASCII HTTP(S) base URLs and ports from 1 through 65535; normalize the trailing slash; compare normalized hostname plus effective port; reject credentials, query, fragment, invalid host labels, raw-Unicode base hosts, strict-prefix collisions, malformed same-origin references, navigable backslashes, and repeatedly percent-decoded `.` or `..` path segments. Skip `data:`, `javascript:`, `mailto:`, and `tel:` before applying the backslash rule, and IDNA-normalize reference hosts so external Unicode IDNs remain ignored. Parse unquoted HTML `href`, `src`, and `poster`, plus `data` only on `object`; parse XML `link`, `guid`, `loc`, and `url` text plus `href`, `src`, and `url` attributes; report malformed XML, unknown XML encodings, and malformed references without aborting the remaining check or exposing a CLI traceback. Continue to ignore external origins, target existence, fragments, CSS URLs, and `srcset` grammar.

- [ ] **Step 4: Run the base-path-verifier unit tests**

Run: `python3 -m unittest tests/test_check_site.py -v`

Expected: 16 tests PASS: 12 checker API tests and four CLI tests.

- [ ] **Step 5: Strengthen the Hugo build helper and add full build-matrix assertions**

Import the base-path verifier in `tests/test_site.py`:

```python
from scripts.check_site import check_site
```

Keep the command-assembly check separate from the output matrix so it proves `--environment production` is always requested. Extend the matrix skeleton to four minified builds: root and project-subpath bases, each with production content and the interaction fixture. For every applicable build, verify the base-path checker, all three English-only posts and no Chinese copies, `.nojekyll`, the PDF and Rmd resources, archive-only resource exclusion, localized tags, both feeds, the sitemap index and both language child sitemaps, absence of generated `srcset`, literal and percent-encoded CJK routes, canonical shared resources, Beyond's absent language switch and absent forced new-tab behavior, and correctly prefixed primary navigation.

Add these flags to the `command` list in `build_site`, before `*extra_arguments`:

```python
        "--environment", "production",
        "--noBuildLock",
        "--panicOnWarning",
        "--cacheDir", str(destination.parent / "cache"),
```

Add this method to `GeneratedSiteTests`:

```python
    def test_root_and_project_subpath_builds_are_complete(self):
        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            matrix = [
                ("https://example.github.io/", "/", temporary_root / "root"),
                ("https://example.github.io/example-blog/", "/example-blog/", temporary_root / "project"),
            ]
            for base_url, base_path, public in matrix:
                build_site(public, base_url, "--minify")
                self.assertEqual([], check_site(public, base_url))
                for slug in ["beyond-the-cloud", "lekythos-a-shape", "the-miracle-of-istanbul"]:
                    self.assertTrue((public / "p" / slug / "index.html").is_file())
                    self.assertFalse((public / "zh" / "p" / slug / "index.html").exists())
                self.assertTrue((public / ".nojekyll").is_file())
                self.assertTrue((public / "p/beyond-the-cloud/beyond_the_cloud.v5.pdf").is_file())
                self.assertTrue((public / "p/the-miracle-of-istanbul/2021-03-04-The-Miracle-of-Istanbul.Rmd").is_file())
                self.assertFalse((public / "cover.png").exists())
                self.assertFalse((public / "3-3.jpeg").exists())
                beyond = read_html(public, "p/beyond-the-cloud/index.html")
                self.assertNotIn("language-switcher", beyond)
                self.assertNotIn('target="_blank"', beyond)
                tags = read_html(public, "tags/index.html")
                self.assertIn("#visualization", tags)
                visualization = read_html(public, "tags/visualization/index.html")
                self.assertIn("Beyond the Cloud", visualization)

                fixture_public = temporary_root / f"fixture-{public.name}"
                build_site(
                    fixture_public,
                    base_url,
                    "--minify",
                    "--config", "hugo.toml,tests/fixtures/interactions.toml",
                    "--contentDir", "tests/fixtures/content",
                )
                self.assertEqual([], check_site(fixture_public, base_url))
                self.assertTrue((fixture_public / "zh/tags/测试/index.html").is_file())
                shared_zh = read_html(fixture_public, "zh/p/shared-article/index.html")
                self.assertIn(f'src="{base_path}p/shared-article/diagram.svg"', shared_zh)
                self.assertIn(f'href="{base_path}p/shared-article/notes.txt"', shared_zh)

            project_home = read_html(temporary_root / "project", "index.html")
            self.assertEqual(
                [
                    ("/example-blog/", "Home"),
                    ("/example-blog/blog/", "Posts"),
                    ("/example-blog/tags/", "Tags"),
                ],
                primary_navigation(project_home),
            )
```

- [ ] **Step 6: Run every standard-library test and both mock layers**

Run: `python3 -m unittest discover -s tests -p 'test_*.py' -v`

Expected: all 71 Python tests PASS, including the two checker-command/matrix methods, four minified matrix builds, encoded resource/suffix resolution, hidden-page SEO isolation, effective semantic-color contrast, and the non-color upvoted cue.

Run: `node --test tests/*.test.mjs`

Expected: all 35 Node tests PASS: four post-search tests plus 31 reported Kudos tests, against the same search, API, and DOM-state contracts used by the generated fixtures.

- [ ] **Step 7: Exercise the base-path verifier as a command-line program**

Run:

```bash
BLOG_PROJECT_BUILD="$(mktemp -d)"
hugo --gc --minify --panicOnWarning --noBuildLock --cleanDestinationDir --environment production --printI18nWarnings --printPathWarnings --baseURL https://example.github.io/example-blog/ --destination "$BLOG_PROJECT_BUILD"
python3 scripts/check_site.py "$BLOG_PROJECT_BUILD" --base-url https://example.github.io/example-blog/
```

Expected: Hugo exits 0 and the verifier prints `base-path verification passed`.

- [ ] **Step 8: Commit build-matrix verification if Git was authorized**

```bash
git add scripts/check_site.py tests/test_check_site.py tests/test_site.py
git commit -m "test: verify root and Pages subpath builds"
```

---

### Task 14: Add the safe authoring contract, GitHub Pages workflow, and operator documentation

**Files:**
- Create: `archetypes/blog.md`
- Create: `scripts/new_translation.py`
- Create: `.github/workflows/hugo.yml`
- Create: `README.md`
- Create: `tests/test_new_translation.py`
- Create: `tests/test_authoring.py`
- Modify: `tests/test_repository.py`

- [ ] **Step 1: Write failing safe-translation unit tests**

```python
# tests/test_new_translation.py
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.new_translation import create_translation


class TranslationCopyTests(unittest.TestCase):
    def make_source(self, content: Path) -> Path:
        source = content / "blog/my-post/index.en.md"
        source.parent.mkdir(parents=True)
        source.write_text('+++\ninteractionId = "my-post"\n+++\n\nBody\n', encoding="utf-8")
        return source

    def test_copies_source_verbatim_to_new_language_file(self):
        with TemporaryDirectory() as temporary:
            content = Path(temporary)
            source = self.make_source(content)
            target = create_translation(content, "my-post", "en", "zh")
            self.assertEqual(source.read_bytes(), target.read_bytes())

    def test_refuses_to_overwrite_an_existing_translation(self):
        with TemporaryDirectory() as temporary:
            content = Path(temporary)
            self.make_source(content)
            create_translation(content, "my-post", "en", "zh")
            with self.assertRaisesRegex(FileExistsError, "already exists"):
                create_translation(content, "my-post", "en", "zh")

    def test_rejects_a_missing_source(self):
        with TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(FileNotFoundError, "source translation does not exist"):
                create_translation(Path(temporary), "missing", "en", "zh")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the helper test to verify it fails**

Run: `python3 -m unittest tests/test_new_translation.py -v`

Expected: ERROR because `scripts/new_translation.py` does not exist.

- [ ] **Step 3: Implement exclusive translation copying**

```python
# scripts/new_translation.py
from __future__ import annotations

import argparse
from pathlib import Path
import re


SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LANGUAGES = {"en", "zh"}


def create_translation(
    content_root: Path,
    slug: str,
    source_language: str,
    target_language: str,
) -> Path:
    if not SLUG_PATTERN.fullmatch(slug):
        raise ValueError("slug must contain lowercase letters, numbers, or internal hyphens")
    if source_language not in LANGUAGES or target_language not in LANGUAGES:
        raise ValueError("languages must be en or zh")
    if source_language == target_language:
        raise ValueError("source and target languages must differ")

    bundle = content_root / "blog" / slug
    source = bundle / f"index.{source_language}.md"
    target = bundle / f"index.{target_language}.md"
    if not source.is_file():
        raise FileNotFoundError(f"source translation does not exist: {source}")
    payload = source.read_bytes()
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
    parser.add_argument("--content-root", type=Path, default=Path("content"))
    arguments = parser.parse_args(argv)
    try:
        target = create_translation(
            arguments.content_root,
            arguments.slug,
            arguments.source_language,
            arguments.target_language,
        )
    except (FileNotFoundError, FileExistsError, ValueError) as error:
        parser.error(str(error))
    print(f"Created {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Before the helper is complete, resolve the content root, blog root, bundle, and source and require each narrower path to remain inside its intended parent. This rejects a symlinked blog root or source that escapes the content tree while retaining exclusive `xb` creation and byte-for-byte copying.

- [ ] **Step 4: Run the helper tests to verify the minimal implementation**

Run: `python3 -m unittest tests/test_new_translation.py -v`

Expected: 6 tests PASS, including byte-preserving exclusive creation, missing-source handling, unsafe-slug rejection, unknown/same-language rejection, and a symlink-escape regression that keeps writes inside the content root.

- [ ] **Step 5: Add failing repository-contract tests**

Add this mapping beside `PINNED_COMMIT` in `tests/test_repository.py`:

```python
DERIVED_TEMPLATES = {
    "layouts/baseof.html": "layouts/_default/baseof.html",
    "layouts/404.html": "layouts/404.html",
    "layouts/_markup/render-image.html": "layouts/_default/_markup/render-image.html",
    "layouts/_markup/render-link.html": "layouts/_default/_markup/render-link.html",
    "layouts/_partials/header.html": "layouts/partials/header.html",
    "layouts/_partials/nav.html": "layouts/partials/nav.html",
    "layouts/_partials/footer.html": "layouts/partials/footer.html",
    "layouts/_partials/toc.html": "layouts/partials/toc.html",
    "layouts/_partials/custom_head.html": "layouts/partials/custom_head.html",
    "layouts/_partials/seo_tags.html": "layouts/partials/seo_tags.html",
    "layouts/_partials/post-list.html": "layouts/_default/list.html",
    "layouts/blog/page.html": "layouts/_default/single.html",
    "layouts/blog/section.html": "layouts/_default/list.html",
    "layouts/home.rss.xml": "layouts/_default/rss.xml",
}
```

Add these methods to `RepositoryTests`:

```python
    def test_pages_workflow_is_pinned_and_default_branch_aware(self):
        workflow = (ROOT / ".github/workflows/hugo.yml").read_text()
        self.assertIn("HUGO_VERSION: 0.164.0", workflow)
        self.assertIn("actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2", workflow)
        self.assertIn("actions/configure-pages@45bfe0192ca1faeb007ade9deae92b16b8254a0d # v6.0.0", workflow)
        self.assertIn("actions/upload-pages-artifact@fc324d3547104276b827a68afc52ff2a11cc49c9 # v5.0.0", workflow)
        self.assertIn("actions/deploy-pages@cd2ce8fcbc39b97be8ca5fce6e763baed58fa128 # v5.0.0", workflow)
        self.assertIn("Require Node.js 22 or newer", workflow)
        self.assertIn("node --test tests/*.test.mjs", workflow)
        self.assertIn("github.event.repository.default_branch", workflow)
        self.assertIn("include-hidden-files: true", workflow)
        self.assertIn("permissions: {}", workflow)
        self.assertIn("build:\n    permissions:\n      contents: read\n      pages: read", workflow)
        self.assertIn("deploy:\n    permissions:\n      pages: write\n      id-token: write", workflow)
        self.assertNotIn("submodules:", workflow)
        self.assertFalse((ROOT / ".gitmodules").exists())

    def test_derived_templates_record_exact_upstream_sources(self):
        for local, upstream in DERIVED_TEMPLATES.items():
            with self.subTest(local=local):
                template = (ROOT / local).read_text()
                self.assertIn(PINNED_COMMIT, template)
                self.assertIn(upstream, template)

    def test_authoring_contract_documents_translation_identity(self):
        archetype = (ROOT / "archetypes/blog.md").read_text()
        readme = (ROOT / "README.md").read_text()
        self.assertIn("interactionId", archetype)
        self.assertIn("index.en.md", readme)
        self.assertIn("index.zh.md", readme)
        self.assertIn("hugo new content --kind blog content/blog/my-post/index.en.md", readme)
        self.assertIn("python3 scripts/new_translation.py my-post en zh", readme)
        self.assertIn("python3 scripts/validate_interaction_ids.py content", readme)
        self.assertIn("node --test tests/*.test.mjs", readme)
        self.assertIn("actionlint .github/workflows/hugo.yml", readme)
        self.assertIn("b449185be66d239555bf1242fec1169a0a09517f", readme)
```

- [ ] **Step 6: Run repository tests to verify they fail**

Run: `python3 -m unittest tests/test_repository.py -v`

Expected: ERROR because the archetype, workflow, and README do not exist.

- [ ] **Step 7: Add a safe draft bundle archetype**

```toml
+++
title = "{{ replace (path.Base (strings.TrimSuffix "/" .File.Dir)) "-" " " | title }}"
date = "{{ .Date }}"
lastmod = "{{ .Date }}"
draft = true
tags = []
interactionId = "{{ path.Base (strings.TrimSuffix "/" .File.Dir) }}"
+++

## Introduction
```

Save as `archetypes/blog.md`. The generated ID is the leaf-bundle directory name, not the filename `index`.

- [ ] **Step 8: Test the documented authoring commands in an isolated site**

```python
# tests/test_authoring.py
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest

from scripts.validate_interaction_ids import read_front_matter


ROOT = Path(__file__).resolve().parents[1]
SITE_DIRECTORIES = ["archetypes", "assets", "i18n", "layouts", "scripts", "static", "themes"]


class AuthoringWorkflowTests(unittest.TestCase):
    def test_documented_commands_create_a_pair_and_a_chinese_only_bundle(self):
        with TemporaryDirectory() as temporary:
            site = Path(temporary) / "site"
            site.mkdir()
            (site / "content").mkdir()
            shutil.copy2(ROOT / "hugo.toml", site / "hugo.toml")
            for directory in SITE_DIRECTORIES:
                shutil.copytree(ROOT / directory, site / directory)

            commands = [
                ["hugo", "new", "content", "--kind", "blog", "content/blog/my-post/index.en.md"],
                ["python3", "scripts/new_translation.py", "my-post", "en", "zh"],
                ["hugo", "new", "content", "--kind", "blog", "content/blog/chinese-only/index.zh.md"],
            ]
            for command in commands:
                subprocess.run(command, cwd=site, check=True, capture_output=True, text=True)

            english = read_front_matter(site / "content/blog/my-post/index.en.md")
            chinese = read_front_matter(site / "content/blog/my-post/index.zh.md")
            chinese_only = read_front_matter(site / "content/blog/chinese-only/index.zh.md")
            self.assertEqual("my-post", english["interactionId"])
            self.assertEqual(english["interactionId"], chinese["interactionId"])
            self.assertEqual("chinese-only", chinese_only["interactionId"])
            self.assertTrue(english["draft"])
            self.assertTrue(chinese["draft"])
            self.assertIsInstance(english["tags"], list)

            public = Path(temporary) / "public"
            subprocess.run(
                [
                    "hugo", "--source", str(site), "--destination", str(public),
                    "--baseURL", "https://example.test/", "--buildDrafts",
                    "--cleanDestinationDir", "--noBuildLock", "--panicOnWarning",
                ],
                cwd=site,
                check=True,
                capture_output=True,
                text=True,
            )
            english_html = (public / "p/my-post/index.html").read_text()
            chinese_html = (public / "zh/p/my-post/index.html").read_text()
            self.assertIn('href="/zh/p/my-post/"', english_html)
            self.assertIn('href="/p/my-post/"', chinese_html)
            self.assertTrue((public / "zh/p/chinese-only/index.html").is_file())
            self.assertFalse((public / "p/chinese-only/index.html").exists())


if __name__ == "__main__":
    unittest.main()
```

Run: `python3 -m unittest tests/test_authoring.py -v`

Expected: PASS, proving the actual `hugo new` and safe copy commands build linked translations plus a Chinese-only page instead of merely checking README text.

- [ ] **Step 9: Add the GitHub Pages workflow**

```yaml
# .github/workflows/hugo.yml
name: Build and deploy Hugo site

on:
  push:
  workflow_dispatch:

env:
  HUGO_VERSION: 0.164.0

permissions: {}

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    permissions:
      contents: read
      pages: read
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2

      - name: Install Hugo Extended
        shell: bash
        run: |
          wget -O "${RUNNER_TEMP}/hugo.deb" "https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-amd64.deb"
          sudo dpkg -i "${RUNNER_TEMP}/hugo.deb"

      - name: Require Node.js 22 or newer
        shell: bash
        run: test "$(node -p 'parseInt(process.versions.node, 10)')" -ge 22

      - name: Configure GitHub Pages
        id: pages
        uses: actions/configure-pages@45bfe0192ca1faeb007ade9deae92b16b8254a0d # v6.0.0

      - name: Validate content identities
        run: python3 scripts/validate_interaction_ids.py content

      - name: Run Python tests
        run: python3 -m unittest discover -s tests -p 'test_*.py' -v

      - name: Run browser-module tests
        run: node --test tests/*.test.mjs

      - name: Build production site
        run: hugo --gc --minify --panicOnWarning --noBuildLock --cleanDestinationDir --printI18nWarnings --printPathWarnings --baseURL "${{ steps.pages.outputs.base_url }}/"

      - name: Verify generated base paths
        run: python3 scripts/check_site.py public --base-url "${{ steps.pages.outputs.base_url }}/"

      - name: Verify Pages marker
        run: test -f public/.nojekyll

      - name: Upload GitHub Pages artifact
        uses: actions/upload-pages-artifact@fc324d3547104276b827a68afc52ff2a11cc49c9 # v5.0.0
        with:
          path: public
          include-hidden-files: true

  deploy:
    permissions:
      pages: write
      id-token: write
    if: github.event_name == 'workflow_dispatch' || github.ref == format('refs/heads/{0}', github.event.repository.default_branch)
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy GitHub Pages
        id: deployment
        uses: actions/deploy-pages@cd2ce8fcbc39b97be8ca5fce6e763baed58fa128 # v5.0.0
```

This intentionally builds every pushed branch but deploys only a manual run or a push to the repository's actual default branch.

- [ ] **Step 10: Write the local, authoring, and activation guide**

````markdown
# Wenxuan Zhao / 赵文轩

This is a multilingual Hugo blog using the vendored
[Hugo Bear Neo](https://github.com/rokcso/hugo-bearneo) theme. English is the
default language; Simplified Chinese is available under `/zh/`. A post may be
English-only, Chinese-only, or translated into both languages.

## Requirements

- Hugo Extended 0.164.0 or a compatible newer release
- Python 3.11 or newer for validation
- Node.js 22 or newer for the dependency-free browser-module tests
- `actionlint` for checking the Pages workflow

## Preview locally

```sh
hugo server
```

Use `hugo server -D` while previewing drafts.

Open the URL printed by Hugo, normally `http://localhost:1313/`. Giscus and
Kudos are disabled until their external settings are complete, so local
reading and navigation work without either service.

Build the production output and validate it:

```sh
python3 scripts/validate_interaction_ids.py content
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.test.mjs
actionlint .github/workflows/hugo.yml
hugo --gc --minify --panicOnWarning --noBuildLock --cleanDestinationDir --printI18nWarnings --printPathWarnings --baseURL https://example.org/
python3 scripts/check_site.py public --base-url https://example.org/
```

## Write a post

Create an English leaf bundle:

```sh
hugo new content --kind blog content/blog/my-post/index.en.md
```

The archetype creates a draft. Confirm the generated title and `interactionId`
before publishing, add tags, write body sections beginning at H2, and set
`draft = false` when the post is ready. The ID may be corrected while the post
is still unpublished; never change it after publication.

Hugo can scaffold a second language inside an existing leaf bundle. To add
Chinese to the same article, prefer the safe copy helper so the source is
copied verbatim and the target is created exclusively:

```sh
python3 scripts/new_translation.py my-post en zh
```

The helper copies the source verbatim, preserving the immutable `interactionId`,
and refuses to overwrite an existing target. Replace the copied title, body,
and tags with Chinese content; do not create a translation file when no
translation exists. A Chinese-only post uses the original `hugo new content`
command with its own slug and `index.zh.md`:

```sh
hugo new content --kind blog content/blog/chinese-only/index.zh.md
```
Tags may be localized independently. Shared images and downloads belong beside
both `index.en.md` and `index.zh.md` and use relative links without a leading
slash. Images need meaningful alternative text. For an authored display width,
use `{{< bundle-image src="image.jpg" alt="Description" width="400" >}}`.

Publication metadata uses `date` for the original publication date and
`lastmod` for the latest update. Valid IDs are 1–80 lowercase ASCII letters,
numbers, or internal hyphens. Validate after every content change:

```sh
python3 scripts/validate_interaction_ids.py content
```

## GitHub Pages

After creating the public GitHub repository and pushing this project, open the
repository's Pages settings and choose **GitHub Actions** as the source. The
workflow builds with the Pages-provided base URL, so it supports both a user
site and a repository project site. The vendored theme requires no submodule.

## Giscus comments

Giscus stays hidden until all values under `[params.giscus]` in `hugo.toml`
are set and `enabled = true`. The eventual public repository must have
Discussions enabled, the Giscus App installed, and a Discussion category
selected at https://giscus.app. The template uses strict `specific` mapping,
so translations sharing an `interactionId` use one Discussion thread.
Giscus is ad-free and stores comments in public GitHub Discussions. Viewing an
enabled comment section loads the third-party `giscus.app`; commenting and
authentication require a GitHub account. It may be slow or unreachable in
mainland China, but a failure affects only the comment region.

## Registration-free Kudos

The upvote client targets [puinoib/kudos](https://github.com/puinoib/kudos),
inspected at commit `b449185be66d239555bf1242fec1169a0a09517f`.
GitHub Pages cannot run this mutable service. To activate it:

1. Fork the inspected Kudos repository.
2. Create a Cloudflare D1 database.
3. Create a Cloudflare Worker connected to the fork and set its
   `D1_DATABASE_ID` build variable to that database's ID.
4. Use the repository's `pnpm run deploy` command for the Worker deployment.
5. If origin restrictions are enabled, set `ALLOWED_ORIGINS` to the final Pages
   origin and the local preview origin used for testing.
6. Set `[params.kudos].endpoint` to the deployed Worker URL and
   `enabled = true` in `hugo.toml`.

Use a credential-free HTTPS origin in production, with no path beyond an
optional trailing slash, no query or fragment, and any explicit port between 1
and 65535. Plain HTTP is accepted only for `localhost` or `127.0.0.1` fixture
testing. When enabled, every post load sends
count and voter-state GET requests to the Worker, so Cloudflare receives normal
request metadata including the visitor's public IP. The inspected Worker stores
a SHA-256-derived identity rather than the raw IP; people on a shared public IP
may therefore share voting state. `ALLOWED_ORIGINS` is browser CORS policy, not
authentication. English and Chinese translations use the same
`post:<interactionId>` entity and count.

For the deterministic local API contract, run `node --test tests/kudos.test.mjs`.
To serve the non-production interaction fixture for a
browser pass:

```sh
BLOG_INTERACTION_BUILD="$(mktemp -d)"
hugo --gc --minify --noBuildLock --cleanDestinationDir \
  --config hugo.toml,tests/fixtures/interactions.toml \
  --contentDir tests/fixtures/content \
  --baseURL http://127.0.0.1:1314/ \
  --destination "$BLOG_INTERACTION_BUILD"
python3 -m http.server 1314 --bind 127.0.0.1 --directory "$BLOG_INTERACTION_BUILD"
```

The acceptance browser pass intercepts Giscus and the fixture Worker routes, so
it never contacts production services. Live Worker CORS is verified only after
deployment. No analytics or advertising scripts are included; Giscus and Kudos
are the only optional third-party requests.

## Source migration archive

The three root Markdown files and `writings-images/` are retained as untouched
migration inputs. Hugo publishes only resources copied into `content/blog/`
leaf bundles.
````

- [ ] **Step 11: Validate workflow syntax and repository contracts**

Run: `actionlint .github/workflows/hugo.yml`

Expected: no output and exit 0.

Run: `python3 -m unittest tests/test_repository.py -v`

Expected: 7 tests PASS, including immutable action pins, exact job permissions, artifact/base-path commands, provenance, and the authoring/operator contract.

- [ ] **Step 12: Run the documented commands verbatim**

Run:

```bash
python3 scripts/validate_interaction_ids.py content
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.test.mjs
actionlint .github/workflows/hugo.yml
hugo --gc --minify --panicOnWarning --noBuildLock --cleanDestinationDir --printI18nWarnings --printPathWarnings --baseURL https://example.org/
python3 scripts/check_site.py public --base-url https://example.org/
```

Expected: every command exits 0 and the base-path verifier reports success.

- [ ] **Step 13: Commit documentation and Pages automation if Git was authorized**

```bash
git add .github/workflows/hugo.yml README.md archetypes/blog.md scripts/new_translation.py tests/test_authoring.py tests/test_new_translation.py tests/test_repository.py
git commit -m "docs: add authoring and Pages deployment workflow"
```

---

### Task 15: Perform final visual, interaction, and acceptance verification

**Files:**
- Verify: all files above
- Modify only if a verification result exposes a concrete defect

- [ ] **Step 1: Invoke the required completion skills**

Before making any completion claim, read and follow `verification-before-completion`. After the full suite is green, read and follow `requesting-code-review`, dispatch an independent reviewer against the approved design and this plan, and resolve findings with `receiving-code-review` where needed.

- [ ] **Step 2: Run the clean verification suite from the project root**

```bash
python3 scripts/validate_interaction_ids.py content
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.test.mjs
actionlint .github/workflows/hugo.yml
hugo --gc --minify --panicOnWarning --noBuildLock --cleanDestinationDir --printI18nWarnings --printPathWarnings
python3 scripts/check_site.py public --base-url https://example.org/
```

Expected: every command exits 0; no Hugo i18n/path warning is printed; Python reports 71 passing tests and Node reports 35 (four post-search plus 31 Kudos).

- [ ] **Step 3: Re-run an explicit GitHub project-site build**

```bash
BLOG_FINAL_BUILD="$(mktemp -d)"
hugo --gc --minify --panicOnWarning --noBuildLock --cleanDestinationDir --environment production --printI18nWarnings --printPathWarnings --baseURL https://example.github.io/example-blog/ --destination "$BLOG_FINAL_BUILD"
python3 scripts/check_site.py "$BLOG_FINAL_BUILD" --base-url https://example.github.io/example-blog/
```

Expected: both commands exit 0 and no URL escapes `/example-blog/`.

- [ ] **Step 4: Start the local server and inspect browser behavior**

First confirm `npx` is available and try the Playwright skill's wrapper. If registry resolution is unavailable, discover an already cached Playwright package beneath the directory reported by `npm config get cache` and use it with an installed local Chrome; do not hard-code the current cache identifier, modify package manifests, or install project dependencies merely for this pass. If neither the wrapper nor a usable cached package/browser exists, report the browser pass as blocked rather than substituting DOM-only checks.

Run `hugo server --bind 127.0.0.1 --port 1313 --disableFastRender` in a persistent terminal session. Use that Playwright browser workflow to inspect:

- `/`, `/blog/`, `/tags/`, and at least one English tag archive.
- `/zh/`, `/zh/blog/`, and `/zh/tags/` including their valid empty states.
- All three English posts, with special attention to the poster link, three Lekythos images, twenty Istanbul images, long R code blocks, footnotes, TOC, and Rmd download.
- Desktop at approximately 1280×900 and mobile at approximately 390×844.
- Emulated light and dark browser preferences, confirming colors change automatically and no manual toggle exists. Check the effective tertiary/upvoted tokens against the page background at 4.5:1 or better and confirm the original dark token values remain in effect.
- Computed Chinese `font-family` contains the configured CJK chain, and Chinese prose line-height is at least 1.6 times its font size without forced letter spacing.
- Posts search matches a title substring, but entering only a rendered publication date produces the localized no-results state. In a Turkish-locale context, `istanbul` still matches `The Miracle of Istanbul`, proving matching does not depend on locale-sensitive casing.
- Keyboard focus on navigation, tag links, image zoom controls, and the disabled-by-default absence of Giscus/Kudos.

Expected: exactly three primary page destinations remain usable, no document-level horizontal overflow occurs, images have nonzero rendered size, code blocks do not widen the page, and content remains readable in both color schemes.

- [ ] **Step 5: Inspect the configured interaction fixture without contacting production services**

Build and serve the fixture in persistent terminal sessions:

```bash
BLOG_INTERACTION_BUILD="$(mktemp -d)"
hugo --gc --minify --noBuildLock --cleanDestinationDir \
  --config hugo.toml,tests/fixtures/interactions.toml \
  --contentDir tests/fixtures/content \
  --baseURL http://127.0.0.1:1314/ \
  --destination "$BLOG_INTERACTION_BUILD"
python3 -m http.server 1314 --bind 127.0.0.1 --directory "$BLOG_INTERACTION_BUILD"
```

Use Playwright request interception before opening the page:

- Abort `https://giscus.app/**`; confirm both article bodies, primary navigation, tags, TOC, and language switch remain visible and usable.
- Fulfill `http://127.0.0.1:4174/post%3Ashared-article` and its `/kudos` child with one in-memory `{count, hasKudos}` state and exact GET/POST/DELETE methods. Answer any browser OPTIONS preflight with 204 and `Access-Control-Allow-Methods: GET, POST, DELETE, OPTIONS`; every mock response includes `Access-Control-Allow-Origin: http://127.0.0.1:1314`, while JSON routes also use the JSON content type.
- Verify `loading → ready`, a real count replacing `—`, one POST for a rapid double click, and the same count/pressed state after switching from English to Chinese through `post:shared-article`. The pressed icon must change from outline to a solid fill in addition to its color and `aria-pressed` changes.
- After the successful POST leaves the shared state upvoted, return 503 for the next DELETE, verify the last correct count/pressed state remains with the localized retry status, then allow a retry and verify exactly one new DELETE succeeds.
- In a fresh context, return 503 for both initial Kudos GETs; verify the localized unavailable state contains no false `0`, remains disabled with `aria-busy="false"`, and leaves article content/navigation usable.
- In another fresh context, abort both initial Kudos GETs as a transport outage and verify the same contained unavailable state without hiding the article or navigation.
- Open the percent-encoded Chinese tag route and confirm it lists the two Chinese fixtures but not the English fixture title.

No production interaction service is contacted during this pass. Aborted Giscus/Kudos requests and deliberate 503 responses are expected to produce request-failure or console diagnostics, so those outage contexts do not have a false “clean console” requirement; the acceptance condition is containment, correct widget state, and no uncaught page error that disrupts content or navigation. The Node HTTP test proves the pinned route/JSON contract but cannot enforce browser CORS; live Worker CORS and real Giscus Discussion creation remain post-deployment checks.

- [ ] **Step 6: Review the final diff and preserve user-owned inputs**

Run `git status --short` and `git diff --check` when Git was authorized. Confirm the original root Markdown files, all files in `writings-images/`, and unrelated workspace changes remain unmodified. Confirm no production `public/` directory is staged.

Expected: only intentional project files appear; `git diff --check` has no whitespace errors.

- [ ] **Step 7: Obtain independent code review and rerun affected verification**

Give the reviewer the approved spec path, this plan path, and the final diff. For each valid finding, add a focused failing regression test, make the smallest fix, and rerun that test plus the full suite before proceeding.

- [ ] **Step 8: Create the final implementation commit if Git was authorized**

Only when review finds no remaining defect and the full verification output is fresh. Stage only project files created by this plan; leave the original root Markdown and `writings-images/` migration inputs untracked unless the user separately asks to archive them in Git:

```bash
git add .github .gitignore README.md archetypes assets content docs/superpowers hugo.toml i18n layouts scripts static tests themes
git commit -m "feat: build multilingual Bear Neo blog"
```

Skip this commit when all implementation tasks were already committed and there is no remaining diff.

- [ ] **Step 9: Hand off the local site and deferred remote values**

Report the local server URL, exact passing commands, and the fact that Giscus and Kudos are intentionally hidden until the public GitHub repository IDs and Cloudflare Worker endpoint are available. Do not claim remote deployment; provide the README steps for enabling Pages and later activating the integrations.
