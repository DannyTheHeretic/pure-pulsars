import logging

import discord
from discord import app_commands
from discord.ext import commands


def main(bot: app_commands.CommandTree) -> None:
    """Command to sync the tree."""

    @bot.command(
        name="sync",
        description="Syncs the command tree",
    )
    @commands.guild_only()
    @commands.is_owner()
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
        except discord.app_commands.errors.CommandInvokeError as e:
            logging.critical(e)
