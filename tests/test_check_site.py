from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from scripts.check_site import check_site


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_site.py"


class GeneratedBasePathTests(unittest.TestCase):
    def test_accepts_scoped_urls_in_html_and_xml(self):
        with TemporaryDirectory() as temporary:
            site = Path(temporary)
            (site / "blog").mkdir()
            (site / "blog" / "index.html").write_text(
                '<a href=/example-blog/tags/>Tags</a>'
                '<img src=image.png alt=fixture>'
                '<video poster="//EXAMPLE.test:443/example-blog/poster.png"></video>'
                '<object data=/example-blog/notes.pdf></object>'
                '<div data=/outside/not-an-object>Ignored data attribute</div>'
                '<img src="data:image/gif;base64,R0lGODlhAQABAIAAAAUEBA==">'
                '<a href="javascript:void(0)">Script</a>'
                '<a href="mailto:reader@example.test">Mail</a>'
                '<a href="tel:+15555555555">Telephone</a>',
                encoding="utf-8",
            )
            (site / "index.xml").write_text(
                '<?xml version="1.0"?>'
                '<rss><channel>'
                '<link>https://example.test:443/example-blog/</link>'
                '<guid>//example.test/example-blog/blog/</guid>'
                '<url>https://external.example/not-checked</url>'
                '<image href="/example-blog/image.png" '
                'src="/example-blog/source.png" url="/example-blog/icon.png" />'
                '</channel></rss>',
                encoding="utf-8",
            )

            self.assertEqual(
                [],
                check_site(site, "https://Example.TEST/example-blog"),
            )

    def test_reports_internal_html_and_xml_urls_that_escape_strict_prefix(self):
        with TemporaryDirectory() as temporary:
            site = Path(temporary)
            (site / "index.html").write_text(
                '<a href=/tags/>Escaped root</a>'
                '<a href="https://example.test/example-blogger/">Prefix collision</a>'
                '<object data="/download.pdf"></object>'
                '<div data="/ignored-div-data">Ignored</div>'
                '<img srcset="/ignored-srcset.png 1x">',
                encoding="utf-8",
            )
            (site / "sitemap.xml").write_text(
                '<?xml version="1.0"?>'
                '<urlset><url><loc>/zh/</loc></url>'
                '<entry url="/feed.xml" /></urlset>',
                encoding="utf-8",
            )

            errors = check_site(site, "https://example.test/example-blog/")

            self.assertEqual(5, len(errors), errors)
            self.assertTrue(all("escapes configured base path" in error for error in errors))
            combined = "\n".join(errors)
            for escaped in ("/tags/", "/example-blogger/", "/download.pdf", "/zh/", "/feed.xml"):
                with self.subTest(escaped=escaped):
                    self.assertIn(escaped, combined)
            self.assertNotIn("ignored-div-data", combined)
            self.assertNotIn("ignored-srcset", combined)

    def test_ignores_external_hosts_and_different_effective_ports(self):
        with TemporaryDirectory() as temporary:
            site = Path(temporary)
            (site / "index.html").write_text(
                '<a href="https://external.example/tags/">External</a>'
                '<a href="http://example.test/tags/">Different default port</a>'
                '<a href="https://example.test:444/tags/">Different explicit port</a>'
                '<a href="https://EXAMPLE.test:443/example-blog/tags/">Internal</a>',
                encoding="utf-8",
            )

            self.assertEqual(
                [],
                check_site(site, "https://example.test/example-blog/"),
            )

    def test_accepts_percent_encoded_cjk_but_rejects_encoded_dot_segments(self):
        with TemporaryDirectory() as temporary:
            site = Path(temporary)
            (site / "index.html").write_text(
                '<a href="/example-blog/zh/tags/%E6%B5%8B%E8%AF%95/">测试</a>'
                '<a href="/example-blog/%2e%2e/zh/">Encoded traversal</a>',
                encoding="utf-8",
            )

            errors = check_site(site, "https://example.test/example-blog/")

            self.assertEqual(1, len(errors), errors)
            self.assertIn("percent-decoded dot path segment", errors[0])
            self.assertIn("%2e%2e", errors[0])
            self.assertNotIn("%E6%B5%8B%E8%AF%95", errors[0])

    def test_does_not_validate_targets_fragments_css_or_srcset(self):
        with TemporaryDirectory() as temporary:
            site = Path(temporary)
            (site / "index.html").write_text(
                '<a href="/example-blog/missing/#fragment">Missing target</a>'
                '<img src="missing.png" alt="Missing image">'
                '<img srcset="/outside/image.png 1x">'
                '<link rel="stylesheet" href="/example-blog/style.css">',
                encoding="utf-8",
            )
            (site / "style.css").write_text(
                'body { background: url("/outside/background.png"); }',
                encoding="utf-8",
            )

            self.assertEqual(
                [],
                check_site(site, "https://example.test/example-blog/"),
            )

    def test_reports_malformed_xml(self):
        with TemporaryDirectory() as temporary:
            site = Path(temporary)
            (site / "index.xml").write_text("<rss><channel></rss>", encoding="utf-8")

            errors = check_site(site, "https://example.test/example-blog/")

            self.assertEqual(1, len(errors), errors)
            self.assertIn("index.xml: unable to parse XML:", errors[0])

    def test_reports_unknown_xml_encoding(self):
        with TemporaryDirectory() as temporary:
            site = Path(temporary)
            (site / "index.xml").write_bytes(
                b'<?xml version="1.0" encoding="x-check-site-unknown"?><urlset />'
            )

            errors = check_site(site, "https://example.test/example-blog/")

            self.assertEqual(1, len(errors), errors)
            self.assertIn("index.xml: unable to parse XML:", errors[0])
            self.assertIn("unknown encoding", errors[0].lower())

    def test_rejects_navigable_backslashes_but_skips_opaque_schemes(self):
        with TemporaryDirectory() as temporary:
            site = Path(temporary)
            (site / "index.html").write_text(
                '<a href="\\zh/">Relative backslash</a>'
                '<a href="https://external.example\\outside/">External backslash</a>'
                '<img src="data:image/svg+xml,a\\b">'
                '<a href="javascript:a\\b">Script</a>'
                '<a href="mailto:reader\\name@example.test">Mail</a>'
                '<a href="tel:+1\\555">Telephone</a>',
                encoding="utf-8",
            )

            errors = check_site(site, "https://example.test/example-blog/")

            self.assertEqual(2, len(errors), errors)
            self.assertTrue(all("contains a backslash" in error for error in errors))
            combined = "\n".join(errors)
            self.assertIn("\\zh/", combined)
            self.assertIn("https://external.example", combined)
            for skipped_scheme in ("data:", "javascript:", "mailto:", "tel:"):
                with self.subTest(skipped_scheme=skipped_scheme):
                    self.assertNotIn(skipped_scheme, combined)

    def test_ignores_external_unicode_idns_but_checks_same_origin_and_malformed_urls(self):
        with TemporaryDirectory() as temporary:
            site = Path(temporary)
            (site / "index.html").write_text(
                '<a href="https://例子.example/tags/">External IDN</a>'
                '<a href="//例子.example:443/tags/">Scheme-relative external IDN</a>'
                '<a href="//EXAMPLE.test.:443/tags/">Normalized same origin</a>'
                '<a href="http://[">Malformed URL</a>'
                '<a href="https:///missing-host/">Missing host</a>',
                encoding="utf-8",
            )

            errors = check_site(site, "https://example.test/example-blog/")

            self.assertEqual(3, len(errors), errors)
            combined = "\n".join(errors)
            self.assertIn("//EXAMPLE.test.:443/tags/", combined)
            self.assertIn("escapes configured base path", combined)
            self.assertIn("http://[", combined)
            self.assertIn("https:///missing-host/", combined)
            self.assertIn("invalid URL", combined)
            self.assertNotIn("例子.example", combined)

    def test_reports_malformed_reference_without_aborting_the_check(self):
        with TemporaryDirectory() as temporary:
            site = Path(temporary)
            (site / "index.html").write_text(
                '<a href="http://[">Malformed host</a>'
                '<a href="https://example.test:99999/tags/">Malformed port</a>',
                encoding="utf-8",
            )

            errors = check_site(site, "https://example.test/example-blog/")

            self.assertEqual(2, len(errors), errors)
            combined = "\n".join(errors)
            self.assertIn("href='http://[': invalid URL", combined)
            self.assertIn("href='https://example.test:99999/tags/': invalid URL", combined)

    def test_missing_nondirectory_and_empty_site_roots_fail(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            missing = root / "missing"
            regular_file = root / "file"
            regular_file.write_text("not a directory", encoding="utf-8")
            empty = root / "empty"
            empty.mkdir()

            self.assertEqual(
                [f"site root does not exist: {missing.resolve()}"],
                check_site(missing, "https://example.test/example-blog/"),
            )
            self.assertEqual(
                [f"site root is not a directory: {regular_file.resolve()}"],
                check_site(regular_file, "https://example.test/example-blog/"),
            )
            self.assertEqual(
                ["site root contains no HTML or XML documents"],
                check_site(empty, "https://example.test/example-blog/"),
            )

    def test_rejects_invalid_base_urls(self):
        with TemporaryDirectory() as temporary:
            site = Path(temporary)
            (site / "index.html").write_text("<main>Fixture</main>", encoding="utf-8")
            invalid_urls = (
                "ftp://example.test/example-blog/",
                "https:///example-blog/",
                "https://user@example.test/example-blog/",
                "https://user:secret@example.test/example-blog/",
                "https://example.test/example-blog/?preview=1",
                "https://example.test/example-blog/?",
                "https://example.test/example-blog/#top",
                "https://example.test/example-blog/#",
                "https://exa mple.test/example-blog/",
                "https://exam\tple.test/example-blog/",
                "https://example.test/example blog/",
                "https://example.test:invalid/example-blog/",
                "https://example.test:0/example-blog/",
                "https://example.test:65536/example-blog/",
                "https://-example.test/example-blog/",
                "https://example..test/example-blog/",
                "https://例子.test/example-blog/",
                "https://example.test/example-blog/%2E/",
            )
            for base_url in invalid_urls:
                with self.subTest(base_url=base_url):
                    with self.assertRaisesRegex(ValueError, "base URL"):
                        check_site(site, base_url)

            self.assertEqual(
                [],
                check_site(site, "https://example.test:65535/example-blog/"),
            )


class GeneratedBasePathCliTests(unittest.TestCase):
    def run_checker(self, site: Path, base_url: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CHECKER), str(site), "--base-url", base_url],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_cli_prints_exact_success_summary(self):
        with TemporaryDirectory() as temporary:
            site = Path(temporary)
            (site / "index.html").write_text(
                '<a href="/example-blog/">Home</a>',
                encoding="utf-8",
            )

            result = self.run_checker(site, "https://example.test/example-blog/")

            self.assertEqual(0, result.returncode)
            self.assertEqual("base-path verification passed\n", result.stdout)
            self.assertEqual("", result.stderr)

    def test_cli_prints_exact_failure_summary_and_returns_nonzero(self):
        with TemporaryDirectory() as temporary:
            site = Path(temporary)
            (site / "index.html").write_text('<a href="/tags/">Tags</a>', encoding="utf-8")

            result = self.run_checker(site, "https://example.test/example-blog/")

            self.assertEqual(1, result.returncode)
            self.assertEqual("", result.stdout)
            self.assertEqual(
                "index.html: href='/tags/': '/tags/' resolves to '/tags/' and "
                "escapes configured base path '/example-blog/'\n"
                "base-path verification failed with 1 error(s)\n",
                result.stderr,
            )

    def test_cli_fails_for_missing_empty_and_invalid_base_url(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            empty = root / "empty"
            empty.mkdir()
            cases = (
                (root / "missing", "https://example.test/example-blog/"),
                (empty, "https://example.test/example-blog/"),
                (empty, "https://example.test/example-blog/?preview=1"),
            )
            for site, base_url in cases:
                with self.subTest(site=site.name, base_url=base_url):
                    result = self.run_checker(site, base_url)
                    self.assertNotEqual(0, result.returncode)
                    self.assertEqual("", result.stdout)
                    self.assertRegex(
                        result.stderr,
                        r"base-path verification failed with 1 error\(s\)\n$",
                    )

    def test_cli_reports_unknown_xml_encoding_without_a_traceback(self):
        with TemporaryDirectory() as temporary:
            site = Path(temporary)
            (site / "index.xml").write_bytes(
                b'<?xml version="1.0" encoding="x-check-site-unknown"?><urlset />'
            )

            result = self.run_checker(site, "https://example.test/example-blog/")

            self.assertEqual(1, result.returncode)
            self.assertEqual("", result.stdout)
            self.assertIn("index.xml: unable to parse XML:", result.stderr)
            self.assertIn("unknown encoding", result.stderr.lower())
            self.assertNotIn("Traceback", result.stderr)
            self.assertRegex(
                result.stderr,
                r"base-path verification failed with 1 error\(s\)\n$",
            )


if __name__ == "__main__":
    unittest.main()
