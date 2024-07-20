import datetime
import os
import random

import discord
import requests
import wikipediaapi
from discord import app_commands

intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

t = wikipediaapi.Wikipedia(user_agent="CoolBot/0.0 (https://example.org/coolbot/) generic-library/0.0")

def rand_date() -> datetime.date:
    """Takes the current time returning the timetuple."""  # noqa: D401
    now = int(datetime.datetime.now(tz=datetime.UTC).timestamp()//1)
    y = int((now - 252482400) - now % 31557600//1)
    return datetime.datetime.fromtimestamp(timestamp=random.randrange(y, now), tz=datetime.UTC)  # noqa: S311

def rand_wiki()->str:
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
        ans+="\n"+w.title+"\n\n"

        links = [link for link in w.links if ":" not in link]

        backlinks = [link for link in w.backlinks if ":" not in link]

        return ans+f"Links: {len(links)}\nBackLinks: {len(backlinks)}\n"
    except KeyError as e:
        print(req_json)
        print(e)
        return "it broke"


@client.event
async def on_ready() -> None:  # noqa: D103
    await tree.sync(guild=discord.Object(id=1262497899925995563))


@tree.command(name="wiki",description="its the command thingy",guild=discord.Object(id=1262497899925995563))
async def wiki(interaction: discord.Interaction) -> None:  # noqa: D103
    await interaction.response.send_message(content="hello, we are processing ur request")
    y = rand_wiki()
    await interaction.followup.send(content=f"\`\`\`{y}\`\`\`")

x = os.getenv("DISAPI")
client.run(x)