import logging
from typing import Literal

import discord
from discord.ext import commands


def main(bot: commands.Bot) -> None:
    """."""

    @bot.command(
        name="sync",
        description="???",
    )
    @commands.guild_only()
    @commands.is_owner()
    async def sync(inter: discord.Interaction, guild: int | None, spec: Literal["~", "*", "^"] | None = None) -> None:
        """."""
        ctx = inter.context
        if not guild:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await ctx.bot.tree.sync()

            val = "globally" if spec is None else "to the current guild."
            logging.info("Synced %d commands %s", len(synced), val)

            ret = 0
            try:
                g = discord.Object(id=guild)
                await ctx.bot.tree.sync(guild=g)
            except discord.HTTPException:
                pass
            else:
                ret += 1
                logging.info("Synced the tree to %d/%d", ret, g.id)
