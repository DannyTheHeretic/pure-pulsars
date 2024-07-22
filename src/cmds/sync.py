import logging
from typing import Literal

import discord
from discord.ext import commands


def main(bot: discord.app_commands.CommandTree) -> None:
    """."""

    @bot.command()
    @commands.guild_only()
    @commands.is_owner()
    async def sync(
        ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: Literal["~", "*", "^"] | None = None
    ) -> None:
        """."""
        if not guilds:
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
            for guild in guilds:
                try:
                    await ctx.bot.tree.sync(guild=guild)
                except discord.HTTPException:
                    pass
                else:
                    ret += 1

                logging.info("Synced the tree to %d/%d", ret, len(guilds))
