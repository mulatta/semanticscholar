import json
import os
from typing import Optional

from mcp.server.fastmcp import FastMCP

from semanticscholar.SemanticScholar import SemanticScholar

mcp = FastMCP("semanticscholar")

_api_key = os.environ.get("S2_API_KEY")
_sch = SemanticScholar(api_key=_api_key)

ABSTRACT_MAX = 300


def _truncate(text: str, max_len: int = ABSTRACT_MAX) -> str:
    if text and len(text) > max_len:
        return text[:max_len] + "..."
    return text


def _paper_to_dict(paper) -> dict:
    d = {}
    if paper.paperId:
        d["paperId"] = paper.paperId
    if paper.title:
        d["title"] = paper.title
    if paper.abstract:
        d["abstract"] = _truncate(paper.abstract)
    if paper.year:
        d["year"] = paper.year
    if paper.citationCount is not None:
        d["citationCount"] = paper.citationCount
    if paper.url:
        d["url"] = paper.url
    if paper.authors:
        d["authors"] = [{"authorId": a.authorId, "name": a.name} for a in paper.authors]
    if paper.externalIds:
        d["externalIds"] = paper.externalIds
    if paper.venue:
        d["venue"] = paper.venue
    if paper.publicationDate:
        d["publicationDate"] = str(paper.publicationDate.date())
    if paper.openAccessPdf:
        d["openAccessPdf"] = paper.openAccessPdf
    if paper.tldr:
        d["tldr"] = paper.tldr.text
    return d


def _author_to_dict(author) -> dict:
    d = {}
    if author.authorId:
        d["authorId"] = author.authorId
    if author.name:
        d["name"] = author.name
    if author.url:
        d["url"] = author.url
    if author.paperCount is not None:
        d["paperCount"] = author.paperCount
    if author.citationCount is not None:
        d["citationCount"] = author.citationCount
    if author.hIndex is not None:
        d["hIndex"] = author.hIndex
    if author.affiliations:
        d["affiliations"] = author.affiliations
    return d


@mcp.tool()
def search_papers(
    query: str,
    year: Optional[str] = None,
    fields_of_study: Optional[str] = None,
    publication_date_or_year: Optional[str] = None,
    min_citation_count: Optional[int] = None,
    limit: int = 10,
) -> str:
    """Search for papers by keyword query.

    Args:
        query: Search query string
        year: Year or range (e.g. "2020", "2018-2022")
        fields_of_study: Comma-separated fields (e.g. "Computer Science,Mathematics")
        publication_date_or_year: Date range "YYYY-MM-DD:YYYY-MM-DD"
        min_citation_count: Minimum citations filter
        limit: Max results (1-100, default 10)
    """
    fos = fields_of_study.split(",") if fields_of_study else None
    results = _sch.search_paper(
        query,
        year=year,
        fields_of_study=fos,
        publication_date_or_year=publication_date_or_year,
        min_citation_count=min_citation_count,
        limit=min(limit, 100),
    )
    papers = [_paper_to_dict(p) for p in results[:limit]]
    return json.dumps({"total": results.total, "papers": papers}, indent=2)


@mcp.tool()
def get_paper(paper_id: str) -> str:
    """Get detailed information about a specific paper.

    Args:
        paper_id: S2PaperId, DOI, ArXivId, CorpusId, ACL, PMID, PMCID, or URL
    """
    paper = _sch.get_paper(paper_id)
    return json.dumps(_paper_to_dict(paper), indent=2)


@mcp.tool()
def get_paper_citations(
    paper_id: str,
    limit: int = 20,
) -> str:
    """Get papers that cite the given paper.

    Args:
        paper_id: Paper identifier
        limit: Max results (1-1000, default 20)
    """
    results = _sch.get_paper_citations(
        paper_id, fields=["title"], limit=min(limit, 1000)
    )
    citations = []
    for item in list(results)[:limit]:
        if item.paper:
            citations.append(
                {
                    "paperId": item.paper.paperId,
                    "title": item.paper.title,
                }
            )
    return json.dumps({"total": len(results), "citations": citations}, indent=2)


@mcp.tool()
def get_paper_references(
    paper_id: str,
    limit: int = 20,
) -> str:
    """Get papers referenced by the given paper.

    Args:
        paper_id: Paper identifier
        limit: Max results (1-1000, default 20)
    """
    results = _sch.get_paper_references(
        paper_id, fields=["title"], limit=min(limit, 1000)
    )
    references = []
    for item in list(results)[:limit]:
        if item.paper:
            references.append(
                {
                    "paperId": item.paper.paperId,
                    "title": item.paper.title,
                }
            )
    return json.dumps({"total": len(results), "references": references}, indent=2)


@mcp.tool()
def search_snippets(
    query: str,
    year: Optional[str] = None,
    fields_of_study: Optional[str] = None,
    publication_date_or_year: Optional[str] = None,
    min_citation_count: Optional[int] = None,
    limit: int = 10,
) -> str:
    """Search within paper text for matching snippets.

    Returns passages from papers that match the query, with surrounding context.

    Args:
        query: Text search query
        year: Year or range (e.g. "2020", "2018-2022")
        fields_of_study: Comma-separated fields
        publication_date_or_year: Date range "YYYY-MM-DD:YYYY-MM-DD"
        min_citation_count: Minimum citations filter
        limit: Max results (1-1000, default 10)
    """
    fos = fields_of_study.split(",") if fields_of_study else None
    results = _sch.search_snippet(
        query,
        year=year,
        fields_of_study=fos,
        publication_date_or_year=publication_date_or_year,
        min_citation_count=min_citation_count,
        limit=min(limit, 1000),
    )
    items = []
    for r in results:
        item = {"score": r.score}
        if r.paper:
            item["paper"] = {
                "paperId": r.paper.paperId,
                "title": r.paper.title,
                "year": r.paper.year,
            }
        if r.snippet:
            item["snippet"] = {
                "text": r.snippet.text,
                "kind": r.snippet.snippetKind,
                "section": r.snippet.section,
            }
        items.append(item)
    return json.dumps({"results": items}, indent=2)


@mcp.tool()
def search_authors(
    query: str,
    limit: int = 10,
) -> str:
    """Search for authors by name.

    Args:
        query: Author name query
        limit: Max results (1-1000, default 10)
    """
    results = _sch.search_author(query, limit=min(limit, 1000))
    authors = [_author_to_dict(a) for a in list(results)[:limit]]
    return json.dumps({"total": results.total, "authors": authors}, indent=2)


@mcp.tool()
def get_author(author_id: str) -> str:
    """Get detailed information about an author.

    Args:
        author_id: Semantic Scholar author ID
    """
    author = _sch.get_author(author_id)
    return json.dumps(_author_to_dict(author), indent=2)


@mcp.tool()
def get_author_papers(
    author_id: str,
    limit: int = 20,
) -> str:
    """Get papers by a specific author.

    Args:
        author_id: Semantic Scholar author ID
        limit: Max results (1-1000, default 20)
    """
    results = _sch.get_author_papers(author_id, limit=min(limit, 1000))
    papers = [_paper_to_dict(p) for p in list(results)[:limit]]
    return json.dumps({"total": len(results), "papers": papers}, indent=2)


@mcp.tool()
def get_recommendations(
    paper_id: str,
    limit: int = 10,
) -> str:
    """Get recommended papers similar to the given paper.

    Args:
        paper_id: Paper identifier
        limit: Max results (1-500, default 10)
    """
    results = _sch.get_recommended_papers(paper_id, limit=min(limit, 500))
    papers = [_paper_to_dict(p) for p in results[:limit]]
    return json.dumps({"papers": papers}, indent=2)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
