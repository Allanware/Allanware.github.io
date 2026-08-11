# Collapsible Callout Design

## Goal

Save space in “The Miracle of Istanbul” by hiding the long “My working
session” section by default while keeping it available to readers on demand.

## Design

Support Hugo Markdown alerts as reusable callouts through the blockquote render
hook. An Obsidian-style fold marker controls native disclosure markup:

- `[!TYPE]- Title` renders a closed `<details>` element.
- `[!TYPE]+ Title` renders an open `<details open>` element.
- An alert without a fold marker remains visible prose.

The alert title becomes the `<summary>`. The alert body continues through
Hugo’s Markdown renderer, so code blocks retain syntax highlighting. Ordinary
Markdown blockquotes remain `<blockquote>` elements. Native disclosure markup
keeps the interaction keyboard-accessible and functional without JavaScript.

The Istanbul post will replace its “My working session” heading with a folded
note titled “My working session”. Its existing `sessionInfo()` command and
output will be nested inside that callout without changing their content.

## Presentation

Callouts use the site’s existing border and secondary-text colors. The summary
is bold, shows a pointer cursor, receives the site focus outline, and gains a
small bottom margin only while open. The initial implementation does not add
type-specific colors or icons.

Built-in labels for untitled note, tip, important, warning, and caution alerts
will be localized in English and Chinese. Explicit titles such as “My working
session” are rendered verbatim.

## Verification

- Build the multilingual fixture and confirm `-` starts closed while `+`
  starts open.
- Confirm Markdown code inside a folded callout still receives syntax
  highlighting.
- Confirm unmarked alerts, localized default labels, and ordinary blockquotes
  retain their intended markup.
- Build the real site and assert that the Istanbul page contains one closed
  callout summarized as “My working session”, with the session command and
  output inside it.
- Run the full regression suite.

## Scope

The change is limited to the Markdown blockquote render hook, callout styles,
callout label translations, focused fixture/test coverage, and the Istanbul
post. No JavaScript, shortcode, theme-vendor edit, or unrelated content change
is required.
