from difflib import SequenceMatcher
from random import randint

import discord
from discord import app_commands

from wikiutils import is_article_title, rand_wiki

ACCURACY_THRESHOLD = 0.8


class TimeoutView(discord.ui.View):
    """View that disables children on timeout."""

    async def on_timeout(self) -> None:
        """Disables children."""
        for child in self.children:
            child.disabled = True

        await self.message.edit(view=self)


class ExcerptButton(discord.ui.Button):
    """Button for revealing more of the summary."""

    async def callback(self, interaction: discord.Interaction) -> None:
        """Reveal more of the summary."""
        if not hasattr(self, "ind"):
            self.ind = 1
        self.ind += 1

        if self.summary[: self.ind] == self.summary or len(".".join(self.summary[: self.ind + 1])) > 1990:  # noqa:PLR2004
            self.view.remove_item(self)

        await interaction.message.edit(content=f"Excerpt: {". ".join(self.summary[:self.ind])}.", view=self.view)
        await interaction.response.defer()


class GuessButton(discord.ui.Button):
    """Button to open guess modal."""

    async def callback(self, interaction: discord.Interaction) -> None:
        """Open guess modal."""
        guess_modal = GuessInput(title="Guess!")
        guess_modal.add_item(discord.ui.TextInput(label="Your guess", placeholder="Enter your guess here..."))
        guess_modal.correct = self.correct
        await interaction.response.send_modal(guess_modal)


class GuessInput(discord.ui.Modal):
    """Input feild for guessing."""

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Guess the article."""
        if SequenceMatcher(None, self.children[0].value.lower(), self.correct.lower()).ratio() >= ACCURACY_THRESHOLD:
            await interaction.response.send_message(
                f"Congratulations! You figured it out, the article title was \
                {self.correct} [read more] \
                (https://en.wikipedia.org/wiki/{self.correct.replace(" ","_")})! Thanks for playing.",
            )
            await interaction.message.edit(view=None)
            return
        await interaction.response.send_message("That's incorect, please try again.", ephemeral=True)


class LinkListButton(discord.ui.Button):
    """Button for showing more links from the list."""

    async def callback(self, interaction: discord.Interaction) -> None:
        """Show 10 diffrent links."""
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

        links = [link for link in article.links if is_article_title(link)]
        backlinks = [link for link in article.backlinks if is_article_title(link)]

        excerpt = article.summary

        for i in article.title.split():
            excerpt = excerpt.replace(i, "~~CENSORED~~")

        sentances = excerpt.split(". ")

        excerpt_view = TimeoutView()
        guess_button = GuessButton(label="Guess!", style=discord.ButtonStyle.success)
        excerpt_button = ExcerptButton(label="Show more", style=discord.ButtonStyle.primary)
        excerpt_view.add_item(excerpt_button)
        excerpt_view.add_item(guess_button)

        excerpt_view.message = await interaction.followup.send(
            content=f"Excerpt: {sentances[0]}.",
            view=excerpt_view,
            wait=True,
        )

        excerpt_button.summary = sentances
        guess_button.correct = article.title

        view = TimeoutView()
        link_button = LinkListButton(label="Show more links in article")
        backlink_button = LinkListButton(label="Show more articles that link to this one")

        view.add_item(link_button)
        view.add_item(backlink_button)

        link_button.links = links
        link_button.message = "Links in article:"
        backlink_button.links = backlinks
        backlink_button.message = "Articles that link to this one:"

        view.message = await interaction.followup.send(view=view, wait=True)
        await interaction.delete_original_response()
