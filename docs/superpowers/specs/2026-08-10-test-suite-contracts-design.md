# Test Suite Contract Cleanup Design

## Goal

Make ordinary edits to articles, metadata, media, README prose, and production branding pass without test maintenance, while retaining regression coverage for behavior that affects readers, authors, security, accessibility, and deployment.

## Contract Boundary

The suite will protect observable behavior and repository safety rules. It will not treat the current production content or presentation implementation as immutable.

Protected contracts include:

- Hugo builds at both a root URL and a project subpath.
- Generated internal URLs remain inside the configured base path.
- Translation, canonical, sitemap, RSS, and interaction identities behave correctly.
- Search, popular-post, kudos, and comments integrations expose valid accessible state.
- Content authoring helpers reject unsafe input and preserve files they must not overwrite.
- CI actions stay pinned and job permissions remain scoped.
- Semantic colors retain adequate contrast.

The following are explicitly editorial or incidental and will not be pinned:

- Article bodies, titles, dates, tags, slugs, image inventories, and asset bytes.
- README wording and section organization.
- Production site title, contact details, social links, and integration identifiers.
- Exact CSS pixels, margins, font sizes, and color literals when a behavioral assertion exists.

## Test Structure

Production content will participate only in a generic build-and-link-validation smoke test. Feature tests will use synthetic content and configuration with deliberately controlled values. Assertions will inspect parsed structure or behavioral state instead of broad substrings and exact implementation fragments where practical.

Large integration cases will be reduced by removing unrelated production-content checks. Existing focused validator and JavaScript state-machine tests will remain because their literals describe input/output contracts rather than production data.

## Repository Tests

Repository tests will continue to check licensing, provenance, action pins, permissions, artifact production, and archetype fields. README prose assertions will be removed. Commands that matter operationally will be verified in the workflow itself instead of duplicated as documentation-copy checks.

## Content Tests

The migrated-content snapshot module will be removed. Its body hashes and resource hashes make all editorial changes look like regressions. A successful production Hugo build plus the base-path validator supplies the useful integrity signal without freezing content.

## Site Tests

The production matrix will assert successful builds, valid generated URLs, parseable HTML/XML output, and generic deployment artifacts. Tests for translations, feeds, integrations, lists, and localization will continue to use fixtures. Branding propagation will be tested with synthetic configuration values rather than expectations read from the same production configuration.

Exact color literals will be replaced by contrast-ratio assertions. Exact layout-value assertions will be removed unless the value itself is required for an accessibility behavior, such as preventing mobile input zoom or ensuring hidden filtered rows cannot be overridden.

## Verification

The cleanup is complete when the Python and Node suites pass, production Hugo builds pass, the generated-site validator passes, and a repository search confirms that article/resource SHA-256 snapshots and README-copy assertions are gone.
