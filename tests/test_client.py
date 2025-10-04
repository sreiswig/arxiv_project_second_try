import os
import sys

# Make sure the top-level `src` directory is on sys.path so tests can import
# the local package without installing it.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from arxiv_api.client import ArxivClient


def load_fixture():
    path = __import__("os").path
    here = path.dirname(__file__)
    with open(path.join(here, "fixtures", "sample_response.atom"), "r", encoding="utf-8") as f:
        return f.read()


def test_parse_feed_minimal():
    atom = load_fixture()
    c = ArxivClient()
    entries = c.parse_feed(atom)
    assert len(entries) == 1
    e = entries[0]
    assert e["id"].startswith("2101.")
    assert "Quantum" in e["title"]
    assert e["pdf_url"] and "pdf" in e["pdf_url"]
    assert isinstance(e["authors"], list) and len(e["authors"]) >= 1
