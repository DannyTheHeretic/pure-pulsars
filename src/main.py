import logging
import os

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from cmds import challenge, help_bot, leaderboard, never, reset_scores, sync, user_info, wikiguesser, wikirandom, wikisearch

load_dotenv(".env")
intents = discord.Intents.all()
client = discord.Client(intents=intents)
client.tree = app_commands.CommandTree(client)

has_ran = False


async def _first_run(client: commands.Bot) -> None:
    has_ran = True
    await client.tree.sync()
    logging.info("The sync has been ran: %s", has_ran)


@client.event
async def on_ready() -> None:
    """Ready command."""
    logging.info("ready for ACTION!!!")
    if not has_ran:
        await _first run (client=client)
    await client.change_presence(
        status=discord.Status.online, activity=discord.activity.CustomActivity("📚 reading wikipedia", emoji="📚")
    )


@client.event
async def on_guild_join(guild: discord.Object) -> None:
    """."""
    await client.tree.sync(guild=guild)
    logging.info("Joined and synced with \nname: %s\nid: %s", guild.name, guild.id)


sync.main(client.tree)
wikiguesser.main(client.tree)
wikirandom.main(client.tree)
leaderboard.main(client.tree)
user_info.main(client.tree)
wikisearch.main(client.tree)
reset_scores.main(client.tree)
never.main(client.tree)
challenge.main(client.tree)
help_bot.main(client.tree)

if bool(os.environ.get("Server",0)):
    from cmds import shutdown
    shutdown.main(client.tree)
client.run(
    os.environ["DISAPI"],
    log_level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    root_logger=True,
)
