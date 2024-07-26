"""Test the ArticleGenerator class."""
# ruff: noqa: SLF001, S101, D103

import pytest
from pywikibot import Page
from src.wikiutils import ArticleGenerator, ArticleGeneratorError


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


@pytest.mark.asyncio()
async def test_multiple_categories() -> None:
    article_gen = ArticleGenerator(categories=("Astronomy", "Physics"))

    assert article_gen.categories == ("Astronomy", "Physics")

    result = await article_gen.fetch_article()

    assert result is not None
    assert all(
        f"Category:{category}" in get_all_categories_from_article(result) for category in article_gen.categories
    )


@pytest.mark.asyncio()
async def test_multiple_titles() -> None:
    article_gen = ArticleGenerator(titles=["Python (programming language)", "Java (programming language)"])

    assert article_gen.titles == ["Python (programming language)", "Java (programming language)"]

    result = await article_gen.fetch_article()

    assert result is not None
    assert result.title() in article_gen.titles

    result1 = result

    result = await article_gen.fetch_article()

    assert result is not None
    assert result.title() in article_gen.titles
    assert result.title() != result1.title()


@pytest.mark.asyncio()
async def test_clear_cache() -> None:
    article_gen = ArticleGenerator(titles=["Python (programming language)", "Java (programming language)"])

    result = await article_gen.fetch_article()

    assert result is not None
    assert result.title() in article_gen.titles
    assert article_gen._generated_articles == {result}

    article_gen.clear_cache()

    assert article_gen._generated_articles == set()


@pytest.mark.asyncio()
async def test_invalid_cateory() -> None:
    article_gen = ArticleGenerator(categories=("Invalid category",))

    with pytest.raises(ArticleGeneratorError):
        _ = await article_gen.fetch_article()


@pytest.mark.asyncio()
async def test_invalid_title() -> None:
    article_gen = ArticleGenerator(titles=["Invalid title!!!.!"])

    with pytest.raises(ArticleGeneratorError):
        _ = await article_gen.fetch_article()


@pytest.mark.asyncio()
async def test_invalid_title_and_category() -> None:
    article_gen = ArticleGenerator(titles=["Invalid title!!!.!"], categories=("Invalid category",))

    with pytest.raises(ArticleGeneratorError):
        _ = await article_gen.fetch_article()


@pytest.mark.asyncio()
async def test_invalid_title_and_valid_category() -> None:
    article_gen = ArticleGenerator(titles=["Invalid title!!!.!"], categories=("Astronomy",))

    with pytest.raises(ArticleGeneratorError):
        _ = await article_gen.fetch_article()


@pytest.mark.asyncio()
async def test_valid_title_and_invalid_category() -> None:
    article_gen = ArticleGenerator(titles=["Python (programming language)"], categories=("Invalid category",))

    with pytest.raises(ArticleGeneratorError):
        _ = await article_gen.fetch_article()


@pytest.mark.asyncio()
async def test_title_and_category() -> None:
    # Note: the category capitalization vs. the actual category name is different.
    #       This is intentional to test the case insensitivity of the category name.
    article_gen = ArticleGenerator(titles=["Python"], categories=("Programming Languages",))

    result = await article_gen.fetch_article()

    assert result is not None
    assert result.title() == "Python (programming language)"
    assert "Category:Programming languages" in get_all_categories_from_article(result)


@pytest.mark.asyncio()
async def test_articlegenerator_as_iterator() -> None:
    article_gen = ArticleGenerator(titles=["Python (programming language)", "Java (programming language)"])

    recieved = []
    async for article in article_gen:
        assert article is not None
        assert article.title() in article_gen.titles

        recieved.append(article)

    assert len(recieved) == len(article_gen.titles)
    assert all(article in article_gen._generated_articles for article in recieved)
