# arXiv API wrapper

Small, dependency-light wrapper around the arXiv Atom API.

Usage example:

```python
from arxiv_api import ArxivClient

client = ArxivClient()
results = client.search('all:quantum', max_results=5)
for r in results:
    print(r['id'], r['title'])
```

Development

- Install dependencies from `requirements.txt`.
- Run tests with `pytest`.
