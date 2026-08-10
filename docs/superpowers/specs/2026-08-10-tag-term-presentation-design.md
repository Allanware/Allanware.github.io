# Individual Tag Page Presentation

## Goal

Make individual tag pages concise while preserving their existing multilingual content grouping, search behavior, and base-path-safe links.

## Visible behavior

- Replace the English heading `Tagged “<term>”` with `Tag: <term>`.
- Replace the Chinese heading `标签“<term>”下的内容` with `标签：<term>`.
- Remove the `All tags` / `全部标签` backlink from individual tag pages.
- Hide the visible project and post counts within individual tag pages.
- Keep the `Projects` group before the `Posts` group when both exist.
- Keep dates, titles, localized empty states, and useful per-group search controls unchanged.

The main Tags overview continues to display the number of tagged entries. The Posts archive continues to display its post count. This change affects only individual tag-term pages.

## Implementation

The shared post-list partial will accept a per-call `ShowCount` option. When omitted, it will continue to follow the site-wide `showPostCount` setting. The individual tag template will pass `ShowCount = false` to both project and post groups.

The hidden singular/plural templates and live status region remain present because the client-side search uses them to announce filtered result counts accessibly. Only the visible count paragraph is suppressed.

The obsolete `allTags` translations will be removed. The existing `filteringFor` translation key will supply the new English and Chinese heading formats.

## Verification

Generated-site tests will cover English and Chinese term pages at root and project-subpath base URLs. They will assert:

- exact localized headings;
- absence of the tag-overview backlink;
- absence of visible project and post count paragraphs;
- retained project-before-post ordering and group-local content;
- retained search controls where a group has at least two entries;
- unchanged counts on the main Tags overview and Posts archive.

The full Python and Node suites, interaction-ID validator, actionlint, JavaScript syntax checks, and strict Hugo root/project-subpath builds will remain green.
