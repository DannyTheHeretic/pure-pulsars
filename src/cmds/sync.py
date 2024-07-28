import logging

import discord
from discord import app_commands
from discord.app_commands.errors import CommandInvokeError
from discord.errors import NotFound


def main(bot: app_commands.CommandTree) -> None:
    """Command to sync the tree."""

    @bot.command(
        name="sync",
        description="Syncs the command tree",
    )
    async def sync(inter: discord.Interaction) -> None:
        """Command to sync the tree."""
        try:
            guild = inter.guild
            try:
                await bot.sync(guild=guild)
            except discord.HTTPException as e:
                logging.critical(e)
            msg = f"Synced the tree to {guild.name}"
            logging.info(msg)
            await inter.response.send_message(content=msg, ephemeral=True)
        except NotFound as e:
            logging.critical(e)
        except CommandInvokeError as e:
            logging.critical(e)
