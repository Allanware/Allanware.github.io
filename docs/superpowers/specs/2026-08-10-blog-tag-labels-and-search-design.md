# Blog and Tag Labels with Working Search

## Goal

Use `Blog` and `博客` consistently for the blog collection on the blog archive
and individual tag pages, give those lists a neutral search prompt, and fix the
search results that remain visible after JavaScript marks them hidden.

## Agreed terminology

The existing English archive title and primary-navigation label will remain
`Blog`. Their Chinese equivalents will remain `博客`.

This design supersedes the earlier archive-year-heading specification only
where that document said tag post-group headings would remain `Posts` and
`文章`.

The post-group heading on an individual tag page will change from `Posts` to
`Blog` in English and from `文章` to `博客` in Chinese. The corresponding search
label and placeholder on blog lists will change from `Search posts` to
`Search...` and from `搜索文章` to `搜索...`.

The following item-oriented language will remain unchanged:

- `No matching posts` and `没有匹配的文章`;
- post result counts and empty states;
- `Posts by Wenxuan Zhao` and `赵文轩的文章` metadata;
- homepage `Latest posts` and `Popular posts` headings and their Chinese
  `最新文章` and `热门文章` equivalents;
- RSS descriptions, individual-entry actions, and popular-post status text;
  and
- developer-facing post identifiers, data attributes, translation keys, and
  variable names.

Project group headings and project search labels on tag pages will also remain
unchanged.

## Search defect and correction

The title-matching JavaScript already behaves correctly. For an `istanbul`
query it sets `hidden` on the nonmatching Lekythos row and its 2022 year marker,
leaves the Istanbul row and 2021 marker unhidden, and announces `1 post`.

The visual result is wrong because author CSS overrides the browser's native
hidden presentation: the theme forces every blog-list row to `display: flex`,
and site CSS forces year markers to `display: block`. Consequently, elements
with a `hidden` attribute still receive layout boxes. An irrelevant query shows
the no-results message while the supposedly hidden rows remain rendered.

Site-local CSS will restore the native contract after the existing list rules:

```css
ul.blog-posts li[hidden] {
  display: none !important;
}
```

The selector is limited to rows in blog-style lists. Removing the `hidden`
attribute restores each row's existing flex or block presentation, so the
JavaScript does not need inline styles, custom classes, or knowledge of the
layout CSS. The current title normalization, per-list mounting, accessible live
status, no-results behavior, and year filtering remain unchanged.

## Source changes

Only the following production sources should change:

- `i18n/en.toml`: update the `posts` and `searchPosts` values;
- `i18n/zh.toml`: update the same two localized values; and
- `assets/css/site.css`: add the scoped hidden-row rule after the explicit blog
  list display rules.

Templates, JavaScript, internal translation keys, content, configuration,
vendored theme files, and documentation terminology are outside the change.

## Verification

Automated tests will first fail on the old label values and missing hidden-row
CSS contract, then pass after the minimal source changes. Generated root and
project-subpath pages will verify that:

- English and Chinese tag post-group headings render `Blog` and `博客`;
- English and Chinese blog-list searches render `Search...` and `搜索...`;
- no-match messages, counts, empty states, metadata, home headings, feeds, and
  article actions retain their post/文章 wording;
- project headings and project search labels remain unchanged; and
- the site stylesheet contains a later, scoped `li[hidden]` rule that wins over
  both row display declarations.

The existing Node tests will continue to verify title matching, independent
list filtering, year visibility state, result counts, and accessible status
announcements. Browser verification against a built site will additionally
check computed visibility, which the fake DOM cannot model:

- `istanbul` visibly leaves only `The Miracle of Istanbul` and the 2021 marker;
- an irrelevant query visibly leaves no rows or year markers and shows
  `No matching posts`;
- clearing the query restores every row and year marker; and
- searchable archive and fixture tag lists behave the same in English and
  Chinese without affecting project groups.

The complete Python and Node suites, strict Hugo root/subpath builds, and
repository checks will run after the focused regressions.
