# Wenxuan Zhao / 赵文轩

This is a multilingual Hugo blog built on a vendored copy of
[Hugo Bear Neo](https://github.com/rokcso/hugo-bearneo). English is the default
language and Simplified Chinese is available under `/zh/`. A post may be
English-only, Chinese-only, or paired in both languages.

The primary navigation intentionally has exactly Home, Posts, and Tags as its
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
content and templates for changes. Comments and upvotes are both enabled, so a
local preview does reach out to `giscus.app` and the Kudos Worker. Set
`enabled = false` under `[params.giscus]` or `[params.kudos]` to preview
without them; neither is required for reading, navigation, feeds, or authoring.

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

Every published post needs a 1–80 character lowercase ASCII `interactionId`
made from letters, numbers, and internal hyphens. It is unique to one article,
identical across that article's language files, and immutable after
publication. That shared value joins both the Giscus discussion and the Kudos
count across translations. Validate it after every content change:

```sh
python3 scripts/validate_interaction_ids.py content
```

Place shared images and downloads beside the Markdown files and link them with
bundle-relative paths without a leading slash. Images need meaningful
alternative text. To specify an authored display width, use the local
`bundle-image` shortcode.

## RSS

The site publishes one feed per language:

- English: `/index.xml`
- Simplified Chinese: `/zh/index.xml`

Each feed includes only posts available in that language. They are deliberately
not combined, so subscribing to one does not mix languages.

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
