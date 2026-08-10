# Remove Homepage Copy Assertions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop homepage prose edits from failing unrelated site tests.

**Architecture:** Remove only the intro-specific assertion block from the existing combined brand/contact/favicon test. Preserve every other assertion and make no production changes.

**Tech Stack:** Python `unittest`, Hugo generated-site fixtures.

---

### Task 1: Remove homepage-intro assertions

**Files:**
- Modify: `tests/test_site.py:2158-2176`

- [ ] **Step 1: Confirm the existing failure**

With the current uncommitted homepage copy edit present, run:

```bash
python3 -B -m unittest \
  tests.test_site.GeneratedSiteTests.test_localized_brand_contact_and_generated_favicons \
  -v
```

Expected: two failures because the test compares the rendered English sentence
to the previous copy for root and subpath builds.

- [ ] **Step 2: Remove the intro assertion block**

Delete the complete block beginning with:

```python
expected_intros = {
    "en": "<p>I am a ill-defined multi-modal functionoid</p>",
    "zh": "",
}
```

and ending after both intro-specific assertions:

```python
self.assertNotIn("<a ", intro.group(1))
self.assertNotIn("mailto:", intro.group(1))
```

Do not alter the surrounding title, brand, contact-email, image-integrity,
favicon, language, or deployment-path assertions.

- [ ] **Step 3: Run focused and complete verification**

```bash
python3 -B -m unittest \
  tests.test_site.GeneratedSiteTests.test_localized_brand_contact_and_generated_favicons \
  -v
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.test.mjs
```

Expected: the focused test passes for both deployment paths, Python reports 94
passing tests, and Node reports 60 passing tests.

- [ ] **Step 4: Audit and commit**

```bash
git diff --check -- tests/test_site.py
git diff -- tests/test_site.py
git add tests/test_site.py
git commit -m "test: stop pinning homepage intro copy"
```

Expected: only the intro assertion block is removed; the current homepage
content edit remains unstaged and uncommitted.
