"""Wiki search command."""

import logging

import discord
from discord import app_commands
from discord.app_commands.errors import CommandInvokeError
from discord.errors import NotFound
from pywikibot.exceptions import InvalidTitleError

from wikiutils import make_embed, search_wikipedia


def main(tree: app_commands.CommandTree) -> None:
    """Create wiki search command."""

    @tree.command(
        name="wiki-search",
        description="get a wikipedia article that you searched for",
    )
    @app_commands.describe(query="What are you asking it?")
    async def wiki(interaction: discord.Interaction, query: str) -> None:
        """Search wikipedia for an article using a query.

        Args:
        ----
        interaction (discord.Interaction): The interaction object.
        query (str): The query to search wikipedia for.

        """
        try:
            await interaction.response.send_message(content="Finding your really cool article...")
            embed = await make_embed(article=await search_wikipedia(query))
            await interaction.followup.send(embed=embed)
            await interaction.delete_original_response()
        except InvalidTitleError:
            await interaction.followup.send(content="Sorry, the article title was not valid.")
            await interaction.delete_original_response()
        except AttributeError:
            await interaction.followup.send(
                content="Sorry, an error with that article occured, please try a different one."
            )
            await interaction.delete_original_response()
        except NotFound as e:
            logging.info("Wiki-Search:\nFunc: main\nException %s", e)
        except CommandInvokeError as e:
            logging.info("Wiki-Search:\nFunc: main\nException %s", e)
