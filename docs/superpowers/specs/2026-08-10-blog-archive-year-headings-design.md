# Blog Archive Year Headings

## Goal

Match the year-group presentation of the reference archive at
`https://rokcso.com/blog/`, rename the archive navigation labels, and remove the
visible archive count without changing post-oriented copy elsewhere.

## Visible behavior

The English primary-navigation label and English blog archive title will read
`Blog`. Because the archive content title supplies Hugo's page metadata, the
English document title and social metadata title will also use `Blog`.

The Chinese primary-navigation label and Chinese blog archive title will both
read `博客`. The individual tag-page post-group label will remain `文章`.

Every visible year group will use a heading aligned with the left edge of its
date column. The heading will have the reference layout's heading size and
vertical spacing. This presentation applies to:

- the English and Chinese blog archives; and
- the post and project lists on individual English and Chinese tag pages.

Both localized blog archives will continue to provide post search, but neither
will show the initial visible post-count paragraph. Search result announcements
and the list's localized count strings will remain available to the existing
search script. Individual tag pages already suppress their visible group counts
and will retain that behavior.

The following text will not be renamed: tag-page `Posts` and `文章` group
headings, `Latest posts`, `Popular posts`, search placeholders and states, count
strings, empty states, and prose descriptions such as `Posts by Wenxuan Zhao`.

## Implementation

The shared `post-list.html` partial will keep each year marker as a valid list
item with its existing `post-year` class and `data-post-year` attribute. Its
year text will become an `h3` rather than an inline `strong` element. This keeps
the JavaScript search contract intact while giving each group a semantic
heading.

Site-local CSS will make the year list item a block and give its `h3` the same
zero horizontal offset and 16-pixel vertical margin used by the reference.
Dates will retain the inherited fixed 80-pixel grouped column, so the year and
date share a left edge and titles continue to start at the second column.

The shared partial is used by both the blog archive and individual tag pages,
so one markup and style change will cover every required list. Existing
uncommitted work that abbreviates long English month names must be preserved.

The blog section template will pass `ShowCount = false` to the shared partial.
This uses the partial's existing caller override rather than disabling
`showPostCount` globally or changing tag-page behavior.

The English archive content title and English menu label will change to `Blog`.
The Chinese archive content title and menu label will change to `博客`.
Repository documentation that names the three navigation items will be updated
to match.

## Verification

Generated-site tests will cover root and project-subpath builds and assert:

- English navigation and archive page/document titles use `Blog`;
- Chinese navigation and archive page/document titles use `博客` while
  individual tag-page post-group headings remain `文章`;
- unrelated post-oriented labels remain unchanged;
- archive and individual tag lists render each year as an `h3` inside the
  existing `li.post-year[data-post-year]` marker;
- the year-marker style has no horizontal indentation and retains reference
  heading spacing;
- grouped dates retain their 80-pixel column on archive and tag pages;
- both localized blog archives keep their search controls and scripts but omit
  the visible `data-post-count` paragraph; and
- tag-page counts remain hidden and year filtering metadata remains intact.

The focused generated-site tests will run first, followed by the complete
Python and Node suites, interaction-ID validation, JavaScript syntax checks,
workflow linting, and strict Hugo builds at both root and project-subpath base
URLs. A browser-level layout check will compare the computed left coordinates
of the year heading and the first grouped date on both an archive and an
individual tag page.
