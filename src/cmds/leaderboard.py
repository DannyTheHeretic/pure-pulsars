"""Leaderboard command and logic for the Wiki Guesser game."""

import logging

import discord
from discord import Enum, app_commands
from discord.app_commands.errors import CommandInvokeError

from database.database_core import DATA


class _GloSer(Enum):
    Yes = 0
    No = 1


def main(tree: app_commands.CommandTree) -> None:
    """Create leaderboard command."""

    def _sort_leaders(e: dict) -> int:
        return e["score"]

    @tree.command(
        name="leaderboard",
        description="Returns your guilds leaderboard",
    )
    @app_commands.describe(globe="Do you want the global leaderboard?")
    async def leaderboard(interaction: discord.Interaction, globe: _GloSer = _GloSer.No) -> None:
        """Display the leaderboard for the server or the entire world.

        Args:
        ----
        interaction (discord.Interaction): The interaction object.
        globe (_GloSer): Whether to show the global leaderboard or not.

        Notes:
        -----
        Another command, ``/reset-scores``, can be used to  reset the scores of
        all users in a server.
        :w

        """
        try:
            ser_id = interaction.guild_id if bool(globe.value) else 0
            await interaction.response.defer(thinking=True)
            board = await DATA.get_server(ser_id)
            lead = list(board.values())
            lead.sort(key=_sort_leaders, reverse=True)
            lead = lead[0:10]
            embed = discord.Embed(
                title=f"Wikiguesser leaderboard for {interaction.guild.name if ser_id != 0 else "THE ENTIRE WORLD"}",
            )
            names = [f"{idx+1}. {uid["name"]} /// {uid["score"]}" for idx, uid in enumerate(lead)]
            embed.add_field(
                name="Users /// Score",
                value=f"{"\n".join(names)}\n",
            )

            await interaction.followup.send(embed=embed)
        except CommandInvokeError as e:
            logging.info("Leaderboard:\nException: %s", e)
