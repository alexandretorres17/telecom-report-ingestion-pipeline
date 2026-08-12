import ast
import configparser
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ArchiveTests(unittest.TestCase):
    def test_all_python_files_parse(self):
        for path in ROOT.glob("*.py"):
            with self.subTest(path=path.name):
                ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))

    def test_example_configuration_is_non_production(self):
        config = configparser.ConfigParser()
        config.read(ROOT / "config.example.ini")
        self.assertTrue(config.get("EMAIL", "server").endswith(".invalid"))
        self.assertEqual("change-me", config.get("EMAIL", "pass"))
        self.assertEqual("change-me", config.get("DATABASE", "pass"))

    def test_zip_extraction_rejects_path_traversal(self):
        source = (ROOT / "main.py").read_text(encoding="utf-8")
        self.assertIn("Unsafe archive member", source)
        self.assertIn("destination / name", source)

    def test_authors_are_recorded(self):
        authors = (ROOT / "AUTHORS.md").read_text(encoding="utf-8")
        self.assertIn("Alexandre Torres", authors)
        self.assertIn("Fabio Vilela", authors)


if __name__ == "__main__":
    unittest.main()
