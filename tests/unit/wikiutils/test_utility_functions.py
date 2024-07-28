"""Testing the rand_wiki function."""
# ruff: noqa: SLF001, S101, D103

import pytest
import pywikibot
from src.wikiutils import get_all_categories_from_article, rand_wiki, site

N_RAND_WIKI_TESTS = 10


@pytest.fixture()
def sample_astronomy_articles() -> list[pywikibot.Page]:
    """Return a list of astronomy articles."""
    page_titles = [
        "Astronomy",
        "Baade-Wesselink method",
        "Tidal downsizing",
    ]

    return [pywikibot.Page(site, title) for title in page_titles]


@pytest.mark.asyncio()
async def test_rand_wiki() -> None:
    """Test the rand_wiki function."""
    for _ in range(N_RAND_WIKI_TESTS):
        result = await rand_wiki()

        assert result is not None
        assert result.title() is not None
        assert result.text is not None
        assert result.categories() is not None


@pytest.mark.asyncio()
async def test_get_all_categories_from_article(sample_astronomy_articles: list[pywikibot.Page]) -> None:
    for article in sample_astronomy_articles:
        categories = get_all_categories_from_article(article)

        assert "Astronomy" in categories

        # All example articles should alsohave any single other category.
        assert len(categories) > 1
