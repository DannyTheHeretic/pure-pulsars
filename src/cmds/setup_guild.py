import discord
from discord import app_commands

from database.leaderboard import LeaderboardDatabase


def main(tree: app_commands.CommandTree) -> None:
    """Create Wiki Guesser command."""

    @tree.command(
        name="setup-wikiguesser-server-board",
        description="required for your server to have it's own leaderboard",
        guild=discord.Object(id=1262497899925995563),

    )
    async def setup_guild(interaction: discord.Interaction) -> None:
        leaderboard = LeaderboardDatabase()
        await interaction.response.defer(thinking=True, ephemeral=True)
        leaderboard.add_guild(interaction.guild_id)
        await interaction.followup.send("Your server now supports server leaderboards", username="Placeholder for now")
