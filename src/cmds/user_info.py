import logging
from datetime import UTC, datetime

import discord
import humanize
from discord import app_commands

from database.database_core import DATA, NullUserError


def main(tree: app_commands.CommandTree) -> None:
    """Create user-info command."""

    @tree.command(
        name="user-info",
        description="Returns your stats",
    )
    async def user_info(interaction: discord.Interaction, user: discord.User = None) -> None:
        try:
            await interaction.response.defer(thinking=True, ephemeral=True)
            embed = discord.embeds.Embed()
            try:
                if user is None:
                    user = interaction.user
                user_data = await DATA.get_user(interaction.guild_id, user.id)
                img = user.display_avatar
                embed.set_thumbnail(url=img.url)
                embed.add_field(
                    name="Name",
                    value=user_data["name"],
                    inline=False,
                )
                embed.add_field(
                    name="Score",
                    value=user_data["score"],
                    inline=False,
                )
                try:
                    embed.add_field(
                        name="W/L",
                        value=(user_data["wins"] / user_data["failure"]),
                        inline=False,
                    )
                except ZeroDivisionError:
                    embed.add_field(
                        name="W/L",
                        value=(user_data["wins"] / 1),
                        inline=False,
                    )
                embed.add_field(
                    name="Last Played",
                    value=humanize.naturaltime(datetime.now(UTC).timestamp() - user_data["last_played"]),
                    inline=False,
                )
            except NullUserError:
                await interaction.followup.send(content=f"User: {user.mention} has **not** played any games")
                return

            await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.app_commands.errors.CommandInvokeError as e:
            logging.critical("Exception %s", e)
