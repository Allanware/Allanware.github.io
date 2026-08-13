from pathlib import Path
import gzip
import hashlib
import re
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest

from scripts.check_site import check_site


ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "assets/vendor/besogo"
PINNED_COMMIT = "4f03a3a04bc632c49ca9b494cbcad5c7cfb3f6b2"
REQUIRED_JS = {
    "besogo.js",
    "boardDisplay.js",
    "coord.js",
    "editor.js",
    "gameRoot.js",
    "loadSgf.js",
    "parseSgf.js",
    "svgUtil.js",
}
UNMODIFIED_VENDOR_FILES = {
    "LICENSE",
    "css/board-flat.css",
    "js/boardDisplay.js",
    "js/coord.js",
    "js/editor.js",
    "js/gameRoot.js",
    "js/loadSgf.js",
    "js/parseSgf.js",
    "js/svgUtil.js",
}
SYNTHETIC_SGF = ROOT / "tests/fixtures/go-board/synthetic.sgf"
GO_BOARD_CONTENT = ROOT / "tests/fixtures/go-board-content"


def relative_luminance(color: str) -> float:
    channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        value / 12.92 if value <= 0.04045
        else ((value + 0.055) / 1.055) ** 2.4
        for value in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(first: str, second: str) -> float:
    lighter, darker = sorted(
        (relative_luminance(first), relative_luminance(second)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def build_site(destination: Path, base_url: str, content: Path) -> None:
    subprocess.run(
        [
            "hugo",
            "--source", str(ROOT),
            "--destination", str(destination),
            "--baseURL", base_url,
            "--contentDir", str(content),
            "--cleanDestinationDir",
            "--panicOnWarning",
            "--noBuildLock",
            "--cacheDir", str(destination.parent / "cache"),
            "--environment", "production",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def run_hugo(destination: Path, content: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "hugo",
            "--source", str(ROOT),
            "--destination", str(destination),
            "--baseURL", "https://example.test/project/",
            "--contentDir", str(content),
            "--panicOnWarning",
            "--noBuildLock",
            "--cacheDir", str(destination.parent / "cache"),
            "--environment", "production",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def write_page(path: Path, *, title: str, interaction_id: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'''+++
title = "{title}"
date = 2026-08-10
draft = false
interactionId = "{interaction_id}"
+++

{body}
''',
        encoding="utf-8",
    )


class GoBoardVendorTests(unittest.TestCase):
    def test_besogo_vendor_is_pinned_minimal_and_image_free(self):
        self.assertEqual(
            REQUIRED_JS,
            {path.name for path in (VENDOR / "js").glob("*.js")},
        )
        self.assertEqual(
            {"board-flat.css"},
            {path.name for path in (VENDOR / "css").glob("*.css")},
        )
        self.assertFalse((VENDOR / "img").exists())

        license_text = (VENDOR / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("MIT License", license_text)
        self.assertIn("Copyright (c) 2015-2018 Ye Wang", license_text)

        provenance = (VENDOR / "UPSTREAM.md").read_text(encoding="utf-8")
        self.assertIn("https://github.com/yewang/besogo", provenance)
        self.assertIn(PINNED_COMMIT, provenance)

    def test_unmodified_vendor_files_match_the_pinned_checksum_manifest(self):
        manifest_path = VENDOR / "UPSTREAM_SHA256SUMS"
        self.assertTrue(manifest_path.is_file())
        entries = {}
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            digest, relative_path = line.split("  ", 1)
            self.assertRegex(digest, r"^[0-9a-f]{64}$")
            entries[relative_path] = digest

        self.assertEqual(UNMODIFIED_VENDOR_FILES, set(entries))
        for relative_path, expected in entries.items():
            actual = hashlib.sha256(
                (VENDOR / relative_path).read_bytes()
            ).hexdigest()
            self.assertEqual(expected, actual, relative_path)


class GoBoardStyleTests(unittest.TestCase):
    def test_board_cancels_figure_gutters_on_narrow_screens(self):
        css = (ROOT / "assets/css/go-board.css").read_text(encoding="utf-8")
        board_rule = re.search(r"\.go-board\s*\{(?P<body>[^}]*)\}", css)
        self.assertIsNotNone(board_rule)
        self.assertRegex(board_rule.group("body"), r"margin-inline:\s*0;")

    def test_board_shell_fills_the_available_figure_width(self):
        css = (ROOT / "assets/css/go-board.css").read_text(encoding="utf-8")
        shell_rule = re.search(r"\.go-board__shell\s*\{(?P<body>[^}]*)\}", css)
        self.assertIsNotNone(shell_rule)
        self.assertRegex(shell_rule.group("body"), r"inline-size:\s*100%;")
        self.assertRegex(shell_rule.group("body"), r"max-width:\s*38rem;")

    def test_unmounted_board_reserves_a_stable_square(self):
        css = (ROOT / "assets/css/go-board.css").read_text(encoding="utf-8")
        shell_rule = re.search(r"\.go-board__shell\s*\{(?P<body>[^}]*)\}", css)
        host_rule = re.search(r"\.go-board__host\s*\{(?P<body>[^}]*)\}", css)
        status_rule = re.search(r"\.go-board__status\s*\{(?P<body>[^}]*)\}", css)
        ready_rule = re.search(
            r'\.go-board__status\[data-state="ready"\]\s*\{(?P<body>[^}]*)\}',
            css,
        )

        for rule in (shell_rule, host_rule, status_rule, ready_rule):
            self.assertIsNotNone(rule)

        self.assertRegex(shell_rule.group("body"), r"position:\s*relative;")
        self.assertRegex(host_rule.group("body"), r"aspect-ratio:\s*1;")
        self.assertRegex(host_rule.group("body"), r"inline-size:\s*100%;")
        self.assertRegex(status_rule.group("body"), r"position:\s*absolute;")
        self.assertRegex(status_rule.group("body"), r"inset:\s*50%\s+auto\s+auto\s+50%;")
        self.assertRegex(
            status_rule.group("body"), r"transform:\s*translate\(-50%,\s*-50%\);"
        )
        self.assertRegex(ready_rule.group("body"), r"inset:\s*auto;")
        self.assertRegex(ready_rule.group("body"), r"margin:\s*-1px;")
        self.assertRegex(ready_rule.group("body"), r"transform:\s*none;")

    def test_final_figcaption_keeps_caption_before_fallbacks_visually(self):
        css = (ROOT / "assets/css/go-board.css").read_text(encoding="utf-8")
        board_rule = re.search(r"\.go-board\s*\{(?P<body>[^}]*)\}", css)
        self.assertIsNotNone(board_rule)
        self.assertRegex(board_rule.group("body"), r"display:\s*flex;")
        self.assertRegex(board_rule.group("body"), r"flex-direction:\s*column;")
        for selector, order in (
            (r"\.go-board figcaption", 1),
            (r"\.go-board__download", 2),
            (r"\.go-board noscript", 3),
        ):
            self.assertRegex(
                css,
                rf"{selector}\s*\{{[^}}]*order:\s*{order};[^}}]*\}}",
            )

    def test_white_stones_have_contrasting_boundaries_in_both_color_schemes(self):
        css = (ROOT / "assets/css/go-board.css").read_text(encoding="utf-8")
        white_stone_rules = re.findall(
            r"\.go-board \.besogo-svg-whiteStone\s*\{(?P<body>[^}]*)\}",
            css,
        )
        self.assertEqual(2, len(white_stone_rules))

        strokes = []
        for rule in white_stone_rules:
            match = re.search(r"stroke:\s*(#[0-9a-fA-F]{6})", rule)
            self.assertIsNotNone(match)
            strokes.append(match.group(1))

        for board, stroke in (("#e0bb6c", strokes[0]), ("#caa35e", strokes[1])):
            self.assertGreaterEqual(contrast_ratio(board, stroke), 3)

    def test_automatic_branch_labels_are_bold_and_contrast_on_both_boards(self):
        css = (ROOT / "assets/css/go-board.css").read_text(encoding="utf-8")
        marker_rule = re.search(
            r'''\.go-board text\[fill=["']#ff474c["']\]\s*\{(?P<body>[^}]*)\}''',
            css,
        )
        self.assertIsNotNone(marker_rule)
        body = marker_rule.group("body")
        fill = re.search(r"fill:\s*(#[0-9a-fA-F]{6})", body)
        halo = re.search(r"stroke:\s*(#[0-9a-fA-F]{6})", body)
        weight = re.search(r"font-weight:\s*([0-9]+)", body)
        stroke_width = re.search(r"stroke-width:\s*([0-9.]+)px", body)
        self.assertIsNotNone(fill)
        self.assertIsNotNone(halo)
        self.assertIsNotNone(weight)
        self.assertIsNotNone(stroke_width)
        self.assertGreaterEqual(int(weight.group(1)), 700)
        self.assertGreaterEqual(float(stroke_width.group(1)), 3)
        self.assertRegex(body, r"paint-order:\s*stroke fill;")
        for board in ("#e0bb6c", "#caa35e"):
            self.assertGreaterEqual(contrast_ratio(board, fill.group(1)), 3)
        self.assertGreaterEqual(contrast_ratio(halo.group(1), fill.group(1)), 3)

    def test_named_variation_buttons_keep_spacing_and_wrap_on_narrow_boards(self):
        css = (ROOT / "assets/css/go-board.css").read_text(encoding="utf-8")
        button_row = re.search(
            r"\.go-board \[data-go-board-variation-buttons\]\s*"
            r"\{(?P<body>[^}]*)\}",
            css,
        )
        self.assertIsNotNone(button_row)
        self.assertRegex(button_row.group("body"), r"display:\s*inline-flex;")
        self.assertRegex(button_row.group("body"), r"flex-wrap:\s*wrap;")
        self.assertRegex(button_row.group("body"), r"gap:\s*0\.5rem;")

        narrow = re.search(
            r"@media \(max-width:\s*480px\)\s*\{(?P<body>.*)\}\s*\Z",
            css,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(narrow)
        self.assertRegex(
            narrow.group("body"),
            r"\.go-board \[data-go-board-variation-buttons\]\s*"
            r"\{[^}]*width:\s*100%;[^}]*\}",
        )

    def test_keyboard_move_controls_wrap_and_stack_on_narrow_boards(self):
        css = (ROOT / "assets/css/go-board.css").read_text(encoding="utf-8")
        controls = re.search(
            r"\.go-board__try-controls\s*\{(?P<body>[^}]*)\}", css
        )
        self.assertIsNotNone(controls)
        self.assertRegex(controls.group("body"), r"display:\s*flex;")
        self.assertRegex(controls.group("body"), r"flex-wrap:\s*wrap;")

        narrow = re.search(
            r"@media \(max-width:\s*480px\)\s*\{(?P<body>.*)\}\s*\Z",
            css,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(narrow)
        self.assertRegex(
            narrow.group("body"),
            r"\.go-board__try-controls\s*\{[^}]*display:\s*grid;[^}]*"
            r"grid-template-columns:\s*repeat\(2,\s*minmax\(0,\s*1fr\)\);",
        )


class GoBoardGeneratedSiteTests(unittest.TestCase):
    def test_boards_are_localized_accessible_conditional_and_base_path_aware(self):
        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)

            for name, base_url, base_path in (
                ("root", "https://example.test/", "/"),
                ("project", "https://example.test/project/", "/project/"),
            ):
                with self.subTest(build=name):
                    public = temporary_root / name / "public"
                    build_site(public, base_url, GO_BOARD_CONTENT)
                    self.assertEqual([], check_site(public, base_url))

                    english = (public / "p/viewer/index.html").read_text(
                        encoding="utf-8"
                    )
                    chinese = (public / "zh/p/viewer/index.html").read_text(
                        encoding="utf-8"
                    )
                    plain = (public / "p/plain/index.html").read_text(
                        encoding="utf-8"
                    )
                    sgf_url = f"{base_path}p/viewer/synthetic.SGF"

                    figures = re.findall(
                        r'<figure[^>]+data-go-board(?:\s|>).*?</figure>',
                        english,
                        flags=re.DOTALL,
                    )
                    self.assertEqual(3, len(figures))
                    for figure in figures:
                        self.assertRegex(
                            figure,
                            re.compile(
                                r'<figcaption id="[^"]+">.*?</figcaption>\s*'
                                r'</figure>\Z',
                                flags=re.DOTALL,
                            ),
                        )
                    self.assertNotIn('<nav class="go-board__controls"', english)
                    control_groups = re.findall(
                        r'<div class="go-board__controls" role="group" '
                        r'aria-labelledby="([^"]+-controls-label) '
                        r'([^"]+-caption)">',
                        english,
                    )
                    self.assertEqual(3, len(control_groups))
                    self.assertEqual(3, len(set(control_groups)))
                    for controls_id, caption_id in control_groups:
                        self.assertIn(
                            f'<span id="{controls_id}" class="visually-hidden">'
                            "Go board controls</span>",
                            english,
                        )
                        self.assertIn(f'<figcaption id="{caption_id}">', english)
                    try_groups = re.findall(
                        r'<div id="(go-board-[0-9a-f]{12}-try-controls)" '
                        r'class="go-board__try-controls" data-go-board-try-controls\s+'
                        r'role="group" aria-labelledby="'
                        r'(go-board-[0-9a-f]{12}-try-controls-label) '
                        r'(go-board-[0-9a-f]{12}-caption)" hidden>',
                        english,
                    )
                    self.assertEqual(3, len(try_groups))
                    self.assertEqual(3, len(set(try_groups)))
                    for group_id, label_id, caption_id in try_groups:
                        figure_id = group_id.removesuffix("-try-controls")
                        self.assertEqual(f"{figure_id}-try-controls-label", label_id)
                        self.assertEqual(f"{figure_id}-caption", caption_id)
                        self.assertRegex(
                            english,
                            rf'<button[^>]+data-go-board-try[^>]+'
                            rf'aria-controls="{group_id}"[^>]+'
                            r'aria-expanded="false"[^>]*>',
                        )
                        self.assertIn(
                            f'<span id="{label_id}" '
                            'class="go-board__try-controls-label">'
                            "Choose a point to play</span>",
                            english,
                        )
                        for axis, label in (("column", "Column"), ("row", "Row")):
                            control_id = f"{figure_id}-try-{axis}"
                            self.assertIn(
                                f'<label for="{control_id}">{label}</label>', english
                            )
                            self.assertIn(
                                f'<select id="{control_id}" '
                                f'data-go-board-try-{axis}></select>',
                                english,
                            )
                        self.assertIn(
                            '<button type="button" data-go-board-play-move>'
                            "Play move</button>",
                            english,
                        )
                        self.assertIn(
                            'data-go-board-try-status role="status" '
                            'aria-live="polite"',
                            english,
                        )
                    variation_groups = re.findall(
                        r'<div id="([^"]+-variations)" '
                        r'class="go-board__variations" data-go-board-variations\s+'
                        r'role="group" aria-labelledby="'
                        r'([^"]+-variations-label) ([^"]+-caption)" hidden>',
                        english,
                    )
                    self.assertEqual(3, len(variation_groups))
                    self.assertEqual(3, len(set(variation_groups)))
                    for _, label_id, caption_id in variation_groups:
                        self.assertIn(
                            f'<span id="{label_id}" '
                            'class="go-board__variations-label">'
                            "Choose a variation</span>",
                            english,
                        )
                        self.assertIn(f'<figcaption id="{caption_id}">', english)
                    self.assertEqual(
                        3,
                        english.count(
                            'data-go-board-variation-status role="status" '
                            'aria-live="polite"'
                        ),
                    )
                    self.assertEqual(
                        1,
                        len(re.findall(r'<figure[^>]+data-go-board(?:\s|>)', chinese)),
                    )
                    self.assertIn('data-selector-kind="move"', english)
                    self.assertIn('data-selector-value="2"', english)
                    self.assertIn('data-selector-kind="path"', english)
                    self.assertIn('data-selector-value="N3B2"', english)
                    start_figure = next(
                        figure for figure in figures
                        if ">Start position</figcaption>" in figure
                    )
                    self.assertIn('data-selector-kind="move"', start_figure)
                    self.assertIn('data-selector-value="0"', start_figure)
                    self.assertIn('>Move 0</output>', start_figure)
                    self.assertEqual(3, english.count(f'data-sgf-url="{sgf_url}"'))
                    self.assertIn(f'href="{sgf_url}" download', english)
                    self.assertTrue((public / "p/viewer/synthetic.SGF").is_file())

                    figure_ids = re.findall(
                        r'<figure id="(go-board-[0-9a-f]{12})"', english
                    )
                    self.assertEqual(3, len(figure_ids))
                    self.assertEqual(3, len(set(figure_ids)))
                    for figure_id in figure_ids:
                        self.assertIn(f'id="{figure_id}-caption"', english)
                        self.assertIn(
                            f'aria-labelledby="{figure_id}-caption"', english
                        )

                    repeat_public = temporary_root / f"{name}-repeat" / "public"
                    build_site(repeat_public, base_url, GO_BOARD_CONTENT)
                    repeat_english = (
                        repeat_public / "p/viewer/index.html"
                    ).read_text(encoding="utf-8")
                    self.assertEqual(
                        figure_ids,
                        re.findall(
                            r'<figure id="(go-board-[0-9a-f]{12})"',
                            repeat_english,
                        ),
                    )

                    self.assertIn(
                        "Main &amp; &lt;strong&gt;board&lt;/strong&gt;", english
                    )
                    self.assertNotIn("<strong>board</strong>", english)
                    for label in (
                        "Previous",
                        "Move {move}",
                        "Next",
                        "Choose a variation",
                        "Variation {label}",
                        "Variation {label} selected",
                        "Try your own line",
                        "Choose a point to play",
                        "Column",
                        "Row",
                        "Choose column",
                        "Choose row",
                        "Play move",
                        "Choose a column and row.",
                        "That point cannot be played.",
                        "Played {coordinate}.",
                        "Return to position",
                        "Current-position note",
                        "Your variations stay in this browser",
                        "Download SGF",
                        "Enable JavaScript to use the interactive board",
                    ):
                        self.assertIn(label, english)
                    for label in (
                        "上一步",
                        "第 {move} 手",
                        "下一步",
                        "选择变化",
                        "变化 {label}",
                        "已选择变化 {label}",
                        "试走变化",
                        "选择试走位置",
                        "列",
                        "行",
                        "选择列",
                        "选择行",
                        "落子",
                        "请选择列和行。",
                        "该位置无法落子。",
                        "已在 {coordinate} 落子。",
                        "返回指定局面",
                        "当前局面注释",
                        "试走变化只保存在当前浏览器中",
                        "下载 SGF 棋谱",
                        "请启用 JavaScript 以使用交互式棋盘",
                    ):
                        self.assertIn(label, chinese)
                    self.assertIn("<noscript>", english)
                    self.assertIn('role="status" aria-live="polite"', english)
                    self.assertIn('aria-busy="true"', english)
                    css_links = re.findall(
                        rf'<link rel="stylesheet" href="{re.escape(base_path)}css/'
                        r'go-board(?:\.min)?\.[0-9a-f]+\.css" '
                        r'integrity="sha256-[^"]+">',
                        english,
                    )
                    scripts = re.findall(
                        rf'<script defer src="{re.escape(base_path)}js/'
                        r'go-board\.[0-9a-f]+\.js" '
                        r'integrity="sha256-[^"]+"></script>',
                        english,
                    )
                    self.assertEqual(
                        1,
                        len(css_links),
                        re.findall(r'<link[^>]+go-board[^>]*>', english),
                    )
                    self.assertEqual(
                        1,
                        len(scripts),
                        re.findall(r'<script[^>]+go-board[^>]*>', english),
                    )
                    self.assertNotRegex(
                        "\n".join([*figures, *css_links, *scripts]),
                        r'https?://',
                    )
                    self.assertEqual(1, len(re.findall(r"css/go-board", chinese)))
                    self.assertEqual(1, len(re.findall(r"js/go-board", chinese)))
                    self.assertNotIn("css/go-board", plain)
                    self.assertNotIn("js/go-board", plain)

                    built_scripts = list((public / "js").glob("go-board.*.js"))
                    self.assertEqual(1, len(built_scripts))
                    runtime = built_scripts[0].read_text(encoding="utf-8")
                    built_styles = list((public / "css").glob("go-board.*.css"))
                    self.assertEqual(1, len(built_styles))
                    stylesheet = built_styles[0].read_text(encoding="utf-8")
                    js_payload = built_scripts[0].read_bytes()
                    css_payload = built_styles[0].read_bytes()
                    js_gzip = len(gzip.compress(js_payload, compresslevel=9, mtime=0))
                    css_gzip = len(gzip.compress(css_payload, compresslevel=9, mtime=0))
                    self.assertLessEqual(len(js_payload), 32_000)
                    self.assertLessEqual(js_gzip, 11_000)
                    self.assertLessEqual(len(css_payload), 5_000)
                    self.assertLessEqual(css_gzip, 1_500)
                    self.assertLessEqual(js_gzip + css_gzip, 12_500)
                    self.assertNotRegex(stylesheet, r'https?://')
                    absolute_runtime_urls = set(
                        re.findall(r'''https?://[^"'\s<>)]+''', runtime)
                    )
                    self.assertEqual(
                        set(),
                        absolute_runtime_urls - {
                            "http://www.w3.org/1999/xlink",
                            "http://www.w3.org/2000/svg",
                        },
                    )
                    for omitted_panel in (
                        "makeControlPanel",
                        "makeNamesPanel",
                        "makeCommentPanel",
                        "makeToolPanel",
                        "makeTreePanel",
                        "makeFilePanel",
                    ):
                        self.assertNotIn(omitted_panel, runtime)

    def test_shortcode_rejects_invalid_arguments_and_resources(self):
        cases = (
            (
                "positional",
                '{{< go-board "synthetic.sgf" "Caption" >}}',
                r"go-board at .*named arguments",
            ),
            (
                "unknown-parameter",
                '{{< go-board src="synthetic.sgf" caption="Caption" mvoe="2" >}}',
                r'go-board at .*unknown named argument "mvoe"',
            ),
            (
                "missing-src",
                '{{< go-board caption="Caption" >}}',
                r"go-board at .*src must be non-empty",
            ),
            (
                "empty-caption",
                '{{< go-board src="synthetic.sgf" caption="  " >}}',
                r"go-board at .*caption must be non-empty",
            ),
            (
                "wrong-extension",
                '{{< go-board src="record.txt" caption="Caption" >}}',
                r"go-board at .*src must name a local \.sgf resource",
            ),
            (
                "missing-resource",
                '{{< go-board src="missing.sgf" caption="Caption" >}}',
                r"go-board at .*resource .*missing\.sgf.*not found.*page bundle",
            ),
            (
                "negative-move",
                '{{< go-board src="synthetic.sgf" caption="Caption" move="-1" >}}',
                r"go-board at .*move .*non-negative integer",
            ),
            (
                "fractional-move",
                '{{< go-board src="synthetic.sgf" caption="Caption" move="1.5" >}}',
                r"go-board at .*move .*non-negative integer",
            ),
            (
                "move-path-conflict",
                '{{< go-board src="synthetic.sgf" caption="Caption" move="0" path="N1" >}}',
                r"go-board at .*move and path are mutually exclusive",
            ),
            (
                "empty-path",
                '{{< go-board src="synthetic.sgf" caption="Caption" path="" >}}',
                r"go-board at .*path .*N<number> and B<positive-number>",
            ),
            (
                "bad-path-zero-branch",
                '{{< go-board src="synthetic.sgf" caption="Caption" path="N1B0" >}}',
                r"go-board at .*path .*N<number> and B<positive-number>",
            ),
            (
                "bad-path-spacing",
                '{{< go-board src="synthetic.sgf" caption="Caption" path="N1 B2" >}}',
                r"go-board at .*path .*N<number> and B<positive-number>",
            ),
            (
                "bad-path-case",
                '{{< go-board src="synthetic.sgf" caption="Caption" path="N1b2" >}}',
                r"go-board at .*path .*N<number> and B<positive-number>",
            ),
        )

        with TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            for name, shortcode, error_pattern in cases:
                with self.subTest(case=name):
                    content = temporary_root / name / "content"
                    bundle = content / "blog/invalid"
                    write_page(
                        bundle / "index.en.md",
                        title="Invalid Go board",
                        interaction_id=f"invalid-go-board-{name}",
                        body=shortcode,
                    )
                    shutil.copyfile(SYNTHETIC_SGF, bundle / "synthetic.sgf")
                    (bundle / "record.txt").write_text(
                        SYNTHETIC_SGF.read_text(encoding="utf-8"),
                        encoding="utf-8",
                    )
                    result = run_hugo(
                        temporary_root / name / "public",
                        content,
                    )
                    self.assertNotEqual(0, result.returncode)
                    output = "\n".join((result.stdout, result.stderr))
                    self.assertRegex(output, error_pattern)
                    self.assertNotRegex(
                        output,
                        r"(?i)nil pointer|index out of range|can't evaluate field",
                    )


if __name__ == "__main__":
    unittest.main()
