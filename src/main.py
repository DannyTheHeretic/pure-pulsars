import os

import discord
from discord import app_commands

from cmds import wikiguesser, wikirandom

intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready() -> None:  # noqa: D103
    await tree.sync(guild=discord.Object(id=1262497899925995563))


wikiguesser.main(tree)
wikirandom.main(tree)

client.run(os.getenv("DISAPI"))
