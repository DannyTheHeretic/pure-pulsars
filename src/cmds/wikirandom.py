import logging

import discord
from discord import app_commands

from wikiutils import make_embed, rand_wiki


def main(tree: app_commands.CommandTree) -> None:
    """Create Wiki Guesser command."""

    @tree.command(
        name="wiki-random",
        description="get a random wikipedia article",
    )
    async def wiki(interaction: discord.Interaction) -> None:
        try:
            await interaction.response.send_message(content="Finding a really cool article...")
            article = await rand_wiki()
            embed = make_embed(article=article)
            await interaction.followup.send(embed=embed)
            await interaction.delete_original_response()
        except discord.app_commands.errors.CommandInvokeError as e:
            logging.critical("Exception %s", e)
