import datetime
import random

import requests
import wikipediaapi

t = wikipediaapi.Wikipedia(user_agent="CoolBot/0.0 (https://example.org/coolbot/) generic-library/0.0")


def rand_date() -> datetime.date:
    """Takes the current time returning the timetuple."""  # noqa: D401
    now = int(datetime.datetime.now(tz=datetime.UTC).timestamp() // 1)
    y = int((now - 252482400) - now % 31557600 // 1)
    return datetime.datetime.fromtimestamp(timestamp=random.randrange(y, now), tz=datetime.UTC)  # noqa: S311


def rand_wiki() -> str:
    """Dw abt it."""
    try:
        rd = rand_date()
        date = f"{rd.year}/{rd.month:02}/{rd.day:02}"
        url = f"https://api.wikimedia.org/feed/v1/wikipedia/en/featured/{date}"
        ans = date
        backlinks = []
        req_json = requests.get(url, timeout=10).json()
        mr = req_json["mostread"]
        random.shuffle(mr["articles"])
        select = mr["articles"][0]
        w = wikipediaapi.WikipediaPage(wiki=t, title=select["normalizedtitle"])
        ans += "\n" + w.title + "\n\n"

        links = [link for link in w.links if ":" not in link]

        backlinks = [link for link in w.backlinks if ":" not in link]

        return ans + f"Links: {len(links)}\nBackLinks: {len(backlinks)}\n"
    except KeyError as e:
        print(req_json)
        print(e)
        return "it broke"
