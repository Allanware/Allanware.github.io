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

## Prototype 2: Train of Thought (Second Revision Selected for Review)

The first train iteration was rejected because its thin, skeletal line drawing
looked ugly and its three-second crossing disappeared too quickly. The second
revision keeps the same homepage-only concept but replaces that drawing with a
larger, rounded, filled toy steam train. It has one compact carriage, a chunky
locomotive, cut-out windows and wheel hubs, and three soft smoke puffs. Its cute
character comes from simple proportions and motion rather than a face, so it
does not become a second mascot.

The monochrome inline SVG is approximately `10.5rem` wide and `4rem` tall. It
inherits the site's secondary text color, uses the page background for its
window and hub cut-outs, and contains fewer internal strokes than the rejected
version. It remains crisp and responsive without depending on an emoji or
platform font.

When the ending enters the viewport, the train takes `5.5s` to travel through a
clipped lane from left to right. The full train is visible for most of that
journey. Its wheels rotate and its smoke puffs rise gently during the same
one-shot sequence; neither effect runs after the train has left.

Only after the train has left the lane does localized copy fade in:

- English: `there goes my train of thought.`
- Chinese: `思绪又飘走了。`

The existing localized return link fades in beneath the line. Clicking it is a
literal restart: script sets the current URL fragment to `#home-top` and reloads
the page. The reload resets the animation state and lands at the homepage's top
anchor. The old observer-based scroll-and-rearm behavior is removed because it
did not reliably restart in the user's browser. Without JavaScript, the link
retains its normal fragment-link fallback.

The train uses CSS rather than an animated GIF, never loops, and adds no external
asset. The reduced-motion version omits the crossing, wheel, smoke, and fade
sequences; it centers the train in its lane and shows the final line and return
link immediately. Activating the link still performs the same hard restart.

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

Dependency-free Node tests cover one-shot viewport activation, observer cleanup,
fallback when `IntersectionObserver` is unavailable, the final visible state,
the fragment-plus-reload restart, and reduced-motion behavior where it is
controlled by script.

The full Python and Node test suites, the strict Hugo build, and a browser review
at desktop and mobile widths verify each prototype before it is presented for
visual judgment.

## Review Sequence

1. Implement and render the escaping-thought prototype. (Complete.)
2. Review it in site. (Complete; rejected as insufficiently interesting or
   cute.)
3. Replace it with the train-of-thought prototype using `思绪又飘走了。` for the
   Chinese analogy. (Complete; first train drawing and timing rejected.)
4. Replace the first train with the larger filled toy-train revision, slow the
   crossing to `5.5s`, and make the return link hard-reload the homepage.
   (Active.)
5. Pause for another in-site review.
6. Keep the preferred prototype and remove temporary comparison code.

The two versions are never shown together, and no final choice is assumed until
both have been seen in the site.
