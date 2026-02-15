from semanticscholar.Paper import Paper
from semanticscholar.SemanticScholarObject import SemanticScholarObject


class Snippet(SemanticScholarObject):
    """
    This class abstracts a snippet from a paper.
    """

    FIELDS = [
        "snippet.text",
        "snippet.snippetKind",
        "snippet.section",
        "snippet.snippetOffset",
        "snippet.annotations",
    ]

    def __init__(self, data: dict) -> None:
        super().__init__()
        self._text = None
        self._snippetKind = None
        self._section = None
        self._snippetOffset = None
        self._annotations = None
        self._init_attributes(data)

    @property
    def text(self) -> str:
        """
        :type: :class:`str`
        """
        return self._text

    @property
    def snippetKind(self) -> str:
        """
        :type: :class:`str`
        """
        return self._snippetKind

    @property
    def section(self) -> str:
        """
        :type: :class:`str`
        """
        return self._section

    @property
    def snippetOffset(self) -> int:
        """
        :type: :class:`int`
        """
        return self._snippetOffset

    @property
    def annotations(self) -> list:
        """
        :type: :class:`list`
        """
        return self._annotations

    def _init_attributes(self, data: dict) -> None:
        self._data = data
        if "text" in data:
            self._text = data["text"]
        if "snippetKind" in data:
            self._snippetKind = data["snippetKind"]
        if "section" in data:
            self._section = data["section"]
        if "snippetOffset" in data:
            self._snippetOffset = data["snippetOffset"]
        if "annotations" in data:
            self._annotations = data["annotations"]


class SnippetSearchResult(SemanticScholarObject):
    """
    This class abstracts a snippet search result containing a paper and snippet.
    """

    def __init__(self, data: dict) -> None:
        super().__init__()
        self._paper = None
        self._snippet = None
        self._score = None
        self._init_attributes(data)

    @property
    def paper(self) -> Paper:
        """
        :type: :class:`semanticscholar.Paper.Paper`
        """
        return self._paper

    @property
    def snippet(self) -> Snippet:
        """
        :type: :class:`semanticscholar.SnippetSearchResult.Snippet`
        """
        return self._snippet

    @property
    def score(self) -> float:
        """
        :type: :class:`float`
        """
        return self._score

    def _init_attributes(self, data: dict) -> None:
        self._data = data
        if "paper" in data:
            if data["paper"] is not None:
                self._paper = Paper(data["paper"])
        if "snippet" in data:
            if data["snippet"] is not None:
                self._snippet = Snippet(data["snippet"])
        if "score" in data:
            self._score = data["score"]
