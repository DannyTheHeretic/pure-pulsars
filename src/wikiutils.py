import random
from datetime import UTC, date, datetime

import aiohttp
import pywikibot
import pywikibot.page
from discord import Embed, User
from fake_useragent import UserAgent
from pywikibot import Page

from database.database_core import DATA, NullUserError

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
    return datetime.fromtimestamp(timestamp=random.randrange(y, now), tz=UTC)  # noqa: S311


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
    articles = json["items"][0]["articles"]
    random.shuffle(articles)
    title = articles[0]["article"]
    page = Page(site, title)
    if page.isRedirectPage() or not page.exists():
        return rand_wiki()
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
        new_user = User(
            name=user.global_name,
            times_played=1,
            wins=1,
            score=score,
            last_played=datetime.now(UTC).timestamp(),
            failure=0,
        )
        await DATA.add_user(uid, new_user, guild)
