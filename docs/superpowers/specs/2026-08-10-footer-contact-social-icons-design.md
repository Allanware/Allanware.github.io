# Footer Contact and Profile Icons

## Goal

Move the contact link off the home page into the footer, and add GitHub and Google Scholar profile links there. Present all three as icons so the footer gains two destinations without gaining a line of text.

## Visible behavior

The home introduction keeps the author name and drops the mail link:

- English: `Wenxuan Zhao.`
- Chinese: `赵文轩。`

The footer renders a single centered row holding three icon links followed by the existing subscribe sentence:

```
✉    ⬤    🎓    Subscribe via RSS.
```

The row is identical in both languages except for the subscribe sentence and the icons' accessible names. It wraps rather than overflowing on narrow viewports.

Icons render at 16px, sized against the footer's 0.8em text. Each icon link exposes an accessible name and no visible text:

- English: `Contact`, `GitHub`, `Google Scholar`
- Chinese: `联系`, `GitHub`, `谷歌学术`

The mail address stays absent from visible text; it appears only inside the `mailto:` href, matching the current home-page behavior. The RSS link keeps its existing wording, position at the end of the row, and trailing period.

## Implementation

Both supplied logo files move into `assets/images/` under kebab-case names matching the existing `drawing-hands.png`:

- `assets/images/github-logo.svg`
- `assets/images/google-scholar-logo.webp`

Three site parameters carry the destinations, keeping URLs out of the template. The existing empty `[params.author]` block stays untouched, because the vendored RSS template depends on that path.

- `contactEmail`
- `githubURL`
- `scholarURL`

The footer partial renders each of the three icons according to what the source art can support:

- **Contact** uses an inline filled envelope SVG painted with `currentColor`, so it tracks link and theme colors automatically. This follows the inline-SVG convention already established for the upvote control.
- **GitHub** renders the SVG asset through an `<img>` element. Because the supplied art is a black roundel enclosing a white octocat, the dark scheme inverts it with a `filter` rule, yielding a white roundel enclosing a dark octocat. The asset file itself needs no modification.
- **Google Scholar** renders a 32px resize of the webp asset through an `<img>` element, giving a 2x source for the 16px display size. Its brand blue holds sufficient contrast against both scheme backgrounds, so no filter applies.

Both asset lookups guard with `errorf` when the source is missing, following the favicon partial.

Layout lives in the site stylesheet as a centered, wrapping flex row with a gap, baseline-consistent icon sizing, and the dark-scheme inversion rule scoped to the GitHub icon.

Three localized strings are added to both translation files for the icons' accessible names.

## Verification

Generated-site tests will cover English and Chinese output at root and project-subpath base URLs. They will assert:

- the home introduction retains the author name and contains no mail link;
- the footer contains exactly four links, resolving to the mail address, the GitHub profile, the Scholar profile, and the language's RSS feed, in that order;
- each icon link carries a localized accessible name and contributes no visible text;
- the mail address never appears as visible text in any generated page;
- the footer keeps its existing subscribe wording and omits the upstream theme's attribution text;
- icons declare explicit 16px dimensions and the Scholar source resolves to a processed 32px derivative;
- the stylesheet scopes the inversion rule to the GitHub icon under the dark scheme only.

The full Python and Node suites, interaction-ID validator, actionlint, JavaScript syntax checks, and strict Hugo root/project-subpath builds must remain green.
