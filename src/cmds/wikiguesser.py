from random import randint

import discord
from discord import app_commands

from wikiutils import is_text_link, rand_wiki


class LinkListButton(discord.ui.Button):  # noqa: D101
    async def callback(self, interaction: discord.Interaction) -> None:  # noqa: D102
        selected_links = []

        for _ in range(10):
            selected_links.append(self.links.pop(randint(0, len(self.links) - 1)))  # noqa: S311
            if len(self.links) == 0:
                break

        await interaction.response.send_message(
            content="Links in articles: " + "\n".join(selected_links),
            view=self.view,
        )
        if len(self.links) == 0:
            self.view.remove_item(self)


def main(tree: app_commands.CommandTree) -> None:
    """Create Wiki Guesser command."""

    @tree.command(
        name="wiki-guesser",
        description="Starts a game of wiki-guesser! Try and find what wikipedia article your in.",
        guild=discord.Object(id=1262497899925995563),
    )
    async def wiki(interaction: discord.Interaction) -> None:
        await interaction.response.send_message(content="Hello, we are processing your request...")

        article = rand_wiki()

        if not article:
            await interaction.followup.send(content="An error occured")
            await interaction.delete_original_response()
            return

        links = [link for link in article.links if is_text_link(link)]
        backlinks = [link for link in article.backlinks if is_text_link(link)]

        excerpt = article.summary.split(". ")[0]

        for i in article.title.split():
            excerpt = excerpt.replace(i, "CENSORED")

        await interaction.followup.send(content=f"Excerpt: {excerpt}")

        view = discord.ui.View()
        link_button = LinkListButton(label="Show more links in article")
        backlink_button = LinkListButton(label="Show more articles that link to this one")
        view.add_item(link_button)
        view.add_item(backlink_button)

        link_button.links = links
        backlink_button.links = backlinks

        await interaction.followup.send(view=view)
        await interaction.delete_original_response()
