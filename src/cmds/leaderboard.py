import discord
from discord import Enum, app_commands

from database.database_core import Database


class _GloSer(Enum):
    GLOBAL = 0
    SERVER = 1


def main(tree: app_commands.CommandTree) -> None:
    """Create Wiki Guesser command."""

    def _sort_leaders(e: dict) -> int:
        return e["score"]

    @tree.command(
        name="leaderboard",
        description="Returns your guilds ",
        guild=discord.Object(id=1262497899925995563),
    )
    async def leaderboard(interaction: discord.Interaction, glob: _GloSer = _GloSer.SERVER) -> None:
        ser_id = interaction.guild_id if bool(glob.value) else 0
        await interaction.response.defer(thinking=True)

        database = Database(ser_id)
        lead = list(database.get_server().values())
        lead.sort(key=_sort_leaders, reverse=True)
        lead = lead[0:10]
        embed = discord.Embed(
            title=f"Leaderboard for {interaction.guild.name}",
        )

        ls_uid = [f"- {uid["name"]} /// {uid["score"]}" for uid in lead]
        embed.description = f"{"\n".join(ls_uid)}\n"

        score = [str(uid["score"]) for uid in lead]
        names = [uid["name"] for uid in lead]
        embed.add_field(name="Users", value=f"{"\n".join(names)}\n")
        embed.add_field(name="Score", value=f"{"\n".join(score)}\n")

        await interaction.followup.send(embed=embed)
