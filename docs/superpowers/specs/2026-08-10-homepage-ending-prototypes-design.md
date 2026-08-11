# Homepage Ending Prototypes Design

## Goal

Compare two quiet, homepage-only endings in the real Hugo site without adding a
second mascot or competing with the writing. Review them sequentially: first an
escaping thought, then a tiny train of thought. Only one prototype is present in
the working tree at a time.

## Shared Placement and Tone

The prototype appears at the end of `layouts/home.html`, immediately after the
Popular posts section and inside the home content container. It is not part of
the global footer, so it never appears on blog posts, project pages, archives,
tag pages, or error pages.

A responsive gap of `clamp(8rem, 25vh, 15rem)` separates the ending from the
real homepage content. The ending uses the site's existing typography and
semantic color tokens at a subdued intensity. It introduces no bitmap art,
sound, persistent state, analytics, or external dependency.

English and Chinese homepages receive equivalent localized copy through the
existing i18n catalogs. The interaction must fit narrow screens without
horizontal overflow in either language or color scheme.

## Prototype 1: Escaping Thought

The first review build renders:

- English: `There was one more thing` followed by three individually addressable
  dots.
- Chinese: `好像还有件事` followed by three individually addressable dots.

When the ending first enters the viewport, the dots detach in sequence, drift
down and to the right, and fade away. The movement plays once per page load and
does not loop. After the final dot leaves, a small localized link fades in:

- English: `↑ perhaps start over`
- Chinese: `↑ 要不从头再来`

The link targets the top of the current homepage and uses smooth scrolling when
the browser permits it. It remains a normal fragment link so navigation still
works when JavaScript is unavailable.

An `IntersectionObserver` starts the one-shot sequence only when the ending is
actually encountered. If the API is unavailable, the ending settles into its
completed, usable state rather than remaining hidden.

With `prefers-reduced-motion: reduce`, the dots remain static, the return link is
visible immediately, and no smooth-scroll or drifting animation is applied.

## Prototype 2: Train of Thought

After the first prototype has been reviewed, it is replaced in the same
homepage-only slot by a second review build. A small typographic/line-drawn train
crosses the available width once when the ending first enters the viewport.
After it exits, localized copy appears:

- English: `there goes my train of thought.`
- Chinese: `思路又跑了。`

The train uses text and CSS rather than an animated GIF, keeping the result
monochrome, crisp, responsive, and non-looping. The reduced-motion version omits
the crossing animation and shows the final line immediately. Exact train glyphs,
speed, and spacing can be tuned during the second in-site review without
changing the shared placement or accessibility contract.

## Implementation Boundaries

The homepage template owns the semantic markup. A small homepage-ending partial
may be introduced if it keeps the prototype swap isolated and readable. Styles
live in `assets/css/site.css`. Behavior lives in a dedicated ES module under
`assets/js/` and loads only on a homepage that renders the active prototype.

No existing title, introduction, project list, post list, Popular posts
behavior, footer, or vendored Bear Neo theme file changes as part of the
prototype.

## Accessibility and Failure Behavior

The ending is decorative editorial content, not a live status announcement, so
its animation does not use an ARIA live region. Visible copy remains ordinary
readable text. Decorative train pieces are hidden from assistive technology;
the revealed sentence carries the meaning.

The return-to-top control is a keyboard-focusable link with the site's existing
focus treatment. Script failure leaves meaningful text and a working link.
Animations use transforms and opacity only, and reduced-motion preferences
remove nonessential motion.

## Verification

Implementation follows test-driven development. Generated-site tests cover both
root and project-subpath base URLs and assert that the active ending:

- appears on English and Chinese homepages with localized copy;
- appears after Popular posts;
- does not appear on representative non-home pages;
- emits base-path-safe assets and a working top fragment target; and
- uses semantic markup without a looping media asset.

Dependency-free Node tests cover one-shot viewport activation, fallback when
`IntersectionObserver` is unavailable, the final visible state, return-to-top
behavior, and reduced-motion behavior where it is controlled by script.

The full Python and Node test suites, the strict Hugo build, and a browser review
at desktop and mobile widths verify each prototype before it is presented for
visual judgment.

## Review Sequence

1. Implement and render the escaping-thought prototype.
2. Pause for the user's in-site review.
3. Replace it with the train-of-thought prototype.
4. Pause for a second in-site review.
5. Keep the preferred prototype and remove temporary comparison code.

The two versions are never shown together, and no final choice is assumed until
both have been seen in the site.
