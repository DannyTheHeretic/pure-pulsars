import datetime
import random

import requests
import wikipediaapi
from discord import Embed
from fake_useragent import UserAgent

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
t = wikipediaapi.Wikipedia(user_agent=ua.random)


def is_article_title(link: str) -> bool:
    """Check if the provided link is a standard text link."""
    return all(not link.startswith(prefix) for prefix in NON_LINK_PREFIXS)


def rand_date() -> datetime.date:
    """Take the current time returning the timetuple."""
    now = int(datetime.datetime.now(tz=datetime.UTC).timestamp() // 1)
    y = int((now - 252482400) - now % 31557600 // 1)
    return datetime.datetime.fromtimestamp(timestamp=random.randrange(y, now), tz=datetime.UTC)  # noqa: S311


def make_embed(article: wikipediaapi.WikipediaPage) -> Embed:
    """Return a Discord Embed."""
    embed = Embed(title=article.title)
    pid = article._attributes  # noqa: SLF001
    try:
        val = f"pageids={pid["pageid"]}"
    except KeyError:
        val = f"titles={pid["title"]}"
    url = f"https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&{val}&format=json"
    req = requests.get(
        url=url,
        timeout=10,
    )
    req_json = req.json()
    embed = Embed(title=article.title)
    embed.description = f"{article.summary[0:400]}...([read more](https://en.wikipedia.org/wiki/\
{article.title.replace(" ","_")}))"
    try:
        _ = req_json["query"]["pages"]
        t = next(iter(_.keys()))
        url = _[t]["thumbnail"]["source"]
        url = url.replace("/thumb/", "/")
        url = url.split("px")[0][0:-3]
        embed.set_image(url=url)
    except KeyError as e:
        print(e)
    except StopIteration as e:
        print(e)
    return embed


def rand_wiki() -> wikipediaapi.WikipediaPage:
    """Return a random popular wikipedia article, returns None if operation failed."""
    rd = rand_date()
    date = f"{rd.year}/{rd.month:02}/{rd.day:02}"
    url = f"https://api.wikimedia.org/feed/v1/wikipedia/en/featured/{date}"
    try:
        req_json = requests.get(url, headers={"UserAgent": ua.random}, timeout=100).json()
        mr = req_json["mostread"]
        random.shuffle(mr["articles"])
        select = mr["articles"][0]
        page = wikipediaapi.WikipediaPage(wiki=t, title=select["normalizedtitle"])
        if is_article_title(page.title):
            return page
        return rand_wiki()
    except KeyError:
        return rand_wiki()
