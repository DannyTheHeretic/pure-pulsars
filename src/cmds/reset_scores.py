import discord
from discord import app_commands

from database.database_core import DATA


def main(tree: app_commands.CommandTree) -> None:
    """Create Wiki Guesser reset-scores command."""

    @tree.command(
        name="reset-scores",
        description="Reset scores of all users in this guild for this guild",
    )
    async def reset_scores(interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)
        if interaction.channel.permissions_for(interaction.user).manage_guild:
            data = await DATA.get_server(interaction.guild_id)
            for uid in data:
                await DATA.update_value_for_user(interaction.guild_id, uid, 0, "score")
            await interaction.followup.send("Scores Reset!", ephemeral=True)
        else:
            await interaction.followup.send(
                "You must have **MANAGE SERVER** permissions to reset scores", ephemeral=True
            )
