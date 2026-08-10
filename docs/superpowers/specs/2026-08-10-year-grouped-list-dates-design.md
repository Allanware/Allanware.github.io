# Year-Grouped List Date Presentation

## Goal

Remove the duplicated year from row dates wherever content is already grouped beneath a visible year heading.

## Visible behavior

The main Posts archives and individual tag pages will keep their year headings while rendering each row date as localized month and day only:

- English: `March 4`, `November 8`
- Chinese: `3月4日`, `11月8日`

This applies to both project and post groups on individual tag pages. Sorting, dates, titles, links, project-before-post ordering, and search behavior remain unchanged.

Article pages continue to show complete localized publication dates, including the year. RSS, sitemap dates, front matter, and other metadata remain unchanged.

## Implementation

Add one language-local `listDateFormat` parameter:

- English: `January 2`
- Chinese: `1月2日`

The shared post-list partial will use `listDateFormat` for visible row text and fall back to the existing full `dateFormat` when the list-specific parameter is absent. The semantic `<time datetime="YYYY-MM-DD">` value, year-group metadata, and year headings remain complete.

The existing `dateFormat = ":date_long"` settings remain the source for article-page publication dates.

## Verification

Generated-site tests will cover English and Chinese output at root and project-subpath base URLs. They will assert:

- localized yearless row dates on the Posts archives;
- localized yearless row dates in project and post groups on individual tag pages;
- retained year headings and complete ISO `datetime` attributes;
- no visible repeated year inside list-row date text;
- unchanged complete localized dates on article pages;
- unchanged ordering, links, search controls, and base-path behavior.

The full Python and Node suites, interaction-ID validator, actionlint, JavaScript syntax checks, and strict Hugo root/project-subpath builds must remain green.
