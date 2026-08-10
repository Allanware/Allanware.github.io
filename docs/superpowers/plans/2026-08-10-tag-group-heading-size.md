# Tag Group Heading Size Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make direct tag-group headings slightly larger than their nested year headings.

**Architecture:** Add one narrowly scoped CSS rule for direct `h3` children of `[data-tag-group]`. Lock the exact selector/value in the existing generated-site test suite and verify the computed hierarchy in a real browser.

**Tech Stack:** Hugo, CSS, Python `unittest`, Playwright with installed Chrome.

---

### Task 1: Enlarge direct tag-group headings

**Files:**
- Modify: `tests/test_site.py` near the existing year-heading CSS tests
- Modify: `assets/css/site.css` before the post-year rules

- [ ] **Step 1: Write the failing CSS contract test**

Add this method to `GeneratedSiteTests`:

```python
def test_tag_group_headings_are_larger_than_year_headings(self):
    site_css = (ROOT / "assets/css/site.css").read_text(encoding="utf-8")
    group_rule = re.search(
        r"\[data-tag-group\]\s*>\s*h3\s*\{([^}]*)\}",
        site_css,
        re.DOTALL,
    )

    self.assertIsNotNone(group_rule)
    self.assertRegex(group_rule.group(1), r"font-size:\s*1\.25em;")
```

- [ ] **Step 2: Run the test and verify RED**

```bash
python3 -B -m unittest \
  tests.test_site.GeneratedSiteTests.test_tag_group_headings_are_larger_than_year_headings \
  -v
```

Expected: FAIL because the direct tag-group heading rule does not exist.

- [ ] **Step 3: Add the minimal CSS rule**

Add before the existing `ul.blog-posts li.post-year` rule:

```css
[data-tag-group] > h3 {
  font-size: 1.25em;
}
```

- [ ] **Step 4: Run focused regressions and verify GREEN**

```bash
python3 -B -m unittest \
  tests.test_site.GeneratedSiteTests.test_tag_group_headings_are_larger_than_year_headings \
  tests.test_site.GeneratedSiteTests.test_year_group_headings_align_with_grouped_date_columns \
  tests.test_site.GeneratedSiteTests.test_year_heading_optically_aligns_with_date_text \
  tests.test_site.GeneratedSiteTests.test_tag_results_group_projects_before_posts \
  -v
```

Expected: all four tests pass.

- [ ] **Step 5: Verify computed browser sizes**

Serve the multilingual fixture and inspect each populated tag group in Chrome.
For every direct group heading and its first nested year heading, assert:

```javascript
Number.parseFloat(getComputedStyle(groupHeading).fontSize) >
  Number.parseFloat(getComputedStyle(yearHeading).fontSize)
```

Expected: direct Blog/博客 and Projects/项目 headings compute to `20px`, while
their nested year headings remain about `18.72px` at the default root size.

- [ ] **Step 6: Run complete regressions and commit**

```bash
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.test.mjs
git diff --check
git add assets/css/site.css tests/test_site.py
git commit -m "style: enlarge tag group headings"
```

Expected: all tests pass, only the two intended files change, and the commit is
clean.
