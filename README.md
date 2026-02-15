# semanticscholar

[![GitHub license](https://img.shields.io/github/license/mulatta/semanticscholar?style=for-the-badge)](https://github.com/mulatta/semanticscholar/blob/main/LICENSE)

Python client library for [Semantic Scholar APIs](https://api.semanticscholar.org/), forked from [danielnsilva/semanticscholar](https://github.com/danielnsilva/semanticscholar).

## Features

- Full coverage of Semantic Scholar APIs (Academic Graph, Recommendations, Datasets, Snippet Search)
- MCP server for LLM tool integration
- Typed responses with paginated result navigation
- Async and sync interfaces
- Exponential backoff retry

## Installation

```console
pip install git+https://github.com/mulatta/semanticscholar.git
```

With MCP server support:

```console
pip install "semanticscholar[mcp] @ git+https://github.com/mulatta/semanticscholar.git"
```

## Usage

```python
from semanticscholar import SemanticScholar

sch = SemanticScholar()

# Search papers
results = sch.search_paper("deep learning")
print(results[0].title)

# Get a paper by ID
paper = sch.get_paper("10.1093/mind/lix.236.433")
print(paper.title)

# Snippet search (full-text search within papers)
snippets = sch.search_snippet("attention mechanism", limit=5)
for s in snippets:
    print(s.snippet.text, s.paper.title)
```

## MCP Server

Run the MCP server for use with Claude Code or other MCP clients:

```console
semanticscholar-mcp
```

Available tools: `search_papers`, `get_paper`, `get_paper_citations`, `get_paper_references`, `search_snippets`, `search_authors`, `get_author`, `get_author_papers`, `get_recommendations`

Set `S2_API_KEY` environment variable for authenticated access with higher rate limits.

## API Documentation

- [Semantic Scholar API docs](https://api.semanticscholar.org/api-docs/graph)
- [FAQ](https://www.semanticscholar.org/faq)
