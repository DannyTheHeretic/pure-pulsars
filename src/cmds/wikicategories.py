"""Request categories for wiki-guesser.

To-do:
-----
+ [ ] Figure out assert issue with ruff
    + Just noqa'ing them for now
+ [ ] Return a relevant page with the proper category
    + Have the Page.category stuff to work with
+ [ ] Handle pages with multiple categories
    + [ ] If none exist, tell the user
        + [ ] Recommend other categories.
    + [ ] Make input as easy as possible for the user

"""

import logging
import unittest
from dataclasses import dataclass

import discord
from discord.app_commands import CommandTree
from pywikibot import Page

from wikiutils import search_wikipedia

HELP_RESPONSE = "No category provided."


@dataclass
class WikiCategoriesResponse:
    """Data for category responses to make them easy to validate/access."""

    message: str
    articles: list[Page]


class WikiCategoriesCommand:
    """Process, make requests, and start other functions relevant to the command."""

    @classmethod
    def process(cls, categories: str) -> str:
        """Process a categories request."""
        logging.info("WikiCategoriesCommand.process recieved categories: %s", categories)

        if not categories:
            return HELP_RESPONSE

        # TODO: This is a placeholder for category resolution logic.
        articles = [search_wikipedia(categories)]

        return WikiCategoriesResponse(
            message=f"Category: {categories.title()}",
            articles=articles,
        )


def main(tree: CommandTree) -> None:
    """Assign the wiki-categories command."""

    @tree.command(
        name="wiki-categories",
        description="Start a game of wiki-guesser with a category.",
    )
    async def wiki_categories(interaction: discord.Interaction, categories: str) -> None:
        """Wrap function used for the command tree, see WikiCategoriesCommand for details of behavior.

        Arguments:
        ---------
            interaction : discord.Interaction
                The interaction object.

            categories: str
                A string representing the category (no seperators) or
                categories (separated by a separator).

        """
        # TODO(teald): This should really just be a single call, passing the interaction
        #              to be managed by the WikiCategoriesCommand.
        response = WikiCategoriesCommand.process(categories)

        await interaction.response.send_message(response)


class TestWikiCategoriesCommand(unittest.TestCase):
    """Tests for the WikiCategoriesCommand class."""

    single_category_str: str = "astronomy"
    multiple_category_strs: tuple[str] = (
        "astronomy, history",
        "astronomy,history",
        "history,astronomy",
    )

    def test_empty_command(self) -> None:
        """Test the wiki-categories slash command without any input."""
        response = WikiCategoriesCommand.process("")

        assert response == HELP_RESPONSE  # noqa: S101

    def test_command_with_category(self) -> None:
        """Test with a specified (literal) category."""
        category_str = self.single_category_str

        response = WikiCategoriesCommand.process(category_str)

        assert f"Category: {category_str.title()}" == response.message  # noqa: S101
        assert len(response.articles) >= 1  # noqa: S101
