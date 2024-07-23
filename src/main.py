import logging
import os

import discord
from discord import app_commands
from discord.ext.commands import HelpCommand
from dotenv import load_dotenv

from cmds import challenge, leaderboard, never, reset_scores, user_info, wikiguesser, wikirandom, wikisearch

load_dotenv(".env")
intents = discord.Intents.all()
client = discord.Client(intents=intents)
client.tree = app_commands.CommandTree(client)


@client.event
async def on_ready() -> None:  # noqa: D103
    print("ready for ACTION!!!")
    await client.change_presence(
        status=discord.Status.online, activity=discord.activity.CustomActivity("📚 reading wikipedia", emoji="📚")
    )


wikiguesser.main(client.tree)
wikirandom.main(client.tree)
leaderboard.main(client.tree)
user_info.main(client.tree)
wikisearch.main(client.tree)
reset_scores.main(client.tree)
never.main(client.tree)
challenge.main(client.tree)

client.help_command = HelpCommand()
client.run(os.environ["DISAPI"])
