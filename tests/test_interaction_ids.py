import tempfile
import unittest
from pathlib import Path

from scripts.validate_interaction_ids import read_front_matter, validate_content


class InteractionIdValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.content_root = Path(self.temporary_directory.name) / "content"

    def tearDown(self):
        self.temporary_directory.cleanup()

    def write_post(
        self,
        bundle: str,
        language: str,
        *,
        section: str = "blog",
        draft: bool = False,
        interaction_id=...,
    ) -> Path:
        front_matter = [
            'title = "Test post"',
            f"draft = {'true' if draft else 'false'}",
        ]
        if interaction_id is not ...:
            if isinstance(interaction_id, str):
                value = f'"{interaction_id}"'
            else:
                value = str(interaction_id)
            front_matter.append(f"interactionId = {value}")

        post_path = self.content_root / section / bundle / f"index.{language}.md"
        post_path.parent.mkdir(parents=True, exist_ok=True)
        post_path.write_text(
            "+++\n" + "\n".join(front_matter) + "\n+++\n\nBody.\n",
            encoding="utf-8",
        )
        return post_path

    def test_missing_content_root_is_rejected(self):
        errors = validate_content(self.content_root)

        self.assertEqual(len(errors), 1)
        self.assertIn("content root is not a directory", errors[0])
        self.assertIn(str(self.content_root), errors[0])

    def test_valid_english_and_chinese_translations_share_an_id(self):
        self.write_post("shared", "en", interaction_id="shared-post")
        self.write_post("shared", "zh", interaction_id="shared-post")

        self.assertEqual(validate_content(self.content_root), [])

    def test_published_post_without_an_id_is_rejected(self):
        self.write_post("missing", "en")

        errors = validate_content(self.content_root)

        self.assertEqual(len(errors), 1)
        self.assertIn("interactionId is required for published articles", errors[0])

    def test_project_translations_share_an_id(self):
        self.write_post(
            "shared-project",
            "en",
            section="projects",
            interaction_id="shared-project",
        )
        self.write_post(
            "shared-project",
            "zh",
            section="projects",
            interaction_id="shared-project",
        )

        self.assertEqual(validate_content(self.content_root), [])

    def test_published_project_without_an_id_is_rejected(self):
        self.write_post("missing-project", "en", section="projects")

        errors = validate_content(self.content_root)

        self.assertEqual(1, len(errors))
        self.assertIn("interactionId is required for published articles", errors[0])

    def test_draft_post_may_omit_an_id(self):
        self.write_post("draft", "en", draft=True)

        self.assertEqual(validate_content(self.content_root), [])

    def test_draft_post_with_an_empty_id_is_rejected(self):
        self.write_post("draft-empty", "en", draft=True, interaction_id="")

        errors = validate_content(self.content_root)

        self.assertEqual(len(errors), 1)
        self.assertIn("interactionId must be 1 to 80 characters", errors[0])

    def test_malformed_id_is_rejected(self):
        self.write_post("malformed", "en", interaction_id="Bad ID")

        errors = validate_content(self.content_root)

        self.assertEqual(len(errors), 1)
        self.assertIn("interactionId must match", errors[0])

    def test_non_string_id_is_rejected(self):
        self.write_post("non-string", "en", interaction_id=42)

        errors = validate_content(self.content_root)

        self.assertEqual(len(errors), 1)
        self.assertIn("interactionId must be a string", errors[0])

    def test_id_longer_than_eighty_characters_is_rejected(self):
        self.write_post("too-long", "en", interaction_id="a" * 81)

        errors = validate_content(self.content_root)

        self.assertEqual(len(errors), 1)
        self.assertIn("interactionId must be 1 to 80 characters", errors[0])

    def test_translations_in_one_bundle_must_share_an_id(self):
        self.write_post("mismatch", "en", interaction_id="english-id")
        self.write_post("mismatch", "zh", interaction_id="chinese-id")

        errors = validate_content(self.content_root)

        self.assertEqual(len(errors), 1)
        self.assertIn("translations in bundle", errors[0])
        self.assertIn("must share one interactionId", errors[0])

    def test_project_translations_must_share_an_id(self):
        self.write_post(
            "mismatched-project",
            "en",
            section="projects",
            interaction_id="english-project",
        )
        self.write_post(
            "mismatched-project",
            "zh",
            section="projects",
            interaction_id="chinese-project",
        )

        errors = validate_content(self.content_root)

        self.assertEqual(1, len(errors))
        self.assertIn("translations in bundle", errors[0])
        self.assertIn("must share one interactionId", errors[0])

    def test_unrelated_bundles_cannot_reuse_an_id(self):
        self.write_post("first", "en", interaction_id="duplicate-id")
        self.write_post("second", "en", interaction_id="duplicate-id")

        errors = validate_content(self.content_root)

        self.assertEqual(len(errors), 1)
        self.assertIn("interactionId 'duplicate-id' is reused by bundles", errors[0])

    def test_blog_and_project_bundles_cannot_reuse_an_id(self):
        self.write_post(
            "article",
            "en",
            section="blog",
            interaction_id="duplicate-id",
        )
        self.write_post(
            "project",
            "en",
            section="projects",
            interaction_id="duplicate-id",
        )

        errors = validate_content(self.content_root)

        self.assertEqual(1, len(errors))
        self.assertIn("interactionId 'duplicate-id' is reused by bundles", errors[0])


if __name__ == "__main__":
    unittest.main()
