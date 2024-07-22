import logging
from typing import Literal

import discord
from discord.ext import commands

gid = commands.parameter(default=0, description="The Guild ID that you want to sync, optional")
spec = commands.parameter(
    default="", description="None - Global, ~ - Current Guild, ^ - Delete CMDs For Current Guild"
)


def main(bot: commands.Bot) -> None:
    """."""
    bot.command(
        name="sync",
        description="???",
    )

    @commands.guild_only()
    @commands.is_owner()
    async def sync(inter: discord.Interaction, guild: int | None, spec: Literal["~", "^"] | None = None) -> None:
        """."""
        await inter.response.defer(thinking=True, ephemeral=False)
        ctx = inter
        if not guild:
            if spec == "~":
                synced = await bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                bot.tree.clear_commands(guild=ctx.guild)
                await bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await bot.tree.sync()

            val = "globally" if spec is None else "to the current guild."
            logging.info("Synced %d commands %s", len(synced), val)

            ret = 0
            try:
                g = discord.Object(id=guild)
                await bot.tree.sync(guild=g)
            except discord.HTTPException:
                pass
            else:
                ret += 1
                logging.info("Synced the tree to %d/%d", ret, g.id)
