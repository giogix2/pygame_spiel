"""Local links, example syntax and source identity; no runtime qualification."""

import ast
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit

import pygame_spiel

ROOT = Path(__file__).resolve().parents[1]


class DocumentationTests(unittest.TestCase):
    def test_checks_target_this_checkout(self):
        self.assertEqual(Path(pygame_spiel.__file__).resolve(), ROOT / "pygame_spiel/__init__.py")

    def test_local_documentation_links_and_python_examples(self):
        for doc in [*ROOT.glob("*.md"), *ROOT.glob("docs/**/*.md")]:
            text = doc.read_text(encoding="utf-8")
            for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', text):
                url = urlsplit(target.strip("<>"))
                if url.scheme or url.netloc:
                    continue
                path = (doc.parent / unquote(url.path)).resolve() if url.path else doc
                with self.subTest(doc=doc.name, target=target):
                    self.assertTrue(path.exists(), str(path))
                    if url.fragment and path.suffix == ".md":
                        headings = re.findall(r'^#+\s+(.+)$', path.read_text(encoding="utf-8"), re.M)
                        anchors = {re.sub(r'[^\w\- ]', '', h.lower()).replace(' ', '-') for h in headings}
                        self.assertIn(unquote(url.fragment), anchors)
            for index, snippet in enumerate(re.findall(r'```python\n(.*?)```', text, re.S)):
                compile(snippet, f"{doc}:{index}", "exec")

    def test_python_sources_parse(self):
        for folder in (ROOT / "pygame_spiel", ROOT / "tests"):
            for path in folder.rglob("*.py"):
                with self.subTest(path=path.relative_to(ROOT)):
                    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
