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
            await interaction.response.defer(thinking=True)
            embed = discord.embeds.Embed()
            try:
                if user is None:
                    user = interaction.user
                user_data = await DATA.get_user(interaction.guild_id, user.id)
                for key, value in user_data.items():
                    _ = value
                    if key.lower() == "userid":
                        continue
                    if key.lower() == "last_played":
                        _ = humanize.naturaltime(datetime.now(UTC) - value)
                    embed.add_field(
                        name=key.capitalize().replace("_", " ").replace("Failure", "Failures"),
                        value=_,
                        inline=False,
                    )
            except NullUserError:
                await interaction.followup.send(content=f"User: {user.mention} has **not** played any games")
                return

            await interaction.followup.send(embed=embed)
        except discord.app_commands.errors.CommandInvokeError as e:
            print(e)
