# Remove Homepage Copy Assertions Design

## Goal

Allow homepage introduction prose to change without requiring test updates.

## Design

Remove the entire homepage-introduction assertion block from
`test_localized_brand_contact_and_generated_favicons`. This includes the exact
English/Chinese intro text comparison and the intro-specific link/email checks.

Keep all remaining assertions in that test unchanged, including localized site
titles, visible brand headings, contact-email absence, source-image integrity,
favicon generation, and root/subpath behavior.

## Scope and verification

Only `tests/test_site.py` changes. No content, template, style, localization, or
configuration files change. The existing homepage edit remains uncommitted and
untouched. Run the focused test and complete Python and Node suites after the
assertion block is removed.
