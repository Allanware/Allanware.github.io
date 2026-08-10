# Tag Group Heading Size Design

## Goal

Make the `Blog`/`博客` heading on individual tag pages visibly but modestly
larger than nested year headings such as `2021`.

## Root cause

The tag-group label and each nested year are both rendered as `h3` elements.
They therefore inherit the same browser heading size even though they represent
different levels in the page hierarchy.

## Design

Add one site-scoped CSS rule targeting only direct headings of tag-result
groups:

```css
[data-tag-group] > h3 {
  font-size: 1.25em;
}
```

The selector applies equally to localized Blog and Project group headings. It
does not affect year headings inside `ul.blog-posts`, archive-page headings, or
other site headings. Existing markup, translations, alignment rules, spacing,
and search behavior remain unchanged.

## Verification

- Add a focused CSS contract test for the exact selector and `1.25em` value.
- Build the multilingual fixture and use a real browser to confirm each direct
  tag-group heading computes larger than its nested year heading.
- Run the full Python and Node regression suites.

## Scope

Only `assets/css/site.css` and the corresponding test in
`tests/test_site.py` should change. No template, JavaScript, localization,
content, configuration, or vendored-theme changes are required.
