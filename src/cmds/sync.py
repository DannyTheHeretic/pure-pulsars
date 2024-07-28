"""Sync the command tree for the bot."""

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
        """Command to sync the tree.

        It will sync the command tree to the guild it is called in.
        """
        try:
            guild = inter.guild
            try:
                await bot.sync(guild=guild)
            except discord.HTTPException as e:
                logging.info("Tried to sync: %s", e)
            msg = f"Synced the tree to {guild.name}"
            logging.info(msg)
            await inter.response.send_message(content=msg, ephemeral=True)
        except NotFound as e:
            logging.info("Failed to sync: %s", e)
        except CommandInvokeError as e:
            logging.info("Failed to sync: %s", e)
