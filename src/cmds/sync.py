import logging
from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

gid = commands.parameter(default=0, description="The Guild ID that you want to sync, optional")
spec = commands.parameter(
    default="", description="None - Global, ~ - Current Guild, ^ - Delete CMDs For Current Guild"
)


def main(bot: app_commands.CommandTree) -> None:
    """."""

    @bot.command(
        name="sync",
        description="???",
    )
    @commands.guild_only()
    @commands.is_owner()
    async def sync(inter: discord.Interaction, guild: int | None, spec: Literal["~", "^"] | None = None) -> None:
        """."""
        await inter.response.defer(thinking=True, ephemeral=False)
        if not guild:
            if spec == "~":
                synced = await bot.sync(guild=inter.guild)
            elif spec == "^":
                bot.clear_commands(guild=inter.guild)
                await bot.sync(guild=inter.guild)
                synced = []
            else:
                synced = await bot.sync()

            val = "globally" if spec is None else "to the current guild."
            msg = "Synced %d commands %s", len(synced), val
            logging.info(msg=msg)
            await inter.response.send_message(content=msg)
            return

        ret = 0
        try:
            g = discord.Object(id=guild)
            await bot.sync(guild=g)
        except discord.HTTPException:
            pass
        else:
            ret += 1
            logging.info("Synced the tree to %d/%d", ret, g.id)
