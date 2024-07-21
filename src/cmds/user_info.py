import discord
from discord import app_commands

from database.database_core import DATA, NullUserError


def main(tree: app_commands.CommandTree) -> None:
    """Create user-info command."""

    @tree.command(
        name="user-info",
        description="Returns your stats",
    )
    async def user_info(interaction: discord.Interaction, user: discord.User) -> None:
        await interaction.response.defer(thinking=True)
        embed = discord.embeds.Embed()
        try:
            user_data = await DATA.get_user(interaction.guild_id, user.id)
            for key, value in user_data.items():
                if key.lower() == "userid":
                    continue
                embed.add_field(
                    name=key.capitalize().replace("_", " ").replace("Failure", "Failures"),
                    value=value,
                    inline=False,
                )
        except NullUserError:
            await interaction.followup.send(content=f"User: {user.mention} has **not** been added")
            return

        await interaction.followup.send(embed=embed)
