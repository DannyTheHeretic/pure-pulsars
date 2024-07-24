"""Utilities for interacting with Wikipedia.

Todo:
----
- [ ] Add a function to get all valid categories.
- [ ] Create a generator/interface for fetching articles iven some contraints
    - [x] Works as `rand_wiki` without any constraints
    - [ ] Works as `rand_wiki` with a list of allowed titles
    - [ ] Works as `rand_wiki` with a list of allowed categories

"""

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
from database.user import UserController, _User

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


async def search_wikipedia(query: str) -> Page:
    """Search wikipedia and return the first result."""
    return next(site.search(query, total=1))


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
        await DATA.update_value_for_user(guild_id=guild, user_id=uid, key="wins", value=db_ref_user["wins"] + 1)
    except NullUserError:
        new_user = UserController(info=_User(
            name=user.global_name,
            times_played=1,
            wins=1,
            score=score,
            last_played=datetime.now(UTC).timestamp(),
        ))
        await DATA.add_user(uid, new_user, guild)


@functools.cache
async def get_all_valid_categories() -> Sequence[str]:
    """Return all valid categories."""
    category_namespace = pywikibot.site.namespace.CATEGORY
    return site.allpages(namespace=category_namespace)


class ArticleGeneratorError(Exception):
    """Base class for ArticleGenerator exceptions."""


class ArticleGenerator:
    """Generates articles from Wikipedia."""

    _article_limit: ClassVar[int] = 1_000

    _current_article: Page
    _titles: list[str]

    def __init__(
        self,
        titles: str | Sequence[str] | None = None,
        categories: Sequence[str] | None = None,
    ) -> None:
        self._current_article = None
        self.titles = titles or []
        self.categories = categories or []

    @property
    def titles(self) -> list[str]:
        """The titles of allowed articles. If empty, any article title is allowed."""
        return self._titles

    @titles.setter
    async def titles(self, _value: str | Sequence[str]) -> None:
        value = [_value] if isinstance(_value, str) else list(_value)
        self._titles = value

        # Validate that these are Wikipedia article titles.
        for title in value:
            if not is_article_title(title):
                message = f"Invalid title: {title}"
                raise ArticleGeneratorError(message)

    @property
    def categories(self) -> Sequence[str]:
        """Return the categories. If empty, any article category is allowed."""
        return self._categories

    @categories.setter
    async def categories(self, _value: Sequence[str]) -> None:
        """Set the categories."""
        value = tuple(_value)
        self._categories = value

        # Validate that these are Wikipedia article categories.
        valid_categories = await self.get_valid_categories()

        invalid_target_categories = [category for category in value if category not in valid_categories]

        if invalid_target_categories:
            message = f"Invalid categories: {', '.join(invalid_target_categories)}"
            raise ArticleGeneratorError(message)

    @property
    def current_article(self) -> Page:
        """Return the current article."""
        return self._current_article

    async def fetch_article(self) -> Page:
        """Return an article. Functon that retrieves the next article from the generator."""
        return await self.next_article()

    async def next_article(self) -> Page:
        """Return a new article."""
        while True:
            self._current_article = await self.fetch_valid_article()
            yield self._current_article

    async def fetch_valid_article(self) -> Page:
        """Return a valid Page based on the current constraints."""
        # If no constraints are set, return a random article.
        if not self.titles and not self.categories:
            return await self.random_article()

        # If titles are set, return a random article from the list of titles.
        if self.titles:
            title = random.choice(self.titles)  # noqa: S311
            return await search_wikipedia(title)

        # If categories are set, return a random article from the list of categories.
        if self.categories:
            category = random.choice(self.categories)  # noqa: S311
            return await search_wikipedia(category)

        # TODO(teald): Deal with this better.
        message = f"Invalid state for ArticleGenerator: {self}"
        raise ArticleGeneratorError(message)

    async def random_article(self) -> Page:
        """Return a random article."""
        # TODO(teald): Bring rand_wiki into this class.
        return await rand_wiki()

    async def get_valid_categories(self) -> Sequence[str]:
        """Return the valid categories."""
        _ = await get_all_valid_categories()

        raise NotImplementedError
