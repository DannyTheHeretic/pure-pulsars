from difflib import SequenceMatcher
from random import randint

import discord
from discord import ButtonStyle, app_commands
from discord.utils import MISSING

from wikiutils import is_article_title, make_embed, rand_wiki

from database.leaderboard import LeaderboardDatabase

ACCURACY_THRESHOLD = 0.8


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

    def __init__(
        self,
        *,
        style: ButtonStyle = ButtonStyle.secondary,
        label: str | None = None,
        disabled: bool = False,
        custom_id: str | None = None,
        url: str | None = None,
        emoji: str | discord.Emoji | discord.PartialEmoji | None = None,
        row: int | None = None,
        sku_id: int | None = None,
        ranked : bool
    ):
        super().__init__(
            style=style,
            label=label,
            disabled=disabled,
            custom_id=custom_id,
            url=url,
            emoji=emoji,
            row=row,
            sku_id=sku_id,
        )
        self.ranked = ranked
    async def callback(self, interaction: discord.Interaction) -> None:
        """Open guess modal."""
        guess_modal = GuessInput(title="Guess!", ranked=self.ranked)
        guess_modal.add_item(discord.ui.TextInput(label="Your guess", placeholder="Enter your guess here..."))
        guess_modal.article = self.article
        await interaction.response.send_modal(guess_modal)


class GuessInput(discord.ui.Modal):
    """Input feild for guessing."""

    def __init__(
        self, *, title: str = ..., timeout: float | None = None, custom_id: str = ..., ranked: bool = False
    ) -> None:
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)
        self.ranked = ranked

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Guess the article."""
        leaderboard = LeaderboardDatabase()
        if (
            SequenceMatcher(None, self.children[0].value.lower(), self.article.title.lower()).ratio()
            >= ACCURACY_THRESHOLD
        ):
            if self.ranked:
                embed = make_embed(self.article)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                await interaction.message.edit(view=None)
                leaderboard.update_placement()
            else:
                embed = make_embed(self.article)
                await interaction.response.send_message(embed=embed, ephemeral=False)
                await interaction.message.edit(view=None)
            return
        await interaction.response.send_message("That's incorect, please try again.", ephemeral=True)


class LinkListButton(discord.ui.Button):
    """Button for showing more links from the list."""

    def __init__(
        self,
        *,
        style: discord.ButtonStyle = ButtonStyle.secondary,
        label: str | None = None,
        disabled: bool = False,
        custom_id: str | None = None,
        url: str | None = None,
        emoji: str | discord.Emoji | discord.PartialEmoji | None = None,
        row: int | None = None,
        sku_id: int | None = None,
        ranked: bool,
    ):
        super().__init__(
            style=style,
            label=label,
            disabled=disabled,
            custom_id=custom_id,
            url=url,
            emoji=emoji,
            row=row,
            sku_id=sku_id,
        )
        self.ranked = ranked

    async def callback(self, interaction: discord.Interaction) -> None:
        """Show 10 diffrent links."""
        # if interaction.message.content:
        #     await interaction.message.edit(view=None) Don't know what this does but it was raising an error and
        # when I commented it out no other errors appeared so :shrug:

        selected_links = []

        for _ in range(10):
            selected_links.append(self.links.pop(randint(0, len(self.links) - 1)))  # noqa: S311
            if len(self.links) == 1:
                selected_links.append(self.links.pop(0))
                break
        if self.ranked:
            await interaction.response.send_message(
                content=f"{self.message}\n```{"\n".join(selected_links)}```", view=self.view, ephemeral=True
            )
        else:
            await interaction.response.send_message(
                content=f"{self.message}\n```{"\n".join(selected_links)}```", view=self.view, ephemeral=False
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
    async def wiki(interaction: discord.Interaction, ranked: bool) -> None:
        if ranked:
            await interaction.response.send_message(content="Hello, we are processing your request...", ephemeral=True)
        else:
            await interaction.response.send_message(
                content="Hello, we are processing your request...", ephemeral=False
            )
        article = rand_wiki()

        if not article:
            if ranked:
                await interaction.followup.send(content="An error occured")
                await interaction.delete_original_response()
            else:
                await interaction.followup.send(content="An error occured")
                await interaction.delete_original_response()
            return

        links = [link for link in article.links if is_article_title(link)]
        backlinks = [link for link in article.backlinks if is_article_title(link)]

        excerpt = article.summary

        for i in article.title.split():
            excerpt = excerpt.replace(i, "~~CENSORED~~")

        sentances = excerpt.split(". ")

        excerpt_view = discord.ui.View()
        guess_button = GuessButton(label="Guess!", style=discord.ButtonStyle.success, ranked=ranked)
        excerpt_button = ExcerptButton(label="Show more", style=discord.ButtonStyle.primary)
        excerpt_view.add_item(excerpt_button)
        excerpt_view.add_item(guess_button)
        if ranked:
            excerpt_view.message = await interaction.followup.send(
                content=f"Excerpt: {sentances[0]}.",
                view=excerpt_view,
                wait=True,
                ephemeral=True,
            )
        else:
            excerpt_view.message = await interaction.followup.send(
                content=f"Excerpt: {sentances[0]}.",
                view=excerpt_view,
                wait=True,
                ephemeral=False,
            )

        excerpt_button.summary = sentances
        guess_button.article = article

        view = discord.ui.View()
        link_button = LinkListButton(label="Show more links in article", ranked=ranked)
        backlink_button = LinkListButton(label="Show more articles that link to this one", ranked=ranked)

        view.add_item(link_button)
        view.add_item(backlink_button)

        link_button.links = links
        link_button.message = "Links in article:"
        backlink_button.links = backlinks
        backlink_button.message = "Articles that link to this one:"
        if ranked:
            view.message = await interaction.followup.send(view=view, wait=True, ephemeral=True)
        else:
            view.message = await interaction.followup.send(view=view, wait=True, ephemeral=False)
        await interaction.delete_original_response()
