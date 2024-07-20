import os

import discord
from discord import app_commands
from dotenv import load_dotenv

from cmds import leaderboard, user_info, wikiguesser, wikirandom
from database.database_core import Database
load_dotenv(".env")
intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready() -> None:  # noqa: D103
    print("ready for ACTION!!!")
    await tree.sync(guild=discord.object.Object("1262497899925995563"))

    await client.change_presence(
        status=discord.Status.online, activity=discord.activity.CustomActivity("📚 reading wikipedia", emoji="📚")
    )


wikiguesser.main(tree)
wikirandom.main(tree)
leaderboard.main(tree)
user_info.main(tree, data=Database())
client.run(os.environ["DISAPI"])
