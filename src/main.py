import os

import discord
from discord import app_commands

from bot_runners import rand_wiki

intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready() -> None:  # noqa: D103
    await tree.sync(guild=discord.Object(id=1262497899925995563))


@tree.command(name="wiki", description="its the command thingy", guild=discord.Object(id=1262497899925995563))
async def wiki(interaction: discord.Interaction) -> None:  # noqa: D103
    await interaction.response.send_message(content="hello, we are processing ur request")
    y = rand_wiki()
    await interaction.followup.send(content=f"```{y}```")


client.run(os.getenv("DISAPI"))
