import discord
from discord import Enum, app_commands

from database.database_core import DATA


class _GloSer(Enum):
    GLOBAL = 0
    SERVER = 1


def main(tree: app_commands.CommandTree) -> None:
    """Create Wiki Guesser command."""

    def _sort_leaders(e: dict) -> int:
        return e["score"]

    @tree.command(
        name="leaderboard",
        description="Returns your guilds leaderboard",
    )
    async def leaderboard(interaction: discord.Interaction, glob: _GloSer = _GloSer.SERVER) -> None:
        try:
            ser_id = interaction.guild_id if bool(glob.value) else 0
            await interaction.response.defer(thinking=True)
            board = await DATA.get_server(ser_id)
            lead = list(board.values())
            lead.sort(key=_sort_leaders, reverse=True)
            lead = lead[0:10]
            embed = discord.Embed(
                title=f"Wikiguesser leaderboard for {interaction.guild.name if ser_id != 0 else "THE ENTIRE WORLD"}",
            )
            score = [str(uid["score"]) for uid in lead]
            names = [f"{lead.index(uid)}. {uid["name"]}" for uid in lead]
            embed.add_field(name="Users", value=f"{"\n".join(names)}\n")
            embed.add_field(name="Score", value=f"{"\n".join(score)}\n")

            await interaction.followup.send(embed=embed)
        except discord.app_commands.errors.CommandInvokeError as e:
            print(e)
