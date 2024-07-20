import datetime
import random

import aiohttp
import pywikibot
from discord import Embed
from fake_useragent import UserAgent
from pywikibot import Page, pagegenerators
import pywikibot.page

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


def rand_date() -> datetime.date:
    """Take the current time returning the timetuple."""
    now = int(datetime.datetime.now(tz=datetime.UTC).timestamp() // 1)
    y = int((now - 252482400) - now % 31557600 // 1)
    return datetime.datetime.fromtimestamp(timestamp=random.randrange(y, now), tz=datetime.UTC)  # noqa: S311


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


async def rand_wiki() -> Page:
    """Return a random popular wikipedia article."""

    date = rand_date()
    date = f"{date.year}/{date.month:02}/{date.day:02}"
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/{date}"
    json = None
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            json = await response.json()
    articles = json['items'][0]['articles']
    random.shuffle(articles)
    title = articles[0]['article']
    if(not is_article_title(title)):
        return rand_wiki()
    
    return pywikibot.page.BasePage(site,title=title)
