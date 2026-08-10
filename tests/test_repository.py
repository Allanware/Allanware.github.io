import unittest
from pathlib import Path
import re


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
THEME_ROOT = REPOSITORY_ROOT / "themes" / "hugo-bearneo"
PINNED_COMMIT = "f5c57c5ea39a091f0167af6312f4d4e385df2e6c"
DERIVED_TEMPLATES = {
    "layouts/baseof.html": "layouts/_default/baseof.html",
    "layouts/404.html": "layouts/404.html",
    "layouts/_markup/render-image.html": "layouts/_default/_markup/render-image.html",
    "layouts/_markup/render-link.html": "layouts/_default/_markup/render-link.html",
    "layouts/_partials/header.html": "layouts/partials/header.html",
    "layouts/_partials/nav.html": "layouts/partials/nav.html",
    "layouts/_partials/footer.html": "layouts/partials/footer.html",
    "layouts/_partials/toc.html": "layouts/partials/toc.html",
    "layouts/_partials/custom_head.html": "layouts/partials/custom_head.html",
    "layouts/_partials/seo_tags.html": "layouts/partials/seo_tags.html",
    "layouts/_partials/post-list.html": "layouts/_default/list.html",
    "layouts/_partials/article.html": "layouts/_default/single.html",
    "layouts/blog/section.html": "layouts/_default/list.html",
    "layouts/home.rss.xml": "layouts/_default/rss.xml",
}
ACTION_PINS = {
    "actions/checkout": (
        "de0fac2e4500dabe0009e67214ff5f5447ce83dd",
        "v6.0.2",
    ),
    "actions/configure-pages": (
        "45bfe0192ca1faeb007ade9deae92b16b8254a0d",
        "v6.0.0",
    ),
    "actions/upload-pages-artifact": (
        "fc324d3547104276b827a68afc52ff2a11cc49c9",
        "v5.0.0",
    ),
    "actions/deploy-pages": (
        "cd2ce8fcbc39b97be8ca5fce6e763baed58fa128",
        "v5.0.0",
    ),
}


def job_block(workflow: str, name: str) -> str:
    match = re.search(
        rf"(?ms)^  {re.escape(name)}:\n(?P<body>.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)",
        workflow,
    )
    if match is None:
        raise AssertionError(f"workflow job {name!r} is missing")
    return match.group("body")


def job_permissions(block: str) -> dict[str, str]:
    match = re.search(
        r"(?m)^    permissions:\n(?P<body>(?:^      [A-Za-z0-9_-]+: [A-Za-z]+\n)+)",
        block,
    )
    if match is None:
        raise AssertionError("job permissions block is missing")
    return {
        key: value
        for key, value in re.findall(
            r"(?m)^      ([A-Za-z0-9_-]+): ([A-Za-z]+)$",
            match.group("body"),
        )
    }


class RepositoryTests(unittest.TestCase):
    def test_vendored_theme_records_license_and_upstream_provenance(self):
        license_file = THEME_ROOT / "LICENSE"
        self.assertTrue(license_file.is_file())
        self.assertIn("MIT License", license_file.read_text(encoding="utf-8"))

        upstream = THEME_ROOT / "UPSTREAM.md"
        self.assertTrue(upstream.is_file())
        provenance = upstream.read_text(encoding="utf-8")
        self.assertIn("https://github.com/rokcso/hugo-bearneo", provenance)
        self.assertIn(PINNED_COMMIT, provenance)

    def test_vendored_theme_does_not_contain_nested_git_metadata(self):
        nested_git_paths = list(THEME_ROOT.rglob(".git"))
        self.assertEqual([], nested_git_paths)

    def test_static_nojekyll_marker_exists(self):
        self.assertTrue((REPOSITORY_ROOT / "static" / ".nojekyll").is_file())

    def test_pages_workflow_uses_pinned_actions_and_scoped_permissions(self):
        workflow = (REPOSITORY_ROOT / ".github/workflows/hugo.yml").read_text(
            encoding="utf-8"
        )
        self.assertRegex(workflow, r"(?m)^  HUGO_VERSION: 0\.164\.0$")
        self.assertRegex(workflow, r"(?m)^permissions: \{\}$")

        actual_uses = re.findall(r"(?m)^\s+uses: ([^\s#]+)", workflow)
        expected_uses = [f"{action}@{pin}" for action, (pin, _) in ACTION_PINS.items()]
        self.assertCountEqual(expected_uses, actual_uses)
        for action, (pin, version) in ACTION_PINS.items():
            self.assertRegex(
                workflow,
                rf"(?m)^\s+uses: {re.escape(action)}@{pin} +# {re.escape(version)}$",
            )

        build = job_block(workflow, "build")
        deploy = job_block(workflow, "deploy")
        self.assertEqual(
            {"contents": "read", "pages": "read"},
            job_permissions(build),
        )
        self.assertNotIn("write", " ".join(job_permissions(build).values()))
        self.assertNotIn("id-token", job_permissions(build))
        self.assertEqual(
            {"pages": "write", "id-token": "write"},
            job_permissions(deploy),
        )

    def test_pages_workflow_builds_the_actual_pages_artifact(self):
        workflow = (REPOSITORY_ROOT / ".github/workflows/hugo.yml").read_text(
            encoding="utf-8"
        )
        build = job_block(workflow, "build")
        deploy = job_block(workflow, "deploy")
        pages_base = "${{ steps.pages.outputs.base_url }}/"

        self.assertIn("id: pages", build)
        self.assertIn(
            "python3 scripts/validate_interaction_ids.py content",
            build,
        )
        self.assertIn(
            "python3 -m unittest discover -s tests -p 'test_*.py' -v",
            build,
        )
        self.assertIn("node --test tests/*.test.mjs", build)
        self.assertRegex(build, r"(?m)^\s+run: hugo .*--baseURL \"\$\{\{ steps\.pages\.outputs\.base_url \}\}/\"$")
        self.assertIn(
            f'python3 scripts/check_site.py public --base-url "{pages_base}"',
            build,
        )
        self.assertRegex(build, r"(?m)^\s+run: test -f public/\.nojekyll$")
        self.assertRegex(
            build,
            r"(?ms)actions/upload-pages-artifact@[0-9a-f]{40}.*?with:\n\s+path: public\n\s+include-hidden-files: true",
        )
        self.assertRegex(
            deploy,
            r"(?m)^    if: github\.event_name == 'workflow_dispatch' \|\| github\.ref == format\('refs/heads/\{0\}', github\.event\.repository\.default_branch\)$",
        )
        self.assertIn("needs: build", deploy)
        self.assertNotRegex(workflow, r"(?m)^\s*submodules\s*:")
        self.assertFalse((REPOSITORY_ROOT / ".gitmodules").exists())

    def test_derived_templates_record_exact_upstream_sources(self):
        for local, upstream in DERIVED_TEMPLATES.items():
            with self.subTest(local=local):
                template = (REPOSITORY_ROOT / local).read_text(encoding="utf-8")
                self.assertIn(PINNED_COMMIT, template)
                self.assertIn(upstream, template)

    def test_blog_archetype_defines_the_authoring_contract(self):
        archetype = (REPOSITORY_ROOT / "archetypes/blog.md").read_text(
            encoding="utf-8"
        )

        required_fields = {
            "title",
            "date",
            "lastmod",
            "draft",
            "tags",
            "interactionId",
        }
        actual_fields = {
            match.group(1)
            for match in re.finditer(r"(?m)^([A-Za-z][A-Za-z0-9]*)\s*=", archetype)
        }
        self.assertTrue(required_fields <= actual_fields)
        self.assertIn("## Introduction", archetype)


if __name__ == "__main__":
    unittest.main()
