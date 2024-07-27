import logging
import os

import discord
import google.generativeai as genai
from discord import app_commands

from wikiutils import make_embed, rand_wiki

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")


def main(tree: app_commands.CommandTree) -> None:
    """Command to create a Wiki rabbit hole (i.e. searching)."""

    @tree.command(
        name="rabbit-hole",
        description="Dive into wiki-knowledge with Rabbit Hole — information overload through random exploration.",
    )
    async def rabbit_hole(interaction: discord.Interaction) -> None:
        try:
            await interaction.response.defer(thinking=True, ephemeral=True)
            article = await rand_wiki()
            embed = make_embed(article=article)
            await interaction.followup.send(embed=embed)
        except discord.app_commands.errors.CommandInvokeError as e:
            logging.critical("Exception %s", e)
