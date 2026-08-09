# Bear Neo Multilingual Blog Design

**Date:** 2026-08-08
**Status:** Approved — reconciled 2026-08-08 after implementation-plan review (see §18)
**Site owner:** Wenxuan Zhao / 赵文轩

## 1. Objective

Convert the existing collection of three Markdown posts into a locally runnable Hugo site based on the Bear Neo theme, with optional English and Simplified Chinese versions of each post. The site will be ready for later deployment to GitHub Pages and will support automatic light/dark appearance, language-specific RSS feeds, Giscus comments, and registration-free Kudos upvotes.

The initial deliverable is a complete local Hugo site, including a documented workflow for writing new posts in either language. GitHub- and Cloudflare-dependent features will be wired into the site but will remain hidden until their required public identifiers or endpoint are configured.

## 2. Current State

Verified against the workspace and the upstream theme on 2026-08-08.

The workspace is not a Git repository and contains:

- `beyond-the-cloud.md`
- `lekythos-a-shape.md`
- `the-miracle-of-istanbul.md`
- `writings-images/`, containing the posts' source images, a poster PDF, and the original R Markdown source for the Istanbul post
- `.DS_Store` files at the root and inside `writings-images/`

All three current posts are English-only. Their front matter uses legacy fields such as `published_at` and `type: writing`, their body repeats the front-matter title as an H1, and their media paths (`../../_media/writings-images/…`) do not resolve in Hugo's intended structure.

All 25 resources referenced by the three Markdown sources are present: 23 images, one poster PDF, and one R Markdown source file. The Istanbul post accounts for 20 images plus the R Markdown file (21 resources, not 21 images). Two additional images, `cover.png` and `3-3.jpeg`, are referenced by none of the posts.

Hugo Extended 0.164.0 is installed locally (`hugo v0.164.0+extended+withdeploy darwin/arm64`). The pinned Bear Neo revision is commit `f5c57c5ea39a091f0167af6312f4d4e385df2e6c` ("Fix RSS configuration example in README docs") of `https://github.com/rokcso/hugo-bearneo`, MIT licensed. The theme declares a minimum of Hugo 0.110.0, so the installed version is compatible.

The theme's shape constrains the work and is recorded here because several requirements depend on it:

- It contains **no `i18n/`, `assets/`, or `static/` directory**. All user-visible interface text is hardcoded English inside templates, and the entire stylesheet lives in `layouts/partials/style.html` (~12 KB).
- `layouts/` holds `404.html`, `index.html`, `robots.txt`, `_default/{baseof,list,rss.xml,single}.html`, `_default/_markup/`, and ten partials: `custom_body`, `custom_head`, `favicon`, `footer`, `header`, `mermaid`, `nav`, `seo_tags`, `style`, `toc`. There is **no `terms.html`**, so taxonomy pages fall back to `list.html`.
- `custom_head.html` and `custom_body.html` are empty, user-overridable injection hooks.
- Dark mode is implemented solely with `@media (prefers-color-scheme: dark)` over CSS custom properties. There is no toggle, no `data-theme` attribute, and no `localStorage` use. The stylesheet declares neither `color-scheme` nor `theme-color`.
- The primary font stack is `--font-primary: Verdana, sans-serif` with **no CJK fallback**.
- `baseof.html` emits `<html lang="{{ with .Site.LanguageCode }}{{ . }}{{ else }}en-US{{ end }}">`.
- `nav.html` hardcodes both the label and the URL of its two links: `<a href="{{ "" | relURL }}">Home</a>` and `<a href="{{ "blog/" | relURL }}">Blog</a>`. `relURL` does not add a language prefix.
- `footer.html` hardcodes root-absolute paths `/index.xml` and `/sitemap.xml`, plus the English strings "Subscribe via", "say hello", and "Made with".
- `list.html` hardcodes `Filtering for "…"`, `Remove filter`, `Search…`, `There is/are N piece/pieces.`, and `No posts yet`, formats dates with `.Date.Format` (which is not locale-aware), and contains a `range .Site.Taxonomies.tags` tag-cloud loop.
- `single.html` derives the upvote entity key from the page's `RelPermalink`, defaulting to `home`, with the Kudos JavaScript inline in the template.
- The theme's own example configuration sets `disableKinds = ["taxonomy"]` and `tags = "/blog/:slug"`, i.e. Bear Blog convention: tag term pages live under `/blog/<tag>/` and **there is no tag overview page at all**.
- Supported params include `upvote`, `upvoteURL`, `postSearch`, `groupByYear`, `showPostCount`, `toc`, `imageZoom`, `externalLinksNewTab`, `dateFormat`, `favicon`, `shareImage`, `copyright`, `Author.email`, `params.RSS.*` (its example uses 10 items; an unset limit is unlimited), and `params.footer.hide*`. The theme has **no comment-system support of any kind**.

## 3. Scope

### Included

- A standard Hugo project rooted in this workspace, initialized as a local Git repository with an appropriate `.gitignore`.
- A vendored, pinned Bear Neo theme snapshot with its upstream license and revision recorded.
- Migration of all three existing posts and every media file they reference.
- English and Simplified Chinese site structure with independently optional post translations.
- Localized site chrome and post controls, added on top of a theme that ships no translation support.
- A tag overview page in each language, which diverges deliberately from the theme's default URL scheme.
- Automatic browser/OS light and dark color matching, with no manual theme control.
- A CJK-capable font stack and Hugo's CJK content settings.
- Per-language RSS feeds and multilingual sitemap/SEO metadata.
- Giscus comments configured to share a discussion between translations.
- Bear Neo/Kudos upvotes configured to share a count between translations.
- A GitHub Actions workflow suitable for GitHub Pages.
- A documented authoring workflow for new posts and new translations.
- Local build, preview, and verification instructions.

### Not included

- Machine-translating the three existing English posts or creating placeholder Chinese copies.
- Creating or mutating a remote GitHub repository, enabling GitHub Discussions, installing the Giscus GitHub App, or choosing a Discussion category without the user's repository details and authorization.
- Forking or deploying Kudos into the user's GitHub and Cloudflare accounts without separate authorization and authenticated access.
- Anonymous text comments, a self-hosted comment backend, moderation tooling beyond Giscus, analytics, advertising, or a manual color-theme toggle.
- A browser-based CMS or admin interface.
- Rewriting the substance of the existing articles.

## 4. Project and Theme Architecture

The project will use Hugo 0.164's current template layout while keeping the vendored theme immutable:

```text
.
├── assets/
│   ├── css/site.css               # focused additions layered over Bear Neo
│   └── js/                        # title search and testable Kudos client
├── archetypes/
│   └── blog.md                    # scaffolds new posts, including interactionId
├── content/
│   ├── _index.en.md
│   ├── _index.zh.md
│   └── blog/
│       ├── _index.en.md
│       ├── _index.zh.md
│       └── <post-slug>/
│           ├── index.en.md
│           ├── index.zh.md        # only when a Chinese version exists
│           └── <shared assets>
├── i18n/
│   ├── en.toml
│   └── zh.toml
├── layouts/                       # current Hugo template types and focused partials
├── scripts/                       # identity and generated-site verification
├── tests/                         # unit, fixture-build, and browser-facing contracts
├── themes/hugo-bearneo/           # vendored pinned snapshot
├── .github/workflows/hugo.yml
├── .gitignore
├── README.md
└── hugo.toml
```

The theme will be copied into `themes/hugo-bearneo` without nested Git metadata. Its `LICENSE` will be preserved, and a provenance note will record the upstream repository and exact commit.

`.gitignore` will cover `public/`, generated Hugo resources, `.hugo_build.lock`, `.DS_Store` at any depth, Python bytecode/cache directories, and local test artifacts. A source-controlled `static/.nojekyll` will be included in the Pages artifact.

### 4.1 Customization strategy

The theme ships no translation layer and its upstream templates use older layout paths and hardcoded English URLs. The site will therefore use a focused site-local renderer layer built with Hugo 0.164's current template types (`layouts/_partials`, `layouts/_markup`, `home.html`, `blog/page.html`, `blog/section.html`, `taxonomy.html`, and `term.html`). This is broader than injection hooks alone, but it avoids deprecated language configuration and keeps behavior explicit and testable. The vendored theme remains a pristine stylesheet/partial source and can be upgraded by replacing one directory.

Site-local templates must use `locale`, `label`, `direction`, `.Language.Locale`, `.Language.Label`, and `.Language.Direction`; they must not reintroduce deprecated `languageCode` or `.Site.LanguageCode`. Templates that reproduce or replace behavior from Bear Neo must carry a one-line provenance comment naming upstream commit `f5c57c5ea39a091f0167af6312f4d4e385df2e6c`. Wholly new templates may instead be marked as site-local.

### 4.2 Override inventory

| Project file | Purpose |
| --- | --- |
| `layouts/baseof.html` | Language-aware document shell, strict cross-origin referrer policy, and current-language RSS discovery |
| `layouts/home.html`, `layouts/blog/{section,page}.html` | Localized home, Posts list, and post rendering |
| `layouts/taxonomy.html`, `layouts/term.html` | Localized tag overview and term archives |
| `layouts/home.rss.xml`, `layouts/sitemap.xml` | Language-specific feeds and real-translation sitemap alternates |
| `layouts/_partials/{header,nav,footer,toc,post-list}.html` | Localized chrome, an RSS-only footer, exactly three primary destinations, dates, counts, and title-only search |
| `layouts/_partials/{seo_tags,interaction-id,giscus,kudos}.html` | Canonical/alternate metadata and guarded shared interactions |
| `layouts/_markup/{render-image,render-link}.html` | Resolve URL-decoded bundle-resource paths, preserve authored query/fragment suffixes, and give translations one canonical asset URL |
| `layouts/_shortcodes/bundle-image.html` | Preserve explicit accessible image widths while reusing the same zoom/resource behavior |
| `layouts/_partials/custom_head.html`, `assets/css/site.css` | Automatic color metadata, CJK font fallback, focus states, and small style refinements |
| `i18n/en.toml`, `i18n/zh.toml` | All interface strings |

The image and link render hooks parse the authored destination, use its URL-decoded path for `.Page.Resources.Get`, and emit the matched resource's `.RelPermalink` followed by the untouched raw query and fragment. Falling back to the original destination is allowed only for non-page-resource URLs. This makes percent-encoded filenames such as `my%20diagram.svg`, query-bearing downloads, and fragments such as `#minipic` resolve without losing authored suffixes. It also deliberately uses Hugo's canonical default-language resource permalink from either translation, because Hugo normally publishes a shared multilingual bundle resource once rather than duplicating it beneath every language prefix.

The existing root Markdown and `writings-images` files are source material. Migration copies their publishable content into the Hugo structure; the originals are not deleted during this work. They sit outside `content/` and `static/`, so Hugo will not publish them.

## 5. Multilingual Content Model

English is the default language and is served without a language prefix. Simplified Chinese is served beneath `/zh/`.

```text
English home:  ./
Chinese home:  ./zh/
English posts: ./blog/
Chinese posts: ./zh/blog/
English tags:  ./tags/
Chinese tags:  ./zh/tags/
English post:  ./p/<slug>/
Chinese post:  ./zh/p/<slug>/
```

These are logical paths relative to the site's configured base URL. They resolve at the host root for a user/organization Pages site or custom domain, and beneath `/<repository>/` for a GitHub project site. Templates and content must use Hugo URL functions or page/resource links rather than hardcoded host-root URLs. `relLangURL` is required wherever a link must stay inside the current language.

### 5.1 Required configuration

| Setting | Value | Why |
| --- | --- | --- |
| `defaultContentLanguage` | `en` | English is primary |
| `defaultContentLanguageInSubdir` | `false` | English served at the root |
| `languages.en.locale` | `en-US` | English regional locale for document metadata, dates, feeds, and `hreflang` |
| `languages.zh.locale` | `zh-CN` | Simplified Chinese locale for document metadata, dates, feeds, and `hreflang` |
| `languages.*.label`, `languages.*.direction` | localized label, `ltr` | Current Hugo language-switch and document-direction metadata |
| `languages.zh.hasCJKLanguage` | `true` | Without it Hugo miscounts words and truncates Chinese summaries incorrectly |
| `capitalizeListTitles` | `false` | Preserve author-supplied tag spelling and capitalization in term labels |
| `disableKinds` | *taxonomy removed* | The theme disables it; the tag overview requires it |
| `permalinks` (posts) | `/p/:contentbasename/` | Ties each route to its leaf-bundle directory; `:slug` falls back to a title-derived value when `slug` front matter is absent |
| `permalinks` (tags) | *none — entry deleted* | Hugo's default term URL is already `/tags/<term>/`; the theme's `/blog/:slug` override is what breaks it |
| `params.kudos.enabled`, `params.kudos.endpoint` | disabled/empty until configured | §11 |
| `params.postSearch`, `groupByYear`, `showPostCount` | `true` | Defines the Posts page behavior |
| `params.toc`, `imageZoom` | `true` | Retained theme features |
| `params.externalLinksNewTab` | `false` | Preserve normal browser navigation; readers choose whether to open a new tab |
| `services.rss.limit` | `10` | Make the accepted site feed cap explicit with Hugo's current service setting |
| `params.Author.email` | unset unless requested | The footer degrades to an RSS-only line |
| `params.favicon`, `params.shareImage` | set, or the partial suppressed | Avoids 404s for theme defaults |

No permalink pattern is configured for tags at all. Hugo's default term URL is `/<taxonomy>/<term>/`, which yields exactly the required `/tags/<term>/` and `/zh/tags/<term>/`; the theme's inherited `tags = "/blog/:slug"` is deleted rather than replaced. Should a custom pattern ever be needed, current Hugo keys the map form by page kind (`[permalinks.term]`) rather than using the flat table the theme inherited.

### 5.2 Translations and bundles

Hugo's filename-based translations inside shared leaf bundles will be used:

```text
content/blog/example/index.en.md
content/blog/example/index.zh.md
content/blog/example/diagram.png
```

This model gives translated pages the same bundle and shared media while allowing either language file to be omitted. A post that exists only in Chinese will appear only in Chinese lists and feeds; an English-only post will appear only in English lists and feeds. No empty translation page will be generated.

Because the post permalink uses `:contentbasename`, translations in one bundle share the bundle-directory route: `/p/example/` and `/zh/p/example/`. Per-language `slug` front matter does not alter this route and is not supported by this design. Shared resources are resolved through the resource-aware image and link hooks from §4.2; a Chinese translation may legitimately link to the resource's canonical English bundle URL when Hugo publishes only one copy.

### 5.3 Interaction identity

Every post will have a stable, language-neutral `interactionId` in front matter. Translation files for the same article must use the same ID. That ID is independent of the URL and keys both Giscus and Kudos. Without it, the theme's `RelPermalink`-derived key would split each article's upvote count into separate English and Chinese tallies. Initial values are:

| Post | `interactionId` |
| --- | --- |
| Beyond the Cloud | `beyond-the-cloud` |
| Shapes and Functions of the Lekythos | `lekythos-a-shape` |
| The Miracle of Istanbul | `the-miracle-of-istanbul` |

`interactionId` is an immutable identifier of 1–80 lowercase ASCII letters, numbers, or internal hyphens, matching `^[a-z0-9]+(?:-[a-z0-9]+)*$`. Every published post must define it in that page's own front matter; site- or language-level parameter fallback never satisfies this requirement. A draft may omit it while being written. Templates never silently create language-specific identities.

Validation is split by cost:

- **Every direct Hugo build and `hugo server` render**, via `errorf` in a value-returning partial: published-page presence, string type, length, format regex, and equality across every page in a translation set. The partial has exactly one final `return`, as required by current Hugo. Malformed or mismatched content is tested with dedicated fixtures that must fail the Hugo command.
- **Verification script**: uniqueness across bundles, i.e. the same `interactionId` must never appear outside a single bundle directory. A small standard-library parser expresses this more clearly than template logic and produces actionable file paths.

### 5.4 Front matter mapping

The legacy fields are normalized exactly as follows. `type: writing` is dropped deliberately: Hugo uses `type` for layout lookup, and leaving it in place makes every post resolve its template through a nonexistent `writing` type.

| Legacy field | Action |
| --- | --- |
| `title` | Keep |
| `published_at` | Rename to `date` |
| `updated` | Rename to `lastmod` |
| `created` | Drop (identical to `published_at` in all three posts) |
| `type: writing` | **Drop** |
| `status: published` | Drop; draft state is expressed by `draft` |
| `tags` | Keep verbatim, including author-supplied capitalization; do not rewrite display labels solely for URL normalization |
| `related: []` | Drop |
| `source:` | Drop |
| — | Add `interactionId` |

Existing publication and update dates are preserved. Page body H1 headings that duplicate the rendered title are removed.

## 6. Initial Content Migration

The initial posts remain English-only:

- `content/blog/beyond-the-cloud/index.en.md`
  - Preserve the title, abstract, author links, dates, and tags.
  - Copy `beyond_the_cloud.v5.pdf` into the bundle.
  - Replace the invalid PDF-as-image markup (`![poster](…v5.pdf)`) with an accessible page-resource download/view link resolved by the resource-aware link hook.
  - Demote the article's `Abstract` and `Poster` headings from H1 to H2 after removing the duplicate title H1, preserving one valid document title and useful TOC hierarchy.
- `content/blog/lekythos-a-shape/index.en.md`
  - Preserve the essay, citations, footnotes, dates, and tags.
  - Copy `front.jpeg`, `detail.jpeg`, and `inner.jpg` into the bundle.
  - The three images are raw `<img>` tags carrying explicit `width` values of 400, 400, and 200 pixels. Plain Markdown image syntax cannot express width, and enabling `markup.goldmark.renderer.unsafe` site-wide to keep raw HTML is a heavier concession than the problem warrants. A small project-level `bundle-image` shortcode taking `src`, `alt`, and `width` will resolve the page resource, render accessible image markup, preserve those exact widths, and reuse the theme-compatible image-zoom treatment.
- `content/blog/the-miracle-of-istanbul/index.en.md`
  - Preserve the article text, R code samples, dates, and tags.
  - Copy the 20 referenced images (`timeline.png` and 19 `unnamed-chunk-*.png`) into the bundle and rewrite links as bundle-relative paths.
  - Copy the linked `.Rmd` file into the bundle as a downloadable page resource. It remains source code and is not rendered as a Hugo content page.

`cover.png` and `3-3.jpeg` are referenced by none of the three Markdown sources and will not be published. If a social preview image is wanted later, the theme's `params.shareImage` accepts one. No other unreferenced file in `writings-images` is published merely because it is present.

## 7. Localized Interface and Navigation

The site title will be localized:

- English: `Wenxuan Zhao`
- Chinese: `赵文轩`

All interface strings move into `i18n/en.toml` and `i18n/zh.toml`: navigation, post lists, search, empty results, table of contents, dates, RSS, comments, and upvotes. English plural strings such as `There are N pieces.` use Hugo's `one`/`other` forms; the Chinese translations are count-invariant. The footer contains only the localized current-language RSS link; the visible Bear Neo attribution and sitemap link are intentionally omitted.

Dates use the page language's locale through `time.Format`. Go's `.Date.Format`, which the theme uses, emits English month names regardless of language and is replaced wherever a date is rendered.

### 7.1 Navigation

The primary navigation contains exactly three destinations in each language. The theme's hardcoded "Home" and "Blog" links are removed in the shadowed `nav.html`; all three entries are language-scoped menu definitions resolved with `relLangURL`.

| English label | Chinese label | English logical path | Chinese logical path |
| --- | --- | --- | --- |
| Home | 首页 | `./` | `./zh/` |
| Posts | 文章 | `./blog/` | `./zh/blog/` |
| Tags | 标签 | `./tags/` | `./zh/tags/` |

RSS remains available through feed-discovery metadata and a secondary footer link rather than becoming a fourth primary-navigation destination.

Each language's navigation points to pages in that language. On a post, the language switch renders only when Hugo reports a real translation, and links directly to the corresponding translated post. On home and section pages, both language homes/sections are available. A post with no counterpart displays no language link, rather than a misleading link that redirects to a homepage.

The home pages are minimal localized landing pages for the site owner and link to the corresponding Posts page; no biography or other personal claims will be invented.

The Posts page is the `blog` section list with year grouping, post counts, and client-side title-only search enabled. Each list item exposes its title so dates and other metadata do not accidentally become searchable, and the client applies locale-neutral lowercase matching rather than reader-locale-sensitive casing; for example, `istanbul` continues to match `Istanbul` in a Turkish-locale browser. Hugo scopes `.Pages` and `.Site.Taxonomies` per language, so each language's list and search cover only its own posts.

### 7.2 Tags

Tag vocabularies are **independent per language**. A Chinese post tags itself with Chinese terms; there is no shared key and no cross-language tag equivalence. `/tags/` lists the English tags, `/zh/tags/` lists the Chinese tags, and each term page lists only posts in its own language and links only within that language.

An identical visible tag label in both languages is treated as a coincidence, not a declared translation. Term pages therefore never emit cross-language switches or `hreflang` relationships; post, home, and section translations retain their normal language relationships.

Consequences accepted with this choice:

- Chinese term paths contain CJK characters, which browsers display as Chinese and transmit percent-encoded (`/zh/tags/希腊/` → `/zh/tags/%E5%B8%8C%E8%85%8A/`). Static hosting on GitHub Pages serves these correctly.
- CJK directory names are created under `public/`. Git's `core.precomposeunicode` (default `true` on macOS) must remain enabled so macOS NFD filenames are not committed in a form Linux CI resolves differently.
- A reader following a tag cannot cross to the other language's equivalent topic, because no such relationship is declared.

Delivering `/tags/` at all is a deliberate divergence from the theme, which disables the taxonomy kind and routes term pages to `/blog/<tag>/`. Implementation therefore removes `taxonomy` from `disableKinds`, deletes the inherited tag permalink so Hugo's default `/tags/<term>/` applies, and adds the current `layouts/taxonomy.html` template, since the theme has no dedicated term-overview renderer. The tag-cloud behavior in the theme's `list.html` informs the site-local template.

The document's `lang` attribute and accessible labels follow the current page language.

## 8. Appearance

Bear Neo's `prefers-color-scheme` styling remains the source of truth. It already matches the requirement: automatic, with no toggle and no stored preference. The site will:

- Follow the browser/operating-system light or dark preference automatically.
- Provide no manual toggle and store no appearance preference.
- Declare support for both schemes with `color-scheme` metadata/CSS, which the theme does not emit.
- Provide light- and dark-specific `theme-color` metadata, which the theme does not emit.
- Ask Giscus to use `preferred_color_scheme`, keeping its embedded interface synchronized with the page.

The theme's `--font-primary: Verdana, sans-serif` contains no CJK glyphs, so Chinese text would fall back to per-glyph browser substitution and render inconsistently. A system CJK chain is appended, using fonts already present on each platform rather than a web-font download: `Verdana, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif`. Chinese prose receives a tested line-height suited to CJK glyphs. Letter spacing remains normal unless the visual pass demonstrates a concrete readability problem; arbitrary CJK tracking will not be added. These additions live in the small site stylesheet loaded by `custom_head.html`, so the theme's 12 KB `style.html` is not shadowed.

Both schemes must preserve readable text, link, focus, code-block, and upvote states, in both scripts. The site overrides only the light-scheme tertiary and upvoted tokens (`#707070` and `#b9473a`) so their effective contrast against the light background is at least 4.5:1; Bear Neo's dark values (`#a0a0a0` and `#ff6b6b`) remain unchanged and also meet that threshold. An upvoted button fills its previously outlined icon with the current color, adding a solid-shape cue so the pressed state is not communicated by color alone.

## 9. RSS and Sitemap

The site exposes independent language feeds, relative to the configured base URL:

- English: `/index.xml`
- Chinese: `/zh/index.xml`

Each feed filters to blog posts available in that language and uses localized site metadata. Posts with `hidden = true` are removed before publish-date sorting and limiting. Feed-discovery links and visible RSS links point to the current language's feed; the theme's hardcoded `/index.xml` in the footer would otherwise send Chinese readers to the English feed and break subpath hosting. The explicit `[services.rss] limit = 10` setting is applied after sorting in the custom feed template. Summary text is HTML-unescaped and then XML-escaped exactly once so literal entities remain well formed without double escaping. No combined bilingual feed will be created. With the initial English-only content, the Chinese feed is valid but has no post entries.

Hugo will generate a multilingual sitemap index and language-specific sitemap entries for search engines and deployment checks, but the sitemap is not linked visibly from the footer.

Canonical and alternate-language metadata are emitted only for pages that actually exist and are not marked `hidden = true`. A generated hidden page emits one `robots` `noindex` directive and omits its own canonical and all `hreflang` alternates. Visible translation pairs receive reciprocal `hreflang` links; unpaired posts do not claim a nonexistent or hidden alternate. For a translation set containing visible English, `x-default` points to the English page; a Chinese-only post has only its canonical URL. Term pages are excluded from alternate metadata because equal tag spelling does not declare semantic equivalence across the independent vocabularies, and hidden-only terms are omitted from the sitemap.

## 10. Giscus Comments

Giscus is the only text-comment system in scope. It was selected knowing its two costs: **every commenter needs a GitHub account**, and `giscus.app` can be slow or unreachable for readers in mainland China. In exchange it requires no backend, no database, no spam filtering, and no moderation tooling. The guarded loader lives in `_partials/giscus.html` and is composed only by `blog/page.html`, so replacing it later touches one integration partial.

It requires a public GitHub repository, GitHub Discussions, the Giscus App, and a chosen Discussion category. Site configuration will expose these values without hardcoding them into theme files. The guarded loader requires the Giscus container to be a map, a real boolean enabled flag, and string values; it trims every required string, accepts `repo` only as one non-whitespace `owner/name` pair, derives the supported interface locale from the page language, and suppresses the widget when any required value is empty, mistyped, or malformed:

- repository name
- repository ID
- category name
- category ID
- enabled state

The theme has no comment support, so this is entirely site-local code. The loader renders only on individual blog posts and only when all required values are present. Until then it emits no broken widget and no placeholder error.

Discussion mapping will use Giscus's `specific` term mode with strict matching. The term is derived from `interactionId`, for example `post:the-miracle-of-istanbul`, rather than from the title or URL. Consequently, English and Chinese translations share one underlying discussion even though their paths and titles differ.

The Giscus interface language follows the page (`en` for the `en-US` site or `zh-CN`), while comments themselves remain a single bilingual conversation. Reactions are enabled, metadata emission is disabled, and the script loads lazily. Comments are public and handled by the third-party GitHub/Giscus service. A Giscus network or authentication failure must not interfere with reading the post.

## 11. Registration-Free Upvotes

Bear Neo includes the upvote button, counter, styling, and browser-side API calls. Persistent counts are supplied by the separate [Kudos](https://github.com/puinoib/kudos) service, which runs on Cloudflare Workers with a D1 database. GitHub Pages cannot provide this mutable backend.

The project retains Bear Neo's visual treatment but replaces its inline page logic with the testable `blog/page.html`, `_partials/kudos.html`, and `assets/js/kudos.mjs` adapter. The site derives the Kudos entity from `interactionId`, for example `post:the-miracle-of-istanbul`, so both translations read and modify one shared count.

Upvotes require no visitor registration. Kudos limits a public IP to one upvote per entity using a hashed IP identity; shared networks may therefore share a voting identity. Loading the control contacts the configured Worker, which receives the visitor's public IP as part of the network request; the inspected service persists only its SHA-256-derived voting identity. The configuration container must be a map, `enabled` must be a real boolean, and `endpoint` must be a string. After trimming surrounding whitespace, the endpoint must be a credential-free ASCII HTTPS root origin, or loopback HTTP using `localhost` or `127.0.0.1`, with an optional port from 1 through 65535, no path other than an optional trailing slash, and no query or fragment.

Server-rendered Kudos markup begins hidden so a missing local module cannot expose a false count. On client mount it is unhidden in a disabled, `aria-busy="true"` loading state with an em dash rather than zero. A successful load reveals the real count and enables the button. A failed load shows a localized unavailable state rather than a false zero. While a mutation is pending, repeat clicks cause no second POST/DELETE. Load and mutation failures are handled without unhandled promise rejections and never block or hide article content.

Production setup remains external:

1. Fork the Kudos repository.
2. Create a Cloudflare D1 database.
3. Deploy the fork as a Cloudflare Worker using the D1 database ID.
4. Optionally restrict `ALLOWED_ORIGINS` to the final GitHub Pages/custom-domain origin and the local preview origin while testing.
5. Set the resulting Worker URL in `params.kudos.endpoint` and enable `params.kudos.enabled`.

Because activation depends on the user's Cloudflare account, the local deliverable is verified against a **mock endpoint** rather than a deployed Worker, so the client route and toggle behavior are demonstrably working before any external service exists. Automated abuse protection beyond Kudos's per-IP behavior, such as Cloudflare rate limiting, is outside the initial implementation.

## 12. GitHub Pages Deployment

The repository will include a GitHub Actions workflow for Hugo deployment. It will:

- Run for pushes, deploy only when the pushed ref is the repository's actual default branch, and also support manual dispatch.
- Pin every third-party action to an immutable 40-character commit SHA, annotated with the reviewed release version.
- Install Hugo Extended pinned to 0.164.0, matching the verified local toolchain.
- Require Node.js 22 or newer and run every Python and `tests/*.test.mjs` browser-module test.
- Check out the repository without relying on a theme submodule.
- Configure GitHub Pages and use the Pages-provided base URL, supporting both user/organization sites and project sites.
- Build the production site with minification, warning promotion, i18n/path warnings, and the focused base-path verifier.
- Upload the generated `public` directory as a Pages artifact.
- Grant the build job only `contents: read` and `pages: read`; grant only the deploy job `pages: write` and `id-token: write`.
- Deploy through the official Pages deployment action with deployment concurrency control.

The site will not rely on Jekyll. A `.nojekyll` marker will always be included in the published artifact.

Verification will build once for a root-hosted base URL and once for a project-site base URL such as `https://example.github.io/example-blog/`. No generated internal link or asset URL may discard the configured subpath. The theme's hardcoded `/index.xml` and `/sitemap.xml` are the known offenders this check exists to catch.

Remote activation requires the user to select or create a repository and enable GitHub Pages with GitHub Actions as its source. The final repository also supplies the Giscus identifiers. These external account changes are separate from creating the local, deployment-ready files.

## 13. Local Development

The primary local workflow is:

```sh
hugo server        # add -D to include drafts
```

The terminal output supplies the local URL, normally `http://localhost:1313/`. Hugo watches content and template changes. Giscus and Kudos are hidden when unconfigured, so the local site remains fully usable before either remote service exists. Once configured, both widgets call their remote services from the local page; the Kudos origin allowlist must include the chosen local origin for that test.

The production-equivalent local build is:

```sh
hugo --gc --minify
```

Generated output goes to `public/` and is not treated as hand-authored source.

## 14. Authoring Workflow

Posts are written locally in a text editor and previewed with `hugo server`. No CMS or admin interface is added.

**A new English post:**

```sh
hugo new content --kind blog content/blog/<slug>/index.en.md
```

The `blog` archetype scaffolds `title`, `date`, `lastmod`, `tags`, `draft: true`, and an `interactionId` pre-filled from the slug. Images and attachments are placed beside the Markdown file in the same directory and referenced with bundle-relative paths, so they travel with the post. Publishing is removing `draft: true`.

**A Chinese translation of an existing post:** run `python3 scripts/new_translation.py <slug> en zh`. Hugo can scaffold a second language file inside an existing leaf bundle; this site-local helper is preferred because it copies the source page verbatim to `index.zh.md`, preserves every identity-bearing field, rejects unsafe paths and symlink escapes, and uses exclusive creation so it cannot overwrite an existing translation. Keep the copied `interactionId` unchanged, then replace the title, body, and tags with Chinese content. Sharing the bundle means sharing the media and route; the identical ID means the translation inherits the same discussion thread and upvote count. A mismatched ID fails the build with a clear message.

**A Chinese-only post:** create the bundle with only `index.zh.md`. It appears solely in Chinese lists, tags, and feeds.

Tags are per-language free text (§7.2), so a Chinese post's tags are written in Chinese and create Chinese term pages.

The README documents these three flows, the two build commands, and where the deferred integration values go.

## 15. Failure Handling and Privacy Boundaries

- Missing optional integration configuration results in no integration markup, not a build failure.
- A published missing, non-string, malformed, overlong, or translation-mismatched `interactionId` is the one integration-related condition that fails the build, because silently minting a divergent identity corrupts data that later cannot be merged. A standalone draft may omit the field and then renders without interactions.
- A Giscus or Kudos outage does not affect navigation, content, language switching, RSS, or static rendering.
- Giscus visitors authenticate through GitHub and are subject to GitHub/Giscus behavior.
- Kudos receives requests through Cloudflare and uses a hash derived from the visitor's public IP to enforce its per-entity vote rule; raw-IP persistence is not part of the blog.
- The document uses `strict-origin-when-cross-origin`; cross-origin Giscus and Kudos requests receive at most the site origin as the referrer, not the post path.
- No analytics or advertising scripts are added.

## 16. Verification and Acceptance Criteria

Verification stays focused on the static-hosting failure mode: standard-library tests build both root-hosted and project-subpath variants, and a dependency-free verifier reports generated internal HTML/XML URLs that discard the configured base path. It also rejects missing, non-directory, or empty site roots; malformed base URLs and XML; unknown XML encodings with a contained diagnostic rather than a traceback; invalid same-origin references; navigable backslashes in relative or HTTP(S) references; strict-prefix collisions; and percent-decoded dot segments. It accepts percent-encoded CJK routes, compares hosts with effective ports, ignores external Unicode IDNs, and continues to skip the opaque `data:`, `javascript:`, `mailto:`, and `tel:` schemes even when their payloads contain backslashes. It does not attempt exhaustive target, fragment, `srcset` grammar, or CSS validation; generated output is asserted not to contain `srcset`, and known pages and resources are covered by targeted assertions and the browser pass.

The implementation is accepted when all of the following hold:

1. Hugo completes a clean, minified production build with no warnings, and the base-path verifier reports no generated internal URL that discards the configured deployment subpath.
2. `/` and `/zh/` render localized homes with the correct site owner name, and each language exposes exactly the localized Home, Posts, and Tags primary-navigation destinations, each staying within its own language. English post counts exercise Hugo's `one`/`other` forms, while Chinese counts remain textually invariant apart from the number. Posts search remains title-only and uses locale-neutral casing, including matching `istanbul` to `Istanbul` under a Turkish reader locale.
3. The three current posts render at their English `/p/<slug>/` URLs with all 23 images, the poster PDF, and the linked R Markdown source available, and with the three Lekythos images at their intended 400, 400, and 200 pixel widths.
4. English-only posts do not generate Chinese copies or misleading post-level language switches.
5. A non-production fixture translation pair demonstrates direct post-level language switching, a shared `interactionId`, and a shared image and download resolved through the default-language page-resource permalink; no fake article content is published. A generated resource fixture proves percent-encoded filenames are URL-decoded for lookup while the raw query and fragment—including `#minipic`—survive under both root and project-subpath bases and from both languages.
6. `/index.xml` contains English content only and `/zh/index.xml` contains Chinese content only; each has localized feed metadata, current-language discovery/footer links, newest `lastmod`, and at most ten visible post items after hidden posts are excluded and the remainder is sorted. Summaries are well-formed XML and are not double escaped.
7. `/tags/` and `/zh/tags/` render localized tag overviews; term links resolve, list only posts in the current language, and remain within that language. A `测试` fixture confirms `/zh/tags/测试/` and its percent-encoded browser form resolve under both root and project-subpath builds and the dev server; an identically spelled tag in both languages proves that term pages do not gain inferred language switches or alternates.
8. Canonical, `lang`, and alternate-language metadata match the actual generated pages, `lang` is `en-US` and `zh-CN` respectively, and the root sitemap index points to valid per-language sitemaps whose entries contain only real reciprocal alternates. A hidden generated page has exactly one `robots` `noindex` directive and no canonical or alternate links, and no visible counterpart advertises it.
9. Light and dark rendering follow simulated browser preferences with no manual toggle; generated metadata contains `color-scheme` support and media-specific light/dark `theme-color` values. Effective tertiary-text and upvoted colors meet a 4.5:1 contrast ratio in both schemes, the dark tokens remain Bear Neo's original values, and the upvoted icon gains a solid-fill non-color cue.
10. Chinese text renders in a CJK font from the configured stack rather than per-glyph browser fallback, and a whitespace-free Chinese fixture with an 11-character first paragraph, a 26-character body, and `summaryLength = 10` produces word count 26 and the exact first-paragraph summary `天地玄黄宇宙洪荒日月盈`, excluding the tail marker `尾标`, when `hasCJKLanguage` is enabled.
11. Missing, incomplete, non-map, mistyped, or malformed optional Giscus/Kudos settings produce no widget and no browser error from partially initialized scripts; valid padded strings are trimmed before rendering.
12. With non-secret fixture configuration, both translations emit the same strict Giscus term and Kudos entity, while Giscus derives the correct interface language from the page, loads lazily, enables reactions, disables metadata emission, and follows the preferred scheme. Deterministic client tests reject wrong entities, unsafe counts, non-boolean voter state, invalid JSON, non-2xx responses, and malformed mutation payloads. A served browser fixture verifies Kudos loading, ready, shared-count, rapid-double-click, mutation-failure, retry, and unavailable states without contacting production services; intentionally aborted Giscus requests and mocked Kudos 503 responses may produce expected request/console diagnostics but must leave article content and navigation usable. Live Worker CORS remains deferred to post-deployment.
13. Direct Hugo validation fails the build on a missing page-local ID even when a site- or language-level fallback exists, on non-string, empty, malformed, or overlong IDs, and on mismatched IDs within a translation pair, including a published/draft pair; an exact 80-character ID remains valid and a standalone draft may omit the ID. The verification script covers the same syntax/equality branches and reports an ID used in more than one bundle.
14. Root-hosted and subpath-hosted production builds both retain their base path in internal links, shared bundle media/downloads, feeds, canonicals, and sitemap URLs.
15. The GitHub Pages workflow validates syntactically, pins every third-party action to an immutable commit SHA, requires Node.js 22 or newer, runs the current 71 Python and 35 browser-module tests (four post-search plus 31 Kudos), builds from the vendored theme without submodules, includes `.nojekyll`, and scopes write/OIDC permissions to deployment only.
16. The vendored theme retains its license and records the exact upstream URL and commit, and every shadowed template records the commit it was copied from.
17. Tests run the README's `hugo new` command and safe translation-copy helper in a temporary copy, verify a correctly scaffolded post and linked translation with the same immutable ID, and prove that the helper rejects path traversal, unknown or identical language arguments, and symlink escapes while preserving an existing translation byte for byte.
18. The site is inspected at desktop and narrow/mobile widths for navigation, long prose in both scripts, code blocks, images, footnotes, CJK typography, and every locally testable interaction state.

Live activation is a separate post-deployment checklist: verify Giscus can read/create the shared Discussion in the configured repository, and verify the deployed Kudos Worker reads, adds, and removes the shared count from both language pages. These checks cannot pass until the deferred external values and services exist.

## 17. Deferred Configuration Needed from the User

The local implementation can proceed without these values, but fully activating remote interactions later requires:

- The public GitHub repository name used for GitHub Pages and Giscus.
- Giscus repository/category IDs generated after Discussions and the Giscus App are configured.
- The deployed Kudos Worker URL.
- The final production origin if the Kudos browser-origin allowlist is restricted.

These values remain centralized in site parameters, so activating the services does not require editing theme templates or post bodies.

## 18. Revision Log

**2026-08-09 — footer simplification.** Removed the visible Bear Neo attribution and sitemap link from both language footers at the user's request; the localized RSS link remains, and sitemap generation is unchanged.

**2026-08-09 — post-review reconciliation.** Recorded URL-decoded page-resource lookup with canonical default-language permalinks and raw query/fragment preservation; hidden-page `noindex` behavior without canonical or alternate advertisement; WCAG 4.5:1 effective tertiary/upvoted colors with preserved dark tokens and a solid-fill pressed cue; locale-neutral title matching; and the final 71-Python/35-Node verification totals.

**2026-08-09 — implementation reconciliation.** Recorded the empirically required `:contentbasename` permalink, 11-character CJK summary boundary, hidden-before-limit and single-escape RSS behavior, strict optional-integration containers and Kudos payload validation, immutable GitHub Action SHA pins, Node.js 22 and the complete browser-module test glob, safe authoring path containment, hardened generated-site verifier, and cached-package fallback for the final local Playwright pass.

**2026-08-08 — cross-document reconciliation.** Restored the user-approved “Posts” navigation label, normal browser link behavior (`externalLinksNewTab = false`), author-supplied tag capitalization, and the `en-US` English locale. Corrected the source audit to 25 referenced resources: 23 images, one PDF, and one R Markdown file; the Istanbul bundle contains 20 images plus the R Markdown source. Kept the technically sound Hugo 0.164 `locale`/`direction` template architecture, added multilingual resource-aware image/link rendering, preserved the Lekythos widths, and made published interaction identities strict and page-local at Hugo build time. Added an explicit ten-item RSS limit, deterministic CJK summary/word-count checks, term-page alternate suppression for independent vocabularies, deterministic Kudos failure/race states, typed optional-integration guards with bounded ports, privacy disclosures, per-job Pages permissions, and a tested exclusive-copy translation helper even though Hugo can scaffold the file, because verbatim exclusive copying preserves the published identity and prevents overwrite. Added safe temporary/ignore handling and narrowed generated-site verification to configured-base-path escapes plus targeted resource assertions.

**2026-08-08 — initial specification review.** Verified theme claims against upstream commit `f5c57c5` and recorded the actual lack of `i18n/`, tag-overview, and comment support. Added the tag-routing conflict, CJK requirement, locale-aware dates, explicit front-matter mapping, local Git initialization, and the `hugo new` authoring workflow. The later reconciliation above supersedes architectural and product choices that this review changed without user approval.

The resulting approved decisions are: current Hugo template and language APIs over deprecated configuration; Home, Posts, and Tags as the three primary destinations; independent per-language tag vocabularies; automatic browser color matching only; Giscus as the sole comment system; shared `interactionId` identities for Giscus and Kudos; and local `hugo new` authoring with no CMS.
