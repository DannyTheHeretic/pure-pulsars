import os

import discord
from discord import app_commands
from dotenv import load_dotenv

from cmds import setup_guild, wikiguesser, wikirandom

load_dotenv(".env")
intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready() -> None:  # noqa: D103
    print("ready for ACTION!!!")
    await tree.sync(guild=discord.Object(id=1262497899925995563))

    await client.change_presence(
        status=discord.Status.online, activity=discord.activity.CustomActivity("📚 reading wikipedia", emoji="📚")
    )


wikiguesser.main(tree)
wikirandom.main(tree)
setup_guild.main(tree)
client.run(os.environ["DISAPI"])
