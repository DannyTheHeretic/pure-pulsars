import logging

import discord
from discord import app_commands
from discord.ext import commands


def main(bot: app_commands.CommandTree) -> None:
    """."""

    @bot.command(
        name="sync",
        description="Syncs the command tree",
    )
    @commands.guild_only()
    @commands.is_owner()
    async def sync(inter: discord.Interaction) -> None:
        """."""
        guild = inter.guild
        try:
            await bot.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            msg = f"Synced the tree to {guild.name}"
            logging.info(msg=msg)
            await inter.followup.send(content=msg)
