# Reader Easter Eggs Concept Catalogue

## Purpose

Preserve four quiet reader easter-egg concepts for later selection without
choosing an implementation subset. Each concept stands on its own and can be
evaluated independently. This catalogue also leaves open whether Concepts 1 and
2 become one sequence or remain separate trails.

## Shared Principles

- Easter eggs stay peripheral. They never block or interrupt normal reading.
- The site owner authors every editorial sentence, connection, signature, and
  symbol mapping. None of this material is generated.
- English and Chinese content develop organically rather than mirroring each
  other. Trails, notes, and lexicons may differ between languages.
- Hidden interactions remain keyboard-accessible. Nonessential movement is
  removed or replaced when the reader prefers reduced motion.
- Reader state stays on the reader's device. No concept adds analytics,
  accounts, or server-side persistence.

Concept 4 gives equivalent English and Chinese tag concepts the same
editorially assigned symbol. The equivalence is editorial; it does not require
the two languages to have matching content, trails, lexicons, or browsing
histories.

## Concept 1: “See Also, Somehow”

This concept turns an authored association between posts into a trail of
unfinished thoughts.

### Trigger and Reveal

Once an eligible paragraph is unlocked, it receives a subdued `↝`. Activating
the mark reveals a one- or two-sentence tentative association written by the
site owner. A phrase that belongs naturally in that note links to the related
post.

The paragraph and post remain complete without opening the association. The
mark is an optional layer rather than a prompt that competes with the prose.

### Progression and Result

Following the linked phrase unlocks another association at the related post.
The new note starts a different thought; it does not answer, complete, or
resolve the note that led there. The result is a locally unlocked trail through
authored connections rather than a question-and-answer chain.

English and Chinese use independent connection sets and independent trail
state. A connection in one language does not require a corresponding connection
in the other.

### Dependencies and Boundaries

The concept depends on eligible paragraph anchors, owner-authored association
copy, natural link phrases, editorially selected post connections, and local
unlock state. Its first unlock also depends on the train-caption gateway for
Concepts 1–3. How that gateway shares the train interaction with Concept 4 is
not settled here.

The association note may navigate only through its authored phrase link. The
catalogue does not make this trail part of Concept 2 or declare it separate from
Concept 2.

## Concept 2: “The Word That Followed You Home”

This concept follows one naturally recurring word as its meaning changes across
posts.

### Trigger and Reveal

The site owner selects a word that already appears naturally, with different
meanings, in at least two posts. Once an occurrence is unlocked, it receives a
faint dotted underline. Activating it creates a small destination link from a
copy of the word.

At the destination, that copy merges with the word's next natural occurrence.
Reduced-motion presentation must communicate the same arrival and unlocked
state without requiring the merge animation.

### Progression and Result

One trail follows the same word from beginning to end; it never switches to a
different word midway. Each destination advances to another editorially chosen
occurrence of that word. When the route is complete, the word joins a hidden
homepage lexicon that shows its semantic itinerary.

English and Chinese maintain different trails and different lexicons. Neither
language must reuse the other's travelling words, meanings, destinations, or
route lengths.

### Dependencies and Boundaries

The concept depends on owner-selected words, occurrences with genuinely
different meanings, an authored order of destinations, stable occurrence
anchors, local progress state, and a homepage lexicon. The word remains part of
the original prose; the easter egg does not insert a convenient occurrence or
generate an interpretation.

Its initial unlock depends on the train-caption gateway for Concepts 1–3.
Whether its route shares a larger sequence with Concept 1 remains deferred.

## Concept 3: “Marginal Notes from Another Allan”

This concept adds a discoverable companion voice beside the published prose.

### Trigger and Reveal

The notes form a companion layer unlocked by another mechanism. Once an
eligible note is available, a small pencil tick opens it as a muted, indented
line below its paragraph. The tick remains an accessible control; the note is
not a navigation link.

Every note and every contextual signature is manually authored. A note may
express doubt, later knowledge, humor, memory, or a cross-disciplinary
interruption, but each note has one clear purpose.

### Progression and Result

Discovery adds the note to the reader's local unlocked state. A discovered note
remains reopenable, but it stays collapsed during ordinary reading. Opening or
reopening it does not advance a route or send the reader to another page.

### Dependencies and Boundaries

The concept depends on stable paragraph anchors, owner-authored note text and
contextual signatures, a separate companion-layer unlock, and local discovery
state. The train-caption gateway for Concepts 1–3 supplies that separate
unlock, but how it coexists with Concept 4's reveal is not decided here.

Marginalia must never conceal a factual error. Errors in published prose are
corrected publicly in the article or its visible correction record; a marginal
note may add perspective but cannot substitute for that correction.

## Concept 4: “Where Was I? — The Tag Manifest”

This concept turns the tags encountered during one browsing session into a
hidden homepage histogram.

### Session Ledger

Each distinct post or project contributes its tags once during the current
browsing session, whether or not the hidden manifest has been revealed.
Revisiting the same item does not increment its tags again. Session closure
clears the ledger.

Equivalent English and Chinese tag concepts share an emoji or textmoji chosen
by the site owner. A concept unique to one language receives its own assigned
symbol. Every tag must have an explicit editorial mapping: a missing mapping
fails validation instead of receiving a generic fallback symbol.

### First Reveal and Later Updates

The first reveal follows one sequence. The reader encounters the homepage train
and activates `Catch the next one` or `那就赶下一班`. That activation returns
the reader to the top. There, the reader activates the visually unchanged site
title, which unfolds the session-to-date histogram. The title interaction must
remain keyboard-accessible even though its appearance does not advertise the
hidden layer.

Tags from later distinct posts and projects update the manifest automatically
during that session. The ledger does not need another train encounter to accept
those updates.

### Resulting Artifact

The homepage manifest is an emoji histogram, never a list of visited titles.
Each tag concept has a stack, and stacks stay in the order their concepts were
first encountered. A stack shows at most five symbols; a taller count adds
`+n` for the remaining number.

Hovering, focusing, or tapping a stack reveals a localized disclosure containing
the tag name and exact count. The histogram is bookkeeping, not navigation: its
symbols and disclosed labels do not open tag pages, posts, or projects.

### Dependencies and Boundaries

The concept depends on stable post and project identities, their tag metadata,
localized tag names, a complete owner-authored tag-symbol mapping, a local
session ledger, and the homepage train, return, and site-title interactions.
The session-local ledger retains stable item identities only to deduplicate
contributions. It also retains tag counts and first-encounter order. The
manifest renders symbols, localized tag names, and exact counts, but never
visited item identities or titles. None of its output is navigation. No state
survives session closure.

## Deferred Decisions

The catalogue intentionally does not decide:

- which subset of the four concepts will be implemented;
- whether Concepts 1 and 2 form one sequence or separate trails;
- how the train-caption gateway for Concepts 1–3 coexists with Concept 4's
  train, return-to-top, and site-title reveal;
- the exact post connections, travelling words, marginal notes, contextual
  signatures, or tag-symbol mappings; or
- final animation and styling details, which require prototypes inside the
  site.
