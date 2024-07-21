import discord
from discord import app_commands

from dotenv import load_dotenv
import os

from database.database_core import DATA
from wikiutils import search_wikipedia, make_embed

def main(tree: app_commands.CommandTree) -> None:
    """???"""

    @tree.command(
        name="h",
        description="???",

    )
    async def question_mark_question_mark_question_mark(interaction: discord.Interaction) -> None:
        await interaction.response.send_message("h", ephemeral=True)
        h = await search_wikipedia(os.environ['h'])
        interaction.followup.send(embed=make_embed(h))
       

