"""Small wrapper around the arXiv API (Atom feed)

Provides a tiny `ArxivClient` with `search` and `get` and a parser for the
Atom XML returned by arXiv. Uses `requests` for HTTP and `feedparser` to
parse Atom.
"""
from typing import List, Dict, Optional
from xml.etree import ElementTree as ET

class ArxivClient:
    """Client for querying the arXiv API.

    Methods:
    - search(query, start=0, max_results=10, sort_by='relevance', sort_order='descending') -> List[dict]
    - get(arxiv_id) -> dict | None
    - parse_feed(atom_text) -> List[dict]

    The returned dicts include keys: 'id', 'title', 'summary', 'published',
    'updated', 'authors', 'pdf_url', 'categories', 'primary_category'.
    """

    BASE_URL = "http://export.arxiv.org/api/query"

    def __init__(self, session: Optional[object] = None, base_url: Optional[str] = None):
        self.session = session
        self.base_url = base_url or self.BASE_URL

    def search(self, query: str, start: int = 0, max_results: int = 10, sort_by: str = "relevance", sort_order: str = "descending") -> List[Dict]:
        """Search arXiv using the query string.

        `query` should be in the arXiv query language, for example:
        - 'all:electron'
        - 'au:Einstein'
        - 'cat:cs.CL'

        Returns a list of entry dicts parsed from the Atom feed.
        """
        # import requests lazily so consumers who only use parse_feed don't need it installed
        import requests

        params = {
            "search_query": query,
            "start": start,
            "max_results": max_results,
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }
        resp = self.session.get(self.base_url, params=params, timeout=15)
        resp.raise_for_status()
        return self.parse_feed(resp.text)

    def get(self, arxiv_id: str) -> Optional[Dict]:
        """Get a single entry by arXiv id (e.g. '2101.00001' or 'hep-th/9901001')."""
        results = self.search(f"id:{arxiv_id}", max_results=1)
        return results[0] if results else None

    def parse_feed(self, atom_text: str) -> List[Dict]:
        """Parse Atom XML (string) produced by the arXiv API into a list of dicts.

        This is a small, forgiving parser using ElementTree that extracts the
        common fields we care about from the arXiv Atom feed.
        """
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
        }
        root = ET.fromstring(atom_text)
        entries = []
        for entry in root.findall("atom:entry", ns):
            # id
            raw_id_el = entry.find("atom:id", ns)
            raw_id = raw_id_el.text if raw_id_el is not None else None
            arxiv_id = None
            if raw_id and "/abs/" in raw_id:
                arxiv_id = raw_id.split("/abs/")[-1]

            # title and summary
            title_el = entry.find("atom:title", ns)
            summary_el = entry.find("atom:summary", ns)
            title = title_el.text.strip() if title_el is not None and title_el.text else ""
            summary = summary_el.text.strip() if summary_el is not None and summary_el.text else ""

            # published / updated
            published_el = entry.find("atom:published", ns)
            updated_el = entry.find("atom:updated", ns)
            published = published_el.text if published_el is not None else None
            updated = updated_el.text if updated_el is not None else None

            # authors
            authors = []
            for a in entry.findall("atom:author", ns):
                name_el = a.find("atom:name", ns)
                if name_el is not None and name_el.text:
                    authors.append(name_el.text.strip())

            # links: find application/pdf link or link with title 'pdf'
            pdf_url = None
            for link in entry.findall("atom:link", ns):
                ltype = link.get("type")
                ltitle = link.get("title")
                href = link.get("href")
                if ltype == "application/pdf" or (ltitle and ltitle.lower() == "pdf"):
                    pdf_url = href
                    break

            # categories
            categories = [c.get("term") for c in entry.findall("atom:category", ns) if c.get("term")]
            primary_category = None
            pc = entry.find("arxiv:primary_category", ns)
            if pc is not None:
                primary_category = pc.get("term")

            entries.append({
                "id": arxiv_id,
                "raw_id": raw_id,
                "title": title,
                "summary": summary,
                "published": published,
                "updated": updated,
                "authors": authors,
                "pdf_url": pdf_url,
                "categories": categories,
                "primary_category": primary_category,
                "_raw_entry": entry,
            })

        return entries
