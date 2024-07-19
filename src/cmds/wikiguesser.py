from random import randint

import discord
from discord import app_commands

from wikiutils import is_text_link, rand_wiki

class ExcerptButton(discord.ui.Button):
    """Button for revealing more of the summary"""

    async def callback(self, interaction: discord.Interaction) -> None:
        """Reveal more of the summary"""

        if not hasattr(self,"ind"):
            self.ind = 1
        self.ind += 1

        await interaction.response.send_message(content=f"Excerpt: {". ".join(self.summary[:self.ind])}.",view=self.view)
        await interaction.message.delete()


class LinkListButton(discord.ui.Button):
    """Button for showing more links from the list"""

    async def callback(self, interaction: discord.Interaction) -> None:
        """Shows 10 diffrent links"""
        if interaction.message.content:
            await interaction.message.edit(view=None)
        else:
            await interaction.message.delete()

        selected_links = []

        for _ in range(10):
            selected_links.append(self.links.pop(randint(0, len(self.links) - 1)))  # noqa: S311
            if len(self.links) == 0:
                break

        await interaction.response.send_message(
            content=f"{self.message}\n```{"\n".join(selected_links)}```",
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

        excerpt = article.summary

        for i in article.title.split():
            excerpt = excerpt.replace(i, "CENSORED")

        sentances = excerpt.split(". ")

        excerpt_view = discord.ui.View()
        excerpt_button = ExcerptButton(label="Show more",style=discord.ButtonStyle.primary)
        excerpt_view.add_item(excerpt_button)

        await interaction.followup.send(content=f"Excerpt: {sentances[0]}.",view=excerpt_view)
        excerpt_button.summary = sentances

        view = discord.ui.View()
        link_button = LinkListButton(label="Show more links in article")
        backlink_button = LinkListButton(label="Show more articles that link to this one")

        view.add_item(link_button)
        view.add_item(backlink_button)

        link_button.links = links
        link_button.message = "Links in article:"
        backlink_button.links = backlinks
        backlink_button.message = "Articles that link to this one:"

        await interaction.followup.send(view=view)
        await interaction.delete_original_response()
