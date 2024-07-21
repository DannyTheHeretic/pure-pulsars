import discord
from discord import app_commands
import time

from database.database_core import DATA
from wikiutils import search_wikipedia, make_embed

def main(tree: app_commands.CommandTree) -> None:
    """Create a wikiguesser command."""

    @tree.command(
        name="deathmatch",
        description="Multiplayer wikiguesser but whoever loses gets shot",

    )
    async def never_gonna_give_you_up(interaction: discord.Interaction, user: discord.User) -> None:
        await interaction.response.send_message(f"Starting deathmatch between {user.mention} and {interaction.user.mention}...")
        article = await search_wikipedia("Never gonna give you up")
        time.sleep(1)
        await interaction.followup.send(embed=make_embed(article))
       

