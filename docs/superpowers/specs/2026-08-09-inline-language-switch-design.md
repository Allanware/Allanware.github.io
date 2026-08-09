# Inline Language Switch Design

**Date:** 2026-08-09
**Status:** Approved

## Goal

Keep the single alternate-language link on the same visual row as the localized Home, Posts, and Tags navigation. The language link must no longer consume a separate line in the header.

## Design

The primary navigation and language navigation remain separate `<nav>` elements so their accessible labels and meanings stay distinct. A new presentational wrapper groups both elements into one navigation row.

The row uses a non-wrapping flex layout with baseline alignment. The primary navigation continues to contain exactly three destinations. The language navigation continues to render only when the current page has a real visible translation and continues to contain exactly one link to that alternate translation. No current-language label or second language link is added.

The existing separator before the language link remains. The Chinese language label changes from `简体中文` to the shorter `中文`; the English label remains `English`. Routes, `hreflang`, `lang`, and accessible-name behavior do not change.

## Responsive Behavior

The complete navigation row must fit without document-level horizontal overflow at the existing 390-pixel mobile acceptance width. Links stay compact and do not split onto separate lines. The site title remains on its own line above the navigation row.

## Verification

Generated-site tests will require:

- one navigation-row wrapper;
- exactly three primary links;
- exactly one alternate-language link on translated pages;
- the Chinese alternate-language link is labelled exactly `中文`;
- both navigation elements as direct children of the shared wrapper;
- no language navigation for an untranslated post;
- non-wrapping flex rules in the site stylesheet.

A browser check at desktop and 390-pixel mobile widths will confirm that the two navigation elements share a row and that the document has no horizontal overflow.

## Non-goals

- Showing both language names simultaneously.
- Adding the language link to the primary menu.
- Changing the `English` label or any language code/locale.
- Changing translation availability rules or URLs.
