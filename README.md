# Where Was I / 说哪儿了

This is a multilingual Hugo blog built on a vendored copy of
[Hugo Bear Neo](https://github.com/rokcso/hugo-bearneo). English is the default
language and Simplified Chinese is available under `/zh/`. A post or project
may be English-only, Chinese-only, or paired in both languages.

The primary navigation intentionally has exactly Home, Blog, and Tags as its
three destinations. English and Chinese have separate post lists and tag
vocabularies. RSS stays available through feed discovery and the footer rather
than becoming a fourth page.

The site follows the automatic browser color preference only. It has no manual
theme switch, analytics, or advertising.

## Requirements

- Hugo Extended 0.164.0, or a compatible newer release
- Python 3.11 or newer
- Node.js 22 or newer
- [actionlint](https://github.com/rhysd/actionlint) for checking the CI workflow

The test suite uses only the Python and Node.js standard libraries.

## Preview locally

Preview published content only:

```sh
hugo server
```

Include drafts while writing:

```sh
hugo server -D
```

Open the URL printed by Hugo, normally `http://localhost:1313/`. Hugo watches
content and templates for changes. Comments and upvotes are enabled: Giscus
contacts `giscus.app`, and Kudos contacts the configured Worker during this
preview. The core site stays usable if either service is unavailable. The
homepage's live ranking also requires the Kudos Worker to allow the exact
`http://localhost:1313` origin. For an external-request-free preview, use an
uncommitted local configuration override that disables both integrations.

Run the local verification suite:

```sh
python3 scripts/validate_interaction_ids.py content
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.test.mjs
actionlint .github/workflows/hugo.yml
hugo --gc --minify --panicOnWarning --noBuildLock --cleanDestinationDir \
  --printI18nWarnings --printPathWarnings --baseURL https://example.org/
python3 scripts/check_site.py public --base-url https://example.org/
```

The Python suite includes root-hosted and project-subpath build coverage. To
exercise the project path directly as well:

```sh
BLOG_PROJECT_BUILD="$(mktemp -d)"
hugo --gc --minify --panicOnWarning --noBuildLock --cleanDestinationDir \
  --printI18nWarnings --printPathWarnings \
  --baseURL https://example.github.io/example-blog/ \
  --destination "$BLOG_PROJECT_BUILD"
python3 scripts/check_site.py "$BLOG_PROJECT_BUILD" \
  --base-url https://example.github.io/example-blog/
```

## Write a post

Posts are multilingual leaf bundles below `content/blog/`. The language suffix
is part of the page filename:

```text
content/blog/my-post/
├── index.en.md
├── index.zh.md
└── shared-image.jpg
```

A standalone post has only the language file that actually exists. A paired
post places `index.en.md` and `index.zh.md` in the same bundle, where they share
images and downloads. Never add a placeholder translation.

Create an English draft:

```sh
hugo new content --kind blog content/blog/my-post/index.en.md
```

The `blog` archetype generates the title, `date`, `lastmod`, `draft = true`, an
empty tag list, an `interactionId` derived from the bundle slug, and an H2 body
starter. Confirm the title and ID, add tags, and set `draft = false` only when
the post is ready. `date` is the original publication date and `lastmod` is the
latest substantive update.

Hugo can create a second language file inside an existing leaf bundle. For a
real translation, use this project's helper instead so the new file is an
exact copy of the source and keeps its identity:

```sh
python3 scripts/new_translation.py my-post en zh
```

The helper preserves the source `interactionId` and refuses to overwrite an
existing target. It also rejects path traversal, unknown languages, and copying
a language onto itself. After copying, translate the title and body and choose
Chinese tags independently, but do not change `interactionId`.

To translate in the other direction, reverse the language arguments. To create
a Chinese-only post, scaffold only its Chinese file:

```sh
hugo new content --kind blog content/blog/chinese-only/index.zh.md
```

Every published post or project needs an immutable, shared 1–80 character
lowercase ASCII `interactionId` made from letters, numbers, and internal
hyphens. It must be unique across `content/blog/` and `content/projects/`, and
identical in every translation of the same entry. Giscus and Kudos both use
that shared value across translations. Validate it after every content change:

```sh
python3 scripts/validate_interaction_ids.py content
```

Place shared images and downloads beside the Markdown files and link them with
bundle-relative paths without a leading slash. Markdown images support three
forms: `![](image.jpg)` for a decorative image with no caption,
`![Alternative text](image.jpg)` for a described image with no visible caption,
and `![Alternative text](image.jpg "Caption")` for a described image with a
visible caption. Use empty alternative text only when the image is decorative.
To specify an authored display width, use the local `bundle-image` shortcode.

## Interactive Go boards

Use Sabaki to add variations, SGF node comments, and standard board marks. Save
the `.sgf` file beside `index.en.md` and `index.zh.md` in the post's leaf
bundle. Paired translations share the same SGF asset; do not duplicate it.

[Authoring a Go review](docs/go-review-authoring.md) is the step-by-step
workflow for game reviews: the Sabaki pass, the record naming rules, how prose
divides between Markdown and SGF comments, and the pre-publish checklist.

Embed a position with the local shortcode:

```go-html-template
{{< go-board src="game.sgf" move="64" caption="Position after move 64." >}}
```

`src` and `caption` are required. The source must be a bundle-relative `.sgf`
file, and the caption must not be empty. With no selector, the board defaults to
move 0. The beginner-friendly `move` selector is a semantic mainline move count
and skips non-move nodes. An exact `path` starts at the authored first SGF node.
`N` advances through that many first-child node transitions and counts all
nodes, not moves; `B` chooses the 1-based child at the current node. `N0` keeps
the authored root, including its move if the root itself contains one. `move`
and `path` are mutually exclusive.

For example, this selects the second continuation after move 64 in the bundled
review record:

```go-html-template
{{< go-board src="2026-7-26.sgf" path="N64B2" caption="Second continuation after move 64." >}}
```

Three useful patterns cover most posts:

- To compare branches, create variations in Sabaki. The viewer adds contextual
  A/B buttons and matching board labels automatically.
- To discuss one point, use the standard `CR`, `TR`, `SQ`, `MA`, `LB`, and `SL`
  marks for circles, triangles, squares, crosses, labels, and selections.
- To show a sequence, record it as a branch so readers can step through it.

Supported SGF properties are moves (`B`/`W`), setup stones and removals
(`AB`/`AW`/`AE`), those standard marks, and `C` node comments. SGF `C` comments
are rendered as plain text; Markdown is not formatted there. Put the main
translated explanation in the Markdown post. Because translations share one
record, SGF notes should be language-neutral, bilingual, or omitted.

The viewer does not display Sabaki arrows and lines or custom engine values
such as `SBKV` and `SBKS`. It also ignores node titles (`N`) and Sabaki's move
and position judgements, so put any verdict in the comment itself.

Readers get one compact control row: Previous, the move number, Next,
contextual A/B variation buttons, and a Try toggle. The current node comment
sits below that row and is the viewer's main prose surface. Try discloses a
single coordinate field, so a move can be played by typing a point such as `D4`
and pressing Enter, or by clicking the board. Try is local and
ephemeral, with no persistence; leaving Try discards the tried moves and puts
the reader back on the position they entered it from. With focus on the board,
the arrow keys step one move and Home and End jump to the published position
and the end of the current line.

The board viewer itself makes no third-party requests. Existing Giscus remains
the post-level comment system. Durable move-level multi-user discussion is
deferred to a separate app or backend.

The implementation uses a [pinned, trimmed BesoGo runtime](assets/vendor/besogo/UPSTREAM.md)
under its [MIT license](assets/vendor/besogo/LICENSE).

## RSS

The site publishes one feed per language:

- English: `/index.xml`
- Simplified Chinese: `/zh/index.xml`

Each feed includes only posts available in that language. They are deliberately
not combined, so subscribing to one does not mix languages.

## Content model

The English site is named **Where Was I** and the Simplified Chinese site is
named **说哪儿了**. Blog leaf bundles live under `content/blog/<slug>/`, while
project leaf bundles live under `content/projects/<slug>/`; each language file
is named `index.en.md` or `index.zh.md`. A project with
`projectStatus = "past"` appears in the homepage Projects/Past section only for
the languages whose files actually exist in its bundle.

Create a project translation with the same copy-first helper used for posts:

```sh
python3 scripts/new_translation.py <slug> en zh --section projects
```

Translate the copied title and body, but keep its `interactionId` unchanged.
Never create a placeholder language file merely to make a project appear in
another language.

## Popular posts

The homepage ranks only published, visible blog posts in the active language.
When at least two candidates exist, it sends one count-only
`GET /<encoded-entity>` request per candidate to the Kudos Worker, waits for all
responses, and lists at most five titles in descending Kudos order. This
ranking never requests voter state and never displays vote counts.

Cloudflare receives ordinary request metadata, including the visitor's public
IP, for these requests. A timeout, network failure, or invalid response affects
only the Popular posts region; the rest of the homepage remains usable. The
production Worker CORS configuration should allow the exact origin
`https://allanware.github.io`. Local ranking at the normal Hugo URL requires
the exact origin `http://localhost:1313` to be allowed as well.

## Comments

[Giscus](https://giscus.app) backs comments with public GitHub Discussions.
Its settings live under `[params.giscus]` in `hugo.toml`, and the comment
section disappears if `enabled = false` or any value is blank. Mapping is
strict `specific` on `post:<interactionId>`, so paired translations share one
bilingual thread.

Reading comments contacts `giscus.app`; posting one requires a GitHub account.
Giscus can be slow or unreachable in mainland China, and any failure there
affects only the comment region, never the article or navigation.

## Upvotes

Kudos provides registration-free upvotes from a Cloudflare Worker backed by a
D1 database, since static hosting cannot serve its mutable API. The Worker
origin is set in `[params.kudos].endpoint` in `hugo.toml`. The integration was
reviewed at [Kudos v0.2.0](https://github.com/puinoib/kudos/releases/tag/v0.2.0),
[commit b449185](https://github.com/puinoib/kudos/commit/b449185be66d239555bf1242fec1169a0a09517f);
redeploying follows that commit's
[pinned guide](https://github.com/puinoib/kudos/blob/b449185be66d239555bf1242fec1169a0a09517f/docs/deployment.md)
— create the D1 database, pass `D1_DATABASE_ID` as a build-time variable rather
than a runtime secret, then run `pnpm run deploy`. The Worker's optional
`ALLOWED_ORIGINS` variable is browser CORS policy, not authentication; when it
is unset, the upstream default is open CORS.

Loading a post sends count and voter-state requests, so Cloudflare receives
ordinary request metadata including the visitor's public IP. The Worker stores a
SHA-256-derived voting identity rather than the raw IP, so visitors sharing one
public IP may share voting state. Both languages share a single
`post:<interactionId>` count, and a Worker outage disables only the upvote
control.

No analytics or advertising scripts are included. Giscus and Kudos are the only
third-party requests.
