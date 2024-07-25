"""Test the ArticleGenerator class."""
# ruff: noqa: S101, D103

import pytest
from pywikibot import Page
from src.wikiutils import ArticleGenerator


def get_all_categories_from_article(article: Page) -> list[str]:
    """Return all categories from an article."""
    return [category.title() for category in article.categories()]


@pytest.mark.asyncio()
async def test_plain_articlegenerator() -> None:
    """Test the ArticleGenerator class."""
    article_gen = ArticleGenerator()

    result = article_gen.fetch_article()

    assert result is not None


@pytest.mark.asyncio()
async def test_specific_page() -> None:
    article_gen = ArticleGenerator(titles=["Python (programming language)"])

    result = await article_gen.fetch_article()

    assert result is not None
    assert result.title() == "Python (programming language)"


@pytest.mark.asyncio()
async def test_category_fetch() -> None:
    article_gen = ArticleGenerator(categories=("Astronomy",))

    assert article_gen.categories == ("Astronomy",)

    result = await article_gen.fetch_article()

    assert result is not None
    assert "Category:Astronomy" in get_all_categories_from_article(result)
