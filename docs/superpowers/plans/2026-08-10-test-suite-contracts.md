# Test Suite Contract Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make editorial and branding changes independent from tests while preserving behavioral, accessibility, security, and deployment contracts.

**Architecture:** Production content is exercised only through generic build validation. Feature behavior is tested with synthetic fixtures and independent expected values; repository tests parse executable configuration instead of policing documentation prose.

**Tech Stack:** Python `unittest`, Node test runner, Hugo, TOML, HTML/XML parsers.

---

### Task 1: Prove the Current Editorial Coupling

**Files:**
- Observe: `tests/test_content.py`
- Observe: `tests/test_repository.py`
- Observe: `content/blog/lekythos-a-shape/index.en.md`
- Observe: `README.md`

- [ ] **Step 1: Copy the repository to a temporary directory and make harmless editorial mutations**

Use `rsync` to copy the working tree without `.git`, append whitespace to an article, and append a harmless sentence to the README.

- [ ] **Step 2: Run the coupled tests and verify they fail for editorial reasons**

Run `python3 -m unittest tests.test_content tests.test_repository -v` in the temporary copy. Expected: failures mention a body SHA-256 mismatch and README text expectations, proving the undesired behavior exists.

### Task 2: Remove Production Content Snapshots

**Files:**
- Delete: `tests/test_content.py`
- Modify: `tests/test_site.py`

- [ ] **Step 1: Remove the migrated-content snapshot module**

Delete the tests that pin article metadata, bodies, resource inventories, image alt text, and asset hashes.

- [ ] **Step 2: Reduce the production matrix to generic smoke contracts**

For both root and project base URLs, retain only a successful Hugo build, `check_site(...) == []`, nonempty HTML/XML output, parseable XML, `.nojekyll`, and base-path-safe generated URLs. Remove named article, production resource, and production copy assertions.

- [ ] **Step 3: Remove production-article integration cases**

Delete the tests dedicated to Beyond the Cloud, Lekythos, and Istanbul routes/resources. Equivalent route, resource, shortcode, and markup behavior remains covered by synthetic bundles elsewhere in `test_site.py`.

- [ ] **Step 4: Run the Python suite**

Run `python3 -m unittest discover -s tests -p 'test_*.py' -v`. Expected: all remaining tests pass.

### Task 3: Stop Testing Documentation Copy

**Files:**
- Modify: `tests/test_repository.py`

- [ ] **Step 1: Remove the README phrase inventory**

Replace `test_authoring_and_operator_contract_is_documented` with an archetype-only contract that verifies required front-matter fields and the starter heading. Do not read `README.md` in the test.

- [ ] **Step 2: Keep executable deployment and security checks**

Retain action SHA pins, job permission parsing, build/deploy wiring, theme provenance, and license checks because these are executable or legal repository contracts.

- [ ] **Step 3: Run repository tests**

Run `python3 -m unittest tests.test_repository -v`. Expected: all repository tests pass.

### Task 4: Make Site Expectations Independent of Production Configuration

**Files:**
- Modify: `tests/test_site.py`
- Create: `tests/fixtures/branding.toml`

- [ ] **Step 1: Add independent branding fixture values**

Create a Hugo overlay configuration containing synthetic English/Chinese titles, contact email, GitHub URL, Scholar URL, Giscus identifiers, and kudos endpoint.

- [ ] **Step 2: Build branding tests with the overlay**

Pass `--config hugo.toml,tests/fixtures/branding.toml` and assert the synthetic values appear in output. Remove module-level reads of production branding fields.

- [ ] **Step 3: Fix synthetic content home titles**

Replace literal `{SITE_TITLE_EN}` and `{SITE_TITLE_ZH}` strings with fixed fixture titles such as `Fixture Home` and `Fixture Home ZH`. These fixtures must not import production branding.

- [ ] **Step 4: Convert RSS production expectations to synthetic content**

Use temporary English, Chinese, visible, and hidden posts to verify localized feeds, ordering, limits, escaping, and subpath links without naming production articles or dates.

- [ ] **Step 5: Run focused site tests**

Run `python3 -m unittest tests.test_site -v`. Expected: all site tests pass.

### Task 5: Remove Presentation Implementation Snapshots

**Files:**
- Modify: `tests/test_site.py`

- [ ] **Step 1: Keep outcome-based color checks**

Remove exact hexadecimal color assertions. Parse the configured semantic colors and retain WCAG contrast-ratio checks for light and dark schemes.

- [ ] **Step 2: Remove exact desktop layout assertions**

Delete checks for fixed margins, grouped-column width, optical offsets, and heading font-size literals. Retain accessibility-critical rules for hidden filtered rows, focus visibility, and mobile search input sizing.

- [ ] **Step 3: Run focused site tests**

Run `python3 -m unittest tests.test_site -v`. Expected: all site tests pass.

### Task 6: Verify Editorial Invariance and the Full Suite

**Files:**
- Verify: `tests/`
- Verify: `.github/workflows/hugo.yml`

- [ ] **Step 1: Run static cleanup checks**

Search for production article SHA-256 constants, resource hash maps, README reads, production titles, production contact values, and literal `{SITE_TITLE_...}` fixture strings. Expected: none remain in tests.

- [ ] **Step 2: Run all Python and Node tests**

Run `python3 -m unittest discover -s tests -p 'test_*.py' -v` and `node --test tests/*.test.mjs`. Expected: zero failures.

- [ ] **Step 3: Run production build validation**

Build Hugo with the production environment into a temporary destination, then run `python3 scripts/check_site.py` with the same base URL. Expected: successful build and `base-path verification passed`.

- [ ] **Step 4: Repeat harmless mutations in a temporary copy**

Change article text, article metadata, README prose, a media file, and branding values only in the copy, then run the relevant tests. Expected: the suite does not fail because it no longer snapshots those values; Hugo may reject deliberately invalid content, so mutations must remain syntactically valid.

- [ ] **Step 5: Review the final diff**

Run `git diff --check`, inspect `git diff --stat`, and review every changed test for a clear behavioral contract.
