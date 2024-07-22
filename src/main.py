import os

import discord
from discord import app_commands
from dotenv import load_dotenv

from cmds import help_bot, leaderboard, never, reset_scores, user_info, wikiguesser, wikirandom, wikisearch

load_dotenv(".env")
intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready() -> None:  # noqa: D103
    print("ready for ACTION!!!")
    await tree.sync(guild=discord.object.Object(1262497899925995563))
    await client.change_presence(
        status=discord.Status.online, activity=discord.activity.CustomActivity("📚 reading wikipedia", emoji="📚")
    )


wikiguesser.main(tree)
wikirandom.main(tree)
leaderboard.main(tree)
user_info.main(tree)
wikisearch.main(tree)
reset_scores.main(tree)
never.main(tree)
help_bot.main(tree)

client.run(
    os.environ["DISAPI"],
    log_level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    root_logger=True,
)
