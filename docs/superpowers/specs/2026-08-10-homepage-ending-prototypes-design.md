# Homepage Ending Prototypes Design

## Goal

Compare two quiet, homepage-only endings in the real Hugo site without adding a
second mascot or competing with the writing. The escaping-thought prototype has
been reviewed and rejected. The active second prototype is a tiny train of
thought. Only one prototype is present in the working tree at a time.

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

## Prototype 1: Escaping Thought (Rejected)

The first review build rendered:

- English: `There was one more thing` followed by a small outlined thought
  balloon.
- Chinese: `好像还有件事` followed by the same thought balloon.

The balloon is a monochrome inline SVG with a scalloped cloud and two trailing
bubbles. It follows the site's text color, stays crisp at different pixel
densities, and does not inherit platform-specific emoji styling. It is
decorative and hidden from assistive technology; the paragraph's localized
accessible label supplies the complete thought.

When the ending enters the viewport, the balloon floats diagonally up and to the
right, then fades away. The movement plays once per encounter and does not loop
while the ending remains visible. After the balloon leaves, a small localized
link fades in:

- English: `↑ perhaps start over`
- Chinese: `↑ 要不从头再来`

The link targets the top of the current homepage and uses smooth scrolling when
the browser permits it. Clicking it also re-arms the ending. The observer waits
until the ending has fully left the viewport, then allows the balloon to play
again on the reader's next scroll to the bottom. It must not restart immediately
while the smooth return-to-top scroll is still moving away from the ending. The
link remains a normal fragment link so navigation still works when JavaScript
is unavailable.

An `IntersectionObserver` starts each armed sequence only when the ending is
actually encountered. If the API is unavailable, the ending settles into its
completed, usable state rather than remaining hidden; the link still returns to
the homepage fragment target.

With `prefers-reduced-motion: reduce`, the balloon remains static, the return
link is visible immediately, and no smooth-scroll or floating animation is
applied.

## Prototype 2: Train of Thought (Selected for Review)

The second review build replaces the balloon in the same homepage-only slot. A
small, rounded line-drawn toy train crosses a clipped lane from left to right
once when the ending enters the viewport. The train consists of a locomotive,
one carriage, visible wheels, and two smoke puffs so the silhouette reads
immediately without relying on an emoji or platform font. A gentle vertical bob
adds personality while the overall motion remains quiet.

Only after the train has left the lane does localized copy fade in:

- English: `there goes my train of thought.`
- Chinese: `思绪又飘走了。`

The existing localized return link fades in beneath the line and keeps the
replay contract established during the first review: clicking it scrolls to the
top, the observer waits for the ending to leave the viewport, and the train may
play again only after the reader returns to the bottom.

The train is an inline SVG animated with CSS rather than an animated GIF. It
inherits the site's secondary text color, stays crisp and responsive, never
loops, and adds no external asset. The reduced-motion version omits the crossing
and fade sequence, centers the train in its lane, and shows the final line and
return link immediately.

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
readable text. The decorative thought balloon and train pieces are hidden from
assistive technology; localized text carries their meaning.

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

Dependency-free Node tests cover armed viewport activation, no replay while the
ending remains visible, re-arming through the return link, replay after a full
viewport exit and re-entry, fallback when `IntersectionObserver` is unavailable,
the final visible state, return-to-top behavior, and reduced-motion behavior
where it is controlled by script.

The full Python and Node test suites, the strict Hugo build, and a browser review
at desktop and mobile widths verify each prototype before it is presented for
visual judgment.

## Review Sequence

1. Implement and render the escaping-thought prototype. (Complete.)
2. Review it in site. (Complete; rejected as insufficiently interesting or
   cute.)
3. Replace it with the train-of-thought prototype using `思绪又飘走了。` for the
   Chinese analogy. (Active.)
4. Pause for a second in-site review.
5. Keep the preferred prototype and remove temporary comparison code.

The two versions are never shown together, and no final choice is assumed until
both have been seen in the site.
