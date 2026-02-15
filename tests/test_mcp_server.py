"""Tests for MCP server tools."""

import json
from datetime import datetime
from types import SimpleNamespace
from unittest import mock

import pytest

pytest.importorskip("mcp")

from semanticscholar.mcp_server import (
    ABSTRACT_MAX,
    _author_to_dict,
    _paper_to_dict,
    _truncate,
    get_author,
    get_author_papers,
    get_paper,
    get_paper_citations,
    get_paper_references,
    get_recommendations,
    search_authors,
    search_papers,
    search_snippets,
)


def _make_paper(**kwargs):
    defaults = dict(
        paperId="abc123",
        title="Test Paper",
        abstract="This is a test abstract.",
        year=2023,
        citationCount=42,
        url="https://example.com/paper",
        authors=[SimpleNamespace(authorId="auth1", name="Author One")],
        externalIds={"DOI": "10.1234/test"},
        venue="TestConf",
        publicationDate=datetime(2023, 1, 15),
        openAccessPdf={"url": "https://example.com/pdf"},
        tldr=SimpleNamespace(text="A short summary."),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _make_author(**kwargs):
    defaults = dict(
        authorId="auth1",
        name="Author One",
        url="https://example.com/author",
        paperCount=50,
        citationCount=1000,
        hIndex=20,
        affiliations=["Test University"],
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _make_paginated(items, total=None):
    if total is None:
        total = len(items)
    result = mock.MagicMock()
    result.total = total
    result.__iter__ = mock.Mock(return_value=iter(items))
    result.__getitem__ = lambda self, key: items[key]
    result.__len__ = mock.Mock(return_value=len(items))
    return result


# --- helper functions ---


class TestTruncate:
    def test_short_text(self):
        assert _truncate("short") == "short"

    def test_long_text(self):
        text = "x" * (ABSTRACT_MAX + 50)
        result = _truncate(text)
        assert len(result) == ABSTRACT_MAX + 3
        assert result.endswith("...")

    def test_none(self):
        assert _truncate(None) is None

    def test_empty(self):
        assert _truncate("") == ""


class TestPaperToDict:
    def test_full_paper(self):
        paper = _make_paper()
        d = _paper_to_dict(paper)
        assert d["paperId"] == "abc123"
        assert d["title"] == "Test Paper"
        assert d["year"] == 2023
        assert d["citationCount"] == 42
        assert d["authors"] == [{"authorId": "auth1", "name": "Author One"}]
        assert d["externalIds"] == {"DOI": "10.1234/test"}
        assert d["venue"] == "TestConf"
        assert d["publicationDate"] == "2023-01-15"
        assert d["openAccessPdf"] == {"url": "https://example.com/pdf"}
        assert d["tldr"] == "A short summary."

    def test_null_fields_omitted(self):
        paper = _make_paper(
            abstract=None,
            authors=None,
            externalIds=None,
            venue=None,
            publicationDate=None,
            openAccessPdf=None,
            tldr=None,
        )
        d = _paper_to_dict(paper)
        for key in (
            "abstract",
            "authors",
            "venue",
            "publicationDate",
            "openAccessPdf",
            "tldr",
        ):
            assert key not in d

    def test_abstract_truncated(self):
        paper = _make_paper(abstract="x" * (ABSTRACT_MAX + 100))
        d = _paper_to_dict(paper)
        assert d["abstract"].endswith("...")
        assert len(d["abstract"]) == ABSTRACT_MAX + 3


class TestAuthorToDict:
    def test_full_author(self):
        author = _make_author()
        d = _author_to_dict(author)
        assert d["authorId"] == "auth1"
        assert d["name"] == "Author One"
        assert d["paperCount"] == 50
        assert d["hIndex"] == 20
        assert d["affiliations"] == ["Test University"]

    def test_null_fields_omitted(self):
        author = _make_author(
            url=None,
            paperCount=None,
            citationCount=None,
            hIndex=None,
            affiliations=None,
        )
        d = _author_to_dict(author)
        for key in ("url", "paperCount", "citationCount", "hIndex", "affiliations"):
            assert key not in d


# --- tool functions ---


class TestSearchPapers:
    @mock.patch("semanticscholar.mcp_server._sch")
    def test_basic_search(self, mock_sch):
        paper = _make_paper()
        mock_sch.search_paper.return_value = _make_paginated([paper], total=1)
        result = json.loads(search_papers("test query"))
        assert result["total"] == 1
        assert len(result["papers"]) == 1
        assert result["papers"][0]["title"] == "Test Paper"
        mock_sch.search_paper.assert_called_once_with(
            "test query",
            year=None,
            fields_of_study=None,
            publication_date_or_year=None,
            min_citation_count=None,
            limit=10,
        )

    @mock.patch("semanticscholar.mcp_server._sch")
    def test_fields_of_study_split(self, mock_sch):
        mock_sch.search_paper.return_value = _make_paginated([])
        search_papers("query", fields_of_study="Computer Science,Mathematics")
        call_kwargs = mock_sch.search_paper.call_args[1]
        assert call_kwargs["fields_of_study"] == ["Computer Science", "Mathematics"]

    @mock.patch("semanticscholar.mcp_server._sch")
    def test_limit_clamped_to_100(self, mock_sch):
        mock_sch.search_paper.return_value = _make_paginated([])
        search_papers("query", limit=200)
        call_kwargs = mock_sch.search_paper.call_args[1]
        assert call_kwargs["limit"] == 100


class TestGetPaper:
    @mock.patch("semanticscholar.mcp_server._sch")
    def test_get_paper(self, mock_sch):
        mock_sch.get_paper.return_value = _make_paper(paperId="xyz")
        result = json.loads(get_paper("xyz"))
        assert result["paperId"] == "xyz"
        mock_sch.get_paper.assert_called_once_with("xyz")


class TestGetPaperCitations:
    @mock.patch("semanticscholar.mcp_server._sch")
    def test_returns_citations(self, mock_sch):
        citation = SimpleNamespace(
            paper=_make_paper(paperId="cite1", title="Citing Paper")
        )
        mock_sch.get_paper_citations.return_value = _make_paginated([citation])
        result = json.loads(get_paper_citations("paper1"))
        assert len(result["citations"]) == 1
        assert result["citations"][0]["paperId"] == "cite1"

    @mock.patch("semanticscholar.mcp_server._sch")
    def test_null_paper_skipped(self, mock_sch):
        items = [
            SimpleNamespace(paper=None),
            SimpleNamespace(paper=_make_paper(paperId="valid")),
        ]
        mock_sch.get_paper_citations.return_value = _make_paginated(items)
        result = json.loads(get_paper_citations("paper1"))
        assert len(result["citations"]) == 1
        assert result["citations"][0]["paperId"] == "valid"

    @mock.patch("semanticscholar.mcp_server._sch")
    def test_limit_clamped_to_1000(self, mock_sch):
        mock_sch.get_paper_citations.return_value = _make_paginated([])
        get_paper_citations("paper1", limit=2000)
        call_kwargs = mock_sch.get_paper_citations.call_args[1]
        assert call_kwargs["limit"] == 1000


class TestGetPaperReferences:
    @mock.patch("semanticscholar.mcp_server._sch")
    def test_returns_references(self, mock_sch):
        ref = SimpleNamespace(paper=_make_paper(paperId="ref1", title="Ref Paper"))
        mock_sch.get_paper_references.return_value = _make_paginated([ref])
        result = json.loads(get_paper_references("paper1"))
        assert len(result["references"]) == 1
        assert result["references"][0]["paperId"] == "ref1"

    @mock.patch("semanticscholar.mcp_server._sch")
    def test_null_paper_skipped(self, mock_sch):
        mock_sch.get_paper_references.return_value = _make_paginated(
            [SimpleNamespace(paper=None)]
        )
        result = json.loads(get_paper_references("paper1"))
        assert len(result["references"]) == 0


class TestSearchSnippets:
    @mock.patch("semanticscholar.mcp_server._sch")
    def test_returns_snippets(self, mock_sch):
        item = SimpleNamespace(
            paper=_make_paper(paperId="s1", title="Snippet Paper"),
            snippet=SimpleNamespace(
                text="matching text", snippetKind="abstract", section="Abstract"
            ),
            score=0.95,
        )
        mock_sch.search_snippet.return_value = [item]
        result = json.loads(search_snippets("query"))
        assert len(result["results"]) == 1
        assert result["results"][0]["score"] == 0.95
        assert result["results"][0]["paper"]["paperId"] == "s1"
        assert result["results"][0]["snippet"]["text"] == "matching text"

    @mock.patch("semanticscholar.mcp_server._sch")
    def test_null_paper_and_snippet(self, mock_sch):
        item = SimpleNamespace(paper=None, snippet=None, score=0.5)
        mock_sch.search_snippet.return_value = [item]
        result = json.loads(search_snippets("query"))
        assert "paper" not in result["results"][0]
        assert "snippet" not in result["results"][0]
        assert result["results"][0]["score"] == 0.5

    @mock.patch("semanticscholar.mcp_server._sch")
    def test_fields_of_study_split(self, mock_sch):
        mock_sch.search_snippet.return_value = []
        search_snippets("query", fields_of_study="Physics,Biology")
        call_kwargs = mock_sch.search_snippet.call_args[1]
        assert call_kwargs["fields_of_study"] == ["Physics", "Biology"]

    @mock.patch("semanticscholar.mcp_server._sch")
    def test_limit_clamped_to_1000(self, mock_sch):
        mock_sch.search_snippet.return_value = []
        search_snippets("query", limit=2000)
        call_kwargs = mock_sch.search_snippet.call_args[1]
        assert call_kwargs["limit"] == 1000


class TestSearchAuthors:
    @mock.patch("semanticscholar.mcp_server._sch")
    def test_returns_authors(self, mock_sch):
        author = _make_author()
        mock_sch.search_author.return_value = _make_paginated([author], total=1)
        result = json.loads(search_authors("Author One"))
        assert result["total"] == 1
        assert result["authors"][0]["name"] == "Author One"


class TestGetAuthor:
    @mock.patch("semanticscholar.mcp_server._sch")
    def test_get_author(self, mock_sch):
        mock_sch.get_author.return_value = _make_author(authorId="a1")
        result = json.loads(get_author("a1"))
        assert result["authorId"] == "a1"


class TestGetAuthorPapers:
    @mock.patch("semanticscholar.mcp_server._sch")
    def test_returns_papers(self, mock_sch):
        paper = _make_paper()
        mock_sch.get_author_papers.return_value = _make_paginated([paper])
        result = json.loads(get_author_papers("a1"))
        assert len(result["papers"]) == 1
        assert result["papers"][0]["title"] == "Test Paper"

    @mock.patch("semanticscholar.mcp_server._sch")
    def test_limit_clamped_to_1000(self, mock_sch):
        mock_sch.get_author_papers.return_value = _make_paginated([])
        get_author_papers("a1", limit=2000)
        call_kwargs = mock_sch.get_author_papers.call_args[1]
        assert call_kwargs["limit"] == 1000


class TestGetRecommendations:
    @mock.patch("semanticscholar.mcp_server._sch")
    def test_returns_recommendations(self, mock_sch):
        paper = _make_paper()
        mock_sch.get_recommended_papers.return_value = [paper]
        result = json.loads(get_recommendations("paper1"))
        assert len(result["papers"]) == 1

    @mock.patch("semanticscholar.mcp_server._sch")
    def test_limit_clamped_to_500(self, mock_sch):
        mock_sch.get_recommended_papers.return_value = []
        get_recommendations("paper1", limit=1000)
        call_kwargs = mock_sch.get_recommended_papers.call_args[1]
        assert call_kwargs["limit"] == 500
