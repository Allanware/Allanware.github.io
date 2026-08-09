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
- [actionlint](https://github.com/rhysd/actionlint) for checking the Pages workflow

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
content and templates for changes. Giscus and Kudos are disabled until their
external settings are complete, so neither service is required for local
reading, navigation, feeds, or authoring.

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

## GitHub Pages

This repository is ready for GitHub Pages but does not configure or push to a
remote repository on its own. After pushing it to a public GitHub repository:

1. Open **Settings → Pages** in that repository.
2. Under **Build and deployment**, select **GitHub Actions** as the source.
3. Push the default branch or run the workflow manually.

The workflow uses GitHub's configured Pages base URL with a trailing slash, so
both user sites and repository project sites retain the correct internal path.
It tests all branches but deploys only the actual default branch or a manual
run. The Bear Neo source is vendored, so checkout does not use submodules. The
uploaded artifact includes the hidden `.nojekyll` marker.

## Giscus comments

[Giscus](https://giscus.app) is a free, ad-free comment interface backed by
public GitHub Discussions. It remains hidden until every value under
`[params.giscus]` in `hugo.toml` is set and `enabled = true`.

Before enabling it, the eventual public repository needs Discussions enabled,
the Giscus GitHub App installed, and a Discussion category selected. Copy the
repository, repository ID, category, and category ID generated by giscus.app
into `hugo.toml`. The template uses strict `specific` mapping with
`post:<interactionId>`, so paired translations share one bilingual Discussion
thread.

Reading comments contacts the third-party `giscus.app`. Writing a comment and
authentication require a GitHub account. Giscus can be slow or unreachable in
mainland China; an outage, blocked request, or authentication failure affects
only the comment region and never the article or navigation.

## Registration-free Kudos

Kudos is the optional, registration-free upvote backend. This integration was
reviewed at upstream
[Kudos v0.2.0](https://github.com/puinoib/kudos/releases/tag/v0.2.0), specifically
[commit b449185be66d239555bf1242fec1169a0a09517f](https://github.com/puinoib/kudos/commit/b449185be66d239555bf1242fec1169a0a09517f).
GitHub Pages cannot host its mutable API, so activation requires a separate
Cloudflare Worker and D1 database. Follow the inspected commit's
[pinned deployment guide](https://github.com/puinoib/kudos/blob/b449185be66d239555bf1242fec1169a0a09517f/docs/deployment.md):

1. Fork that inspected Kudos release and install the guide's dependencies.
2. Create a Cloudflare D1 database.
3. Supply `D1_DATABASE_ID` as the build/deploy environment variable used to
   generate the Worker's D1 binding; it is not a Worker runtime secret.
4. Deploy the fork with the guide's `pnpm run deploy` command.
5. Optionally set `ALLOWED_ORIGINS` as a Worker runtime variable containing the
   final Pages or custom-domain origin and any loopback preview origin used for
   testing. When it is unset, the upstream default is open CORS.
6. Put the resulting Worker origin in `[params.kudos].endpoint` in `hugo.toml`
   and set `enabled = true`.

`ALLOWED_ORIGINS` is browser CORS policy, not authentication or authorization.
Use a credential-free HTTPS root origin in production, with no path beyond an
optional trailing slash and no query or fragment. Plain HTTP is accepted only
for `localhost` or `127.0.0.1` local testing.

When Kudos is enabled, loading a post sends count and voter-state requests to
the Worker. Cloudflare therefore receives ordinary request metadata, including
the visitor's public IP. The reviewed Worker stores a SHA-256-derived voting
identity rather than the raw IP. People sharing one public IP may consequently
share voting state. Both languages use the same `post:<interactionId>` entity
and count. A Worker failure disables only the upvote control.

No analytics or advertising scripts are included. Giscus and Kudos are the
only optional third-party requests.

## Source migration archive

The three root Markdown files and `writings-images/` remain untouched migration
inputs. Hugo publishes only resources copied into `content/blog/` leaf bundles.
