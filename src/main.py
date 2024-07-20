import os

import discord
from discord import app_commands
from dotenv import load_dotenv

from cmds import leaderboard, wikiguesser, wikirandom
from database.database_core import Database
from database.user import User

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

@client.event
async def on_guild_join(guild: discord.Guild) -> None:
    '''Adds all the users to the Database.'''
    data = Database()
    for member in guild.members:
        if not member.bot:
            data.add_user(member.id, User.create_empty_user(member.id))


wikiguesser.main(tree)
wikirandom.main(tree)
leaderboard.main(tree)
client.run(os.environ["DISAPI"])
