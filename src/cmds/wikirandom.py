"""Wiki Random Command."""

import logging

import discord
from discord import NotFound, app_commands
from discord.app_commands.errors import CommandInvokeError

from wikiutils import make_embed, rand_wiki


def main(tree: app_commands.CommandTree) -> None:
    """Create random command."""

    @tree.command(
        name="wiki-random",
        description="get a random wikipedia article",
    )
    async def wiki(interaction: discord.Interaction) -> None:
        """Run the wiki-random command.

        This command will get a random wikipedia article and send it to the user.
        """
        try:
            await interaction.response.send_message(content="Finding a really cool article...")
            article = await rand_wiki()
            embed = await make_embed(article=article)
            await interaction.followup.send(embed=embed)
            await interaction.delete_original_response()
        except NotFound as e:
            logging.info("Wiki-Random:\nFunc: main\nException %s", e)
        except CommandInvokeError as e:
            logging.info("Wiki-Random:\nFunc: main\nException %s", e)
