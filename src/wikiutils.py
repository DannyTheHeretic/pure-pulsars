"""Utilities for interacting with Wikipedia.

This module contains some helper functions for interacitng with and fetching
data from Wikipedia. It also contains a class that can be used to generate
articles with a specific category or title
"""

import functools
import logging
import random
import secrets
from collections import defaultdict
from collections.abc import AsyncGenerator, Sequence
from datetime import UTC, date, datetime
from typing import ClassVar

import aiohttp
import pywikibot
import pywikibot.page
from discord import Colour, Embed, User
from pywikibot import Page

from database.database_core import DATA, NullUserError
from database.user import UserController, _User

UA = "WikiWabbit/1.1.0 (https://pure-pulsars.web.app/; dannytheheretic@proton.me)"
site = pywikibot.Site("en", "wikipedia", user=UA)


def rand_date() -> date:
    """Take the current time returning the timetuple.

    Pulls a random date between 8 years ago and now.
    """
    now = int(datetime.now(tz=UTC).timestamp() // 1)

    # Picking a random date between 8 years and now.
    y = int((now - 252482400) - now % 31557600 // 1)
    return datetime.fromtimestamp(timestamp=now - secrets.randbelow(now - y), tz=UTC)


async def make_embed(article: Page) -> Embed:
    """Return a Discord Embed.

    Args:
    ----
    article (Page): The article to create the embed for.

    Returns:
    -------
    Embed: The embed.

    Raises:
    ------
    AttributeError: If the image url cannot be found.

    """
    embed = Embed(title=article.title())
    embed.description = f"{article.extract(chars=400)}...([read more]({article.full_url()}))"
    url = article.page_image()
    try:
        url = url.latest_file_info.url
    except AttributeError:
        url = None
    embed.set_image(url=url)
    return embed


def make_img_embed(article: Page, error_message: str = "Sorry no image found") -> Embed:
    """Return a Discord Image type Embed.

    Args:
    ----
    article (Page): The article to create the embed for.
    error_message (str): The error message if no picture is found.

    Returns:
    -------
    Embed: The embed.

    Raises:
    ------
    AttributeError: If the image url cannot be found.

    """
    embed = Embed(colour=Colour.blue(), type="image")
    img_data = article.page_image()
    try:
        img_url = img_data.get_file_url()
    except AttributeError:
        img_url = "https://wikimedia.org/static/images/project-logos/enwiki-2x.png"
        embed.description = error_message
    embed.set_image(url=img_url)
    return embed


def get_best_result(results: tuple[Page], query: str) -> Page | None:
    """Return the best result from a list of results.

    Args:
    ----
    results (tuple[Page]): A list of results.
    query (str): The query to search for.

    Returns:
    -------
    Page: The best result. None if no results are found.

    Notes:
    -----
    Does not implement an optimal search algorithm, but works fine for the
    scope of the project.

    """
    # Check for exact match in the title
    for result in results:
        if query.casefold().strip() == result.title().casefold().strip():
            return result

    # Check for near match in the title
    for result in results:
        if query.casefold().strip() in result.title().casefold().strip():
            return result

    return None


async def search_wikipedia(query: str) -> Page | None:
    """Search wikipedia and return the first result.

    Args:
    ----
    query (str): The query to search for.

    Returns:
    -------
    Page: The first page found. None if no results are found.

    """
    result = Page(site, title=query)

    if not result.exists() or result.isRedirectPage():
        # Try performing a search.
        results = tuple(site.search(query, total=10))

        if not results:
            return None

        return get_best_result(results, query)

    try:
        return result

    except IndexError:
        logging.exception("No results found for query: %s", query)
        return None


async def search_wikipedia_generator(query: str, max_number: int = 10) -> AsyncGenerator[Page, None]:
    """Search wikipedia and return results matching the query.

    Args:
    ----
    query (str): The query to search for.
    max_number (int): The maximum number of results to return.

    Returns:
    -------
    Page: The first page found. None if no results are found.

    """
    results = tuple(site.search(query, total=max_number))

    for result in results:
        yield result


async def rand_wiki() -> Page:
    """Return a random popular wikipedia article."""
    return await ArticleGenerator().fetch_article()


async def loss_update(guild: int, user: User) -> None:
    """Update the user in the database.

    Args:
    ----
    guild (int): The guild id.
    user (User): The user to update.
    score (int): The score to update.

    """
    uid = user.id
    try:
        db_ref_user = await DATA.get_user(guild, uid)
        await DATA.update_value_for_user(
            guild_id=guild,
            user_id=uid,
            key="times_played",
            value=db_ref_user["times_played"] + 1,
        )

        await DATA.update_value_for_user(
            guild_id=guild,
            user_id=uid,
            key="failure",
            value=db_ref_user["failure"] + 1,
        )

        await DATA.update_value_for_user(
            guild_id=guild,
            user_id=uid,
            key="last_played",
            value=datetime.now(UTC).timestamp(),
        )

    except NullUserError:
        new_user = UserController(
            info=_User(
                name=user.global_name,
                times_played=1,
                failure=1,
                score=0,
                last_played=datetime.now(UTC).timestamp(),
            ),
        )
        await DATA.add_user(uid, new_user, guild)


async def win_update(guild: int, user: User, score: int) -> None:
    """Update the user in the database.

    Args:
    ----
    guild (int): The guild id.
    user (User): The user to update.
    score (int): The score to update.

    Notes:
    -----
    This interfaces directly with the database connection provided by database_core.py.
    For more information on the functions used here, see database_core.py.

    """
    uid = user.id
    try:
        db_ref_user = await DATA.get_user(guild, uid)
        await DATA.update_value_for_user(
            guild_id=guild,
            user_id=uid,
            key="times_played",
            value=db_ref_user["times_played"] + 1,
        )

        await DATA.update_value_for_user(
            guild_id=guild,
            user_id=uid,
            key="score",
            value=db_ref_user["score"] + score,
        )

        await DATA.update_value_for_user(
            guild_id=guild,
            user_id=uid,
            key="last_played",
            value=datetime.now(UTC).timestamp(),
        )

        await DATA.update_value_for_user(
            guild_id=guild,
            user_id=uid,
            key="wins",
            value=db_ref_user["wins"] + 1,
        )

    except NullUserError:
        new_user = UserController(
            info=_User(
                name=user.global_name,
                times_played=1,
                wins=1,
                score=score,
                last_played=datetime.now(UTC).timestamp(),
            ),
        )

        await DATA.add_user(uid, new_user, guild)


def get_all_categories_from_article(article: Page) -> list[str]:
    """Return all categories from an article.

    Args:
    ----
    article (Page): The article to get the categories from.

    Returns:
    -------
    list[str]: A list of categories.

    Notes:
    -----
    This is a convenience function for getting all categories from an article.
    For implementation, see ``ArticleGenerator.get_all_categories_from_article``.

    """
    return ArticleGenerator.get_all_categories_from_article(article)


async def get_articles_with_categories(categories: Sequence[str], number: int = 1) -> list[Page]:
    """Get a list of articles with the given categories.

    Args:
    ----
    categories (Sequence[str]): A list of categories to search for.
    number (int): The number of articles to return.

    Returns:
    -------
    list[Page]: A list of articles.

    """
    generator = ArticleGenerator(categories=categories)

    return [await generator.fetch_article() for _ in range(number)]


class ArticleGeneratorError(Exception):
    """Base class for ArticleGenerator exceptions."""


class ArticleGenerator:
    """Generates articles from Wikipedia.

    This class is a generator that will return articles based on the given
    constraints. It can be used to generate articles based on categories or
    titles. It can also be used to generate random articles.

    Attributes
    ----------
    categories (tuple[str]): A tuple of categories to search for.
    titles (list[str]): A list of titles to search for.
    _current_article (Page): The current article.
    _generated_articles (set[Page]): A set of generated articles.

    """

    _article_limit: ClassVar[int] = 1_000

    _current_article: Page
    _generated_articles: set[Page]
    categories: tuple[str]
    titles: list[str]

    def __init__(
        self,
        titles: Sequence[str] | None = None,
        categories: Sequence[str] | None = None,
    ) -> None:
        """Initialize the ArticleGenerator.

        Args:
        ----
        titles (Sequence[str]): A list of titles to search for.
        categories (Sequence[str]): A list of categories to search for.

        """
        self._current_article = None
        self.titles = titles or []
        self.categories = categories or ()
        self._generated_articles = set()

    # Make this class a generator that will iterate over subsequent calls to fetch_article.
    def __aiter__(self) -> "ArticleGenerator":
        """Return the generator."""
        return self

    async def __anext__(self) -> Page:
        """Return the next article."""
        try:
            return await self.fetch_article()

        except ArticleGeneratorError as err:
            raise StopAsyncIteration from err

    @property
    def current_article(self) -> Page:
        """Return the current article."""
        return self._current_article

    def clear_cache(self) -> None:
        """Clear the cache."""
        self._generated_articles.clear()

    async def fetch_article(self) -> Page:
        """Return an article. Functon that retrieves the next article from the generator."""
        return await anext(self.next_article())

    async def next_article(self) -> AsyncGenerator[Page, None]:
        """Return a new article."""
        while True:
            self._current_article = await self.fetch_valid_article()
            yield self._current_article

    async def fetch_valid_article(self) -> Page:
        """Return a valid Page based on the current constraints."""
        articles = await self._articles_from_titles() if self.titles else []

        # Filter articles that have already been generated.
        articles = [article for article in articles if article not in self._generated_articles]

        if self.categories:
            if not articles:
                articles = await self._articles_from_categories()

            try:
                article = secrets.choice([article for article in articles if self.article_has_categories(article)])

            except IndexError as err:
                message = f"No articles found in the categories: {self.categories}."
                raise ArticleGeneratorError(message) from err

        elif not articles and not self.titles:
            article = await self.random_article()

        else:
            try:
                article = articles[0]

            except IndexError as err:
                message = "No articles found for the given titles."
                raise ArticleGeneratorError(message) from err

        # Record this article as generated.
        self._generated_articles.add(article)

        return article

    async def _articles_from_categories(self) -> list[Page]:
        """Return an article from the list of categories."""
        category_pages = {category: set(pywikibot.Category(site, category).articles()) for category in self.categories}

        # If there are mutlitple categories, get the intersection of the articles.
        articles = functools.reduce(set.union, category_pages.values())

        # For each of these articles, check if they have all the categories.
        articles = [article for article in articles if self.article_has_categories(article)]

        try:
            return articles

        except IndexError as err:
            message = "No articles found in the categories."
            raise ArticleGeneratorError(message) from err

    async def _articles_from_titles(self) -> list[Page]:
        """Return an article from the list of titles."""
        # If categories are provided, do a broader search.
        if self.categories:
            title_articles: dict[str, set[Page]] = defaultdict(set)

            for title in self.titles:
                async for article in search_wikipedia_generator(title):
                    title_articles[title].add(article)

            articles = {a for articles in title_articles.values() for a in articles}

            if any(article is None for article in title_articles.values()):
                titles_not_found = [title for title, article in title_articles.items() if article is None]
                message = f"No articles found for the following titles: {titles_not_found}"

                raise ArticleGeneratorError(message)

            # Ensure the title is at least a partial match.
            articles = {
                article
                for article in articles
                if any(title.casefold() in article.title().casefold() for title in self.titles)
            }

        else:
            # Get top page for each of the titles.
            articles = [await search_wikipedia(title) for title in self.titles]

        if None in articles:
            titles_not_found = [
                title for title, article in zip(self.titles, articles, strict=False) if article is None
            ]
            message = f"No articles found for the following titles: {titles_not_found}"

            raise ArticleGeneratorError(message)

        if not articles:
            message = "No articles found for the given titles"
            raise ArticleGeneratorError(message)

        return articles

    def article_has_categories(self, article: Page) -> bool:
        """Return True if the article has all the categories."""
        article_categories = get_all_categories_from_article(article)
        article_categories = {category.casefold() for category in article_categories}

        return all(category.casefold() in article_categories for category in self.categories)

    @staticmethod
    async def random_article() -> Page:
        """Return a random article."""
        date = rand_date()
        date = f"{date.year}/{date.month:02}/{date.day:02}"
        url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/{date}"
        json = None
        async with aiohttp.ClientSession(headers={"UserAgent": UA}) as session, session.get(url) as response:
            json = await response.json()
        try:
            articles = json["items"][0]["articles"]
            random.shuffle(articles)
            title = articles[0]["article"]
            page = Page(site, title)
            if page.isRedirectPage() or not page.exists():
                return await rand_wiki()
        except KeyError as e:
            logging.info("Wikiutils:\nFunc: random_article\nException: %s", e)
            return await rand_wiki()
        return page

    @staticmethod
    def get_all_categories_from_article(article: Page) -> list[str]:
        """Return all categories from an article."""
        return [category.title().replace("Category:", "") for category in article.categories()]
