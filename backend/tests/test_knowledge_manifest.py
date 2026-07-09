"""Tests for knowledge indexing manifest loading."""

import tempfile
import unittest
from pathlib import Path

from app.knowledge.manifest import ManifestError, ManifestLoader

VALID_MANIFEST = """\
version: 2
default_language: en
chunk_size: 1200
chunk_overlap: 150
supported_extensions:
  - docx
  - md
"""


class ManifestLoaderTests(unittest.TestCase):
    """Verify dynamic manifest loading and validation."""

    def test_loads_valid_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            manifest_path = Path(temporary_directory) / "manifest.yaml"
            manifest_path.write_text(VALID_MANIFEST, encoding="utf-8")

            manifest = ManifestLoader(manifest_path).load()

        self.assertEqual(manifest.version, 2)
        self.assertEqual(manifest.default_language, "en")
        self.assertEqual(manifest.chunk_size, 1200)
        self.assertEqual(manifest.chunk_overlap, 150)
        self.assertEqual(manifest.supported_extensions, ["docx", "md"])
        self.assertEqual(len(manifest.fingerprint()), 64)

    def test_rejects_invalid_chunk_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            manifest_path = Path(temporary_directory) / "manifest.yaml"
            manifest_path.write_text(
                VALID_MANIFEST.replace(
                    "chunk_overlap: 150",
                    "chunk_overlap: 1200",
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ManifestError):
                ManifestLoader(manifest_path).load()

    def test_rejects_malformed_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            manifest_path = Path(temporary_directory) / "manifest.yaml"
            manifest_path.write_text("version: [", encoding="utf-8")

            with self.assertRaises(ManifestError):
                ManifestLoader(manifest_path).load()

    def test_rejects_unsupported_extensions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            manifest_path = Path(temporary_directory) / "manifest.yaml"
            manifest_path.write_text(
                VALID_MANIFEST.replace("  - md", "  - pdf"),
                encoding="utf-8",
            )

            with self.assertRaises(ManifestError):
                ManifestLoader(manifest_path).load()


if __name__ == "__main__":
    unittest.main()
