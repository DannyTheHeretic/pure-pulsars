import datetime
import random

import requests
import wikipediaapi
from fake_useragent import UserAgent

NON_LINK_PREFIXS = ["Category:",
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
                    "File:"]

def is_text_link(link:str)-> bool:
    """Check if the provided link is a standard text link."""
    return all(not link.startswith(prefix) for prefix in NON_LINK_PREFIXS)

ua = UserAgent()
t = wikipediaapi.Wikipedia(user_agent=ua.random)

def rand_date() -> datetime.date:
    """Takes the current time returning the timetuple."""  # noqa: D401
    now = int(datetime.datetime.now(tz=datetime.UTC).timestamp() // 1)
    y = int((now - 252482400) - now % 31557600 // 1)
    return datetime.datetime.fromtimestamp(timestamp=random.randrange(y, now), tz=datetime.UTC)  # noqa: S311


def rand_wiki() -> wikipediaapi.WikipediaPage:
    """Return a random popular wikipedia article,
    returns None if failed."""
    try:
        rd = rand_date()
        date = f"{rd.year}/{rd.month:02}/{rd.day:02}"
        url = f"https://api.wikimedia.org/feed/v1/wikipedia/en/featured/{date}"
        req_json = requests.get(url, timeout=20).json()
        mr = req_json["mostread"]
        random.shuffle(mr["articles"])
        select = mr["articles"][0]

        return wikipediaapi.WikipediaPage(wiki=t, title=select["normalizedtitle"])
    except KeyError:
        return None
