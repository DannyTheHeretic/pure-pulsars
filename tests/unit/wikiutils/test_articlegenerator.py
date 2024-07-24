"""Test the ArticleGenerator class."""
# ruff: noqa: S101, D103

from src.wikiutils import ArticleGenerator


def test_plain_articlegenerator() -> None:
    """Test the ArticleGenerator class."""
    article_gen = ArticleGenerator()

    result = article_gen.fetch_article()

    assert result is not None


def test_specific_page() -> None:
    article_gen = ArticleGenerator(titles="Python (programming language)")

    result = article_gen.fetch_article()

    assert result is not None
    assert result.title() == "Python (programming language)"
