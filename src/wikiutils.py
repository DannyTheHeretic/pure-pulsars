"""Utilities for interacting with Wikipedia.

Todo:
----
- [ ] Add a function to get all valid categories.
- [ ] Create a generator/interface for fetching articles iven some contraints
    - [x] Works as `rand_wiki` without any constraints
    - [ ] Works as `rand_wiki` with a list of allowed titles
    - [ ] Works as `rand_wiki` with a list of allowed categories

"""
# ruff: noqa: S311

import functools
import logging
import random
import secrets
from collections.abc import Sequence
from datetime import UTC, date, datetime
from typing import ClassVar

import aiohttp
import pywikibot
import pywikibot.page
from discord import Embed, User
from fake_useragent import UserAgent
from pywikibot import Page

from .database.database_core import DATA, NullUserError
from .database.user import UserController, _User

NON_LINK_PREFIXS = [
    "Category:",
    "Help:",
    "Template talk:",
    "Template:",
    "Wikipedia:",
    "Talk:",
    "User:",
    "User talk:",
    "Wikipedia talk:",
    "List of ",
    "Draft:",
    "Portal:",
    "File:",
]

ua = UserAgent()
site = pywikibot.Site("en", "wikipedia")


def is_article_title(link: str) -> bool:
    """Check if the provided link is a standard text link."""
    return all(not link.startswith(prefix) for prefix in NON_LINK_PREFIXS)


def rand_date() -> date:
    """Take the current time returning the timetuple."""
    now = int(datetime.now(tz=UTC).timestamp() // 1)
    y = int((now - 252482400) - now % 31557600 // 1)
    return datetime.fromtimestamp(timestamp=now - secrets.randbelow(now - y), tz=UTC)


def make_embed(article: Page) -> Embed:
    """Return a Discord Embed."""
    embed = Embed(title=article.title())
    embed.description = f"{article.extract(chars=400)}...([read more]({article.full_url()}))"
    url = article.page_image()
    try:
        url = url.latest_file_info.url
    except AttributeError:
        try:
            url = url.oldest_file_info.url
        except AttributeError:
            url = "https://wikimedia.org/static/images/project-logos/enwiki-2x.png"
    embed.set_image(url=url)
    return embed


def get_best_result(results: tuple[Page], query: str) -> Page:
    """Return the best result from a list of results."""
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

        return get_best_result(results)

    try:
        return result

    except IndexError:
        logging.exception("No results found for query: %s", query)
        return None


async def rand_wiki() -> Page:
    """Return a random popular wikipedia article."""
    date = rand_date()
    date = f"{date.year}/{date.month:02}/{date.day:02}"
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/{date}"
    json = None
    async with aiohttp.ClientSession() as session, session.get(url) as response:
        json = await response.json()
    try:
        articles = json["items"][0]["articles"]
        random.shuffle(articles)
        title = articles[0]["article"]
        page = Page(site, title)
        if page.isRedirectPage() or not page.exists():
            return await rand_wiki()
    except KeyError as e:
        logging.critical("Oops, %s", e)
        return await rand_wiki()
    return page


async def update_user(guild: int, user: User, score: int) -> None:
    """Update the user in the database."""
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
            )
        )
        await DATA.add_user(uid, new_user, guild)


@functools.cache
async def get_all_valid_categories() -> Sequence[str]:
    """Return all valid categories."""
    raise NotImplementedError


def get_all_categories_from_article(article: Page) -> list[str]:
    """Return all categories from an article."""
    return [category.title() for category in article.categories()]


class ArticleGeneratorError(Exception):
    """Base class for ArticleGenerator exceptions."""


class ArticleGenerator:
    """Generates articles from Wikipedia."""

    _article_limit: ClassVar[int] = 1_000

    categories: tuple[str]
    _current_article: Page
    titles: list[str]

    def __init__(
        self,
        titles: Sequence[str] | None = None,
        categories: Sequence[str] | None = None,
    ) -> None:
        self._current_article = None
        self.titles = titles or []
        self.categories = categories or ()

    @property
    def current_article(self) -> Page:
        """Return the current article."""
        return self._current_article

    async def fetch_article(self) -> Page:
        """Return an article. Functon that retrieves the next article from the generator."""
        return await anext(self.next_article())

    async def next_article(self) -> Page:
        """Return a new article."""
        while True:
            self._current_article = await self.fetch_valid_article()
            yield self._current_article

    async def fetch_valid_article(self) -> Page:
        """Return a valid Page based on the current constraints."""
        articles = await self._article_from_titles() if self.titles else []

        # TODO(teald): Refactor below.
        if self.categories:
            if not articles:
                article = await self._article_from_categories()

            else:
                article = random.choice(
                    [
                        article
                        for article in articles
                        if any(category in get_all_categories_from_article(article) for category in self.categories)
                    ]
                )

        elif not articles:
            article = await self.random_article()

        else:
            article = articles[0]

        return article

    async def _article_from_categories(self) -> list[Page]:
        """Return an article from the list of categories."""
        return await search_wikipedia(random.choice(self.categories))

    async def _article_from_titles(self) -> list[Page]:
        """Return an article from the list of titles."""
        # Get top page for each of the titles.
        return [await search_wikipedia(title) for title in self.titles]

    async def random_article(self) -> Page:
        """Return a random article."""
        # TODO(teald): Bring rand_wiki into this class.
        return await rand_wiki()

    async def get_valid_categories(self) -> Sequence[str]:
        """Return the valid categories."""
        _ = await get_all_valid_categories()

        raise NotImplementedError
