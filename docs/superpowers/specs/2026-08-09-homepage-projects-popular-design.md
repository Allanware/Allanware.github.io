# Homepage Projects and Live Popular Posts Design

## Goal

Replace the minimal multilingual homepage with a structured, language-local
landing page that introduces Wenxuan Zhao, highlights projects, lists the three
latest posts, and ranks up to five popular posts from live Kudos counts. Move
“Beyond the Cloud” from Posts to Past projects without changing its public URL,
resources, tags, Giscus discussion, or Kudos identity.

## Scope

This change includes:

- localized site titles: `Ramblings` in English and `闲扯` in Chinese;
- a one-sentence localized contact placeholder whose visible text contains the
  author's name and “Contact me”/“联系我,” while the email address appears only
  as the `mailto:` link target;
- localized Projects, Past projects, Latest posts, and Popular posts homepage
  sections;
- a dedicated Hugo projects content section;
- live, title-only popular-post ranking from Kudos public counts;
- project-first grouping on individual tag result pages; and
- tests and documentation for the new content model and runtime behavior.

This change does not add a Projects item to the primary navigation, visible
vote counts on the homepage, a Worker batch endpoint, scheduled builds, or
cross-language fallback content. The projects section index is not rendered;
projects are reached from the homepage, tags, sitemap, and direct article URLs.

## Localized Homepage Structure

The existing site header remains the page-level `h1`. Homepage content appears
in this order:

1. A short introductory paragraph.
2. An `h2` Projects/项目 section.
   - An `h3` Past projects/过往项目 subsection.
   - A title-only list of past projects available in the active language.
   - A localized empty message when the active language has no past projects.
3. An `h2` Latest posts/最新文章 section.
   - At most three visible, published blog posts in reverse chronological
     order.
   - Title links only; no dates, summaries, tags, or counts.
4. An `h2` Popular posts/热门文章 section.
   - At most five visible, published blog posts in live Kudos order.
   - Title links only; no visible vote counts.

The introductory copy is:

- English: `Wenxuan Zhao. Contact me.`
- Chinese: `赵文轩。联系我。`

Only “Contact me”/“联系我” is linked. Its destination is
`mailto:xiaodoubizwx@gmail.com`; the address is not rendered as visible text.
The placeholder can be replaced later without changing the homepage template.
The browser document title and header are exactly `Ramblings` or `闲扯` on the
respective homepage; they do not duplicate or append the author's name.

Every list is language-local. English content does not appear as fallback on
the Chinese homepage, and Chinese content does not appear as fallback on the
English homepage. “Beyond the Cloud” therefore appears only on the English
homepage until an `index.zh.md` translation exists in the same project bundle.

## Project Content Model

Move the complete leaf bundle from:

`content/blog/beyond-the-cloud/`

to:

`content/projects/beyond-the-cloud/`

Add `projectStatus = "past"` to its front matter. Configure the `projects`
section with the same `/p/:contentbasename/` permalink pattern as `blog`, so
the published page and PDF remain:

- `/p/beyond-the-cloud/`
- `/p/beyond-the-cloud/beyond_the_cloud.v5.pdf`

The move must not change article body bytes, resource bytes, tags, publication
dates, `interactionId`, or page discoverability. The interaction entity remains
exactly `post:beyond-the-cloud`; changing the prefix would split existing
Giscus and Kudos state.

Posts and projects share one article-rendering partial. Thin `blog/page.html`
and `projects/page.html` templates call it, so both content types receive the
same article markup, date, tags, TOC, SEO, Giscus, and Kudos behavior without
duplicated templates.

The interaction-ID validator scans leaf bundles in both `content/blog` and
`content/projects`, enforces uniqueness across both sections, and preserves the
existing translation identity rules. The translation helper accepts either
section explicitly and retains its safe, exclusive no-overwrite behavior.

The blog archive, Latest posts, Popular posts, and home RSS feed select only
the `blog` section. Moving the bundle therefore removes “Beyond the Cloud” from
Posts and RSS by content type instead of hiding or deindexing it. Sitemap and
SEO behavior remain enabled for the project page.

The projects branch bundle disables rendering only for its section index while
remaining listable, so Hugo can select its regular project pages for homepage,
tag, and sitemap output without creating an unrequested `/projects/` archive.

## Popular-Post Ranking

Hugo emits an inert candidate record for every eligible post in the active
language. Each record contains only:

- localized title;
- base-path-safe relative permalink;
- immutable entity `post:<interactionId>`; and
- reverse-chronological fallback position.

Hidden pages, drafts, projects, and other languages are never candidates.

Runtime behavior is:

1. Zero candidates render the localized no-posts message and load no ranking
   script.
2. One candidate renders directly and loads no ranking script because sorting
   cannot change its position.
3. Two or more candidates with a valid, enabled Kudos endpoint load one
   fingerprinted ES module. It concurrently
   performs exactly one public count request per candidate:
   `GET <endpoint>/<encodeURIComponent(entity)>`.
4. The module never calls the voter-state `/:entity/kudos` endpoint, never
   writes a vote, sends no credentials, and uses `referrerPolicy: "no-referrer"`.
5. Every response must be successful JSON with the exact requested entity and
   a nonnegative safe-integer count.
6. After all responses succeed, candidates sort by count descending. Equal
   counts sort by the supplied reverse-chronological position, and the first
   five title links become visible.
7. A five-second shared timeout, network failure, non-success response,
   malformed JSON, entity mismatch, or invalid count makes the complete ranking
   unavailable. The page shows a localized temporary-unavailable message and
   never presents a partial ranking as authoritative.

When two or more candidates exist but Kudos is disabled or its endpoint fails
the existing strict configuration guard, the template emits the same localized
unavailable state and no ranking script or network request.

The initial popular-post region is marked `aria-busy="true"` and contains one
polite, atomic status message. Candidate links remain hidden and unfocusable
until the final order is known. Successful rendering clears busy state and
announces completion once; failure clears busy state and exposes the localized
failure message. A localized `noscript` message explains that live ranking
requires JavaScript. Article, project, navigation, latest-post, and tag content
remain usable regardless of Worker or script failure.

The production Worker already allows `https://allanware.github.io`. Live
ranking on `http://localhost:1313` requires that loopback origin to be added to
the Worker's `ALLOWED_ORIGINS` runtime variable; without it, the intentional
failure state appears locally.

## Tags

The Tags overview remains one alphabetical vocabulary with counts covering all
visible tagged posts and projects in the active language.

Each individual tag result page keeps its tag heading and “All tags” backlink,
then groups matching visible pages in this order:

1. Projects/项目
2. Posts/文章

An empty group is omitted. If neither group contains a visible page, the
existing localized empty state appears. The group lists retain the existing
date-and-title archive presentation and remain language-local. Search and count
controls apply independently to each rendered group only when useful, with
project-specific search, count, and empty labels rather than calling projects
“posts.”

## Configuration, Localization, and Styling

Set the language site titles in `hugo.toml` to `Ramblings` and `闲扯`. The
author's name remains in the localized introductory content, not in the site
title.

Template-owned labels and states live in both i18n catalogs. Required concepts
include Projects, Past projects, Latest posts, Popular posts, no projects,
search projects, project count, popular-post loading, popular-post unavailable,
popular-post ready, and JavaScript-required.

Homepage title lists use a dedicated semantic list style rather than the
date-oriented archive list. New CSS stays in `assets/css/site.css`; the vendored
Bear Neo theme remains unchanged. Layout must remain readable without horizontal
overflow in both color schemes and at mobile widths.

## Privacy and Performance

Homepage count requests contact the configured Cloudflare Worker, so Cloudflare
receives ordinary request metadata such as the visitor's public IP. Unlike the
article upvote control, homepage ranking makes no voter-state request and does
not ask the Worker to derive or return the visitor's voting identity. The README
must disclose this homepage behavior.

The current archive yields only two English ranking requests after the project
move and no Chinese requests. Request volume grows linearly with the number of
eligible posts. A Worker batch endpoint is intentionally deferred until the
archive is large enough for that trade-off to be worthwhile.

## Testing

Use test-driven development. Generated-site tests must cover both a root base
URL and a project-subpath base URL and assert:

- localized site titles and contact link text;
- exact homepage section order and `h2`/`h3` hierarchy;
- language-local projects and empty project state;
- latest-post reverse-date order, title-only markup, three-item limit, and
  exclusion of projects and hidden pages;
- popular candidate language/section/visibility filtering, five-item limit,
  and base-path-safe links;
- unchanged Beyond route, PDF, interaction entity, Giscus term, SEO, and tag
  membership;
- removal of Beyond from Posts and RSS;
- combined tag-overview counts and Projects-before-Posts grouping on tag result
  pages; and
- a translated project appearing only in languages with a content document.

Dependency-free Node tests must cover:

- descending count ranking;
- newest-first tie breaking;
- the five-item limit;
- exact one-time entity encoding and count-only endpoints;
- credentials/referrer request options;
- zero- and one-candidate no-fetch behavior;
- malformed payloads, HTTP errors, timeouts, and all-or-nothing failure;
- accessible loading, success, failure, and no-JavaScript states; and
- no unhandled promise rejection.

Full acceptance also requires the existing Python and Node suites, interaction
validator, actionlint, warning-fatal Hugo builds, root/project base-path
checker, and a mobile browser smoke test to pass. The untracked root migration
sources and `writings-images/` archive remain untouched and uncommitted.

## Acceptance Criteria

The work is complete when:

1. `/` is titled `Ramblings`, `/zh/` is titled `闲扯`, and neither site title
   uses the author's name.
2. Both homepages render the approved localized structure and contact link.
3. “Beyond the Cloud” is absent from Posts, Latest posts, Popular posts, and
   RSS, but remains available at its existing URL with unchanged interactions
   and resources.
4. Projects are language-local and appear above posts on tag result pages.
5. Latest posts show at most three titles; Popular posts show at most five
   titles with no visible counts.
6. Live popularity follows the exact ranking, validation, timeout, privacy, and
   failure contract above.
7. A Worker outage never removes or disables unrelated homepage content.
8. All automated and browser acceptance checks pass at root and project base
   paths without modifying the vendored theme or migration archive.
