"""User info command for the Wiki Guesser game."""

import logging
from datetime import UTC, datetime

import discord
import humanize
from discord import app_commands
from discord.app_commands.errors import CommandInvokeError
from discord.errors import NotFound

from database.database_core import DATA, NullUserError

SKIP = ["userid", "last_played"]


def main(tree: app_commands.CommandTree) -> None:
    """Create user-info command."""

    @tree.command(
        name="user-info",
        description="Returns your stats",
    )
    @app_commands.describe(user="Who are you asking about, leave blank for self?")
    async def user_info(interaction: discord.Interaction, user: discord.User = None) -> None:
        """Get game info for a specific user from the scores database.

        Args:
        ----
        interaction (discord.Interaction): The interaction object.
        user (discord.User): The user to get the game info for.

        Notes:
        -----
        If no user is provided, the command will default to the user who invoked the command.

        """
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
        except NotFound as e:
            logging.info("Tried to get User-Info: %s", e)
        except CommandInvokeError as e:
            logging.info("Tried to get User-Info: %s", e)
