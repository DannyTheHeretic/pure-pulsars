from datetime import UTC, datetime
from difflib import SequenceMatcher
from random import randint
from typing import NamedTuple

import discord
from discord import ButtonStyle, Enum, app_commands
from discord.utils import MISSING
from pywikibot import Page

from database.database_core import DATA, NullUserError
from database.user import User
from wikiutils import is_article_title, make_embed, rand_wiki

ACCURACY_THRESHOLD = 0.8


class _Button(NamedTuple):
    style: ButtonStyle = ButtonStyle.secondary
    label: str | None = None
    disabled: bool = False
    custom_id: str | None = None
    url: str | None = None
    emoji: str | discord.Emoji | discord.PartialEmoji | None = None
    row: int | None = None
    sku_id: int | None = None


class _Comp(NamedTuple):
    score: list[int]
    ranked: bool = False
    article: Page = None


class _Ranked(Enum):
    YES = 1
    NO = 0


class ExcerptButton(discord.ui.Button):
    """Button for revealing more of the summary."""

    def __init__(self, *, info: _Button, summary: str, score: list[int]) -> None:
        super().__init__(
            style=info.style,
            label=info.label,
            disabled=info.disabled,
            custom_id=info.custom_id,
            url=info.url,
            emoji=info.emoji,
            row=info.row,
            sku_id=info.sku_id,
        )
        self.summary = summary
        self.score = score
        self.ind = 1

    async def callback(self, interaction: discord.Interaction) -> None:
        """Reveal more of the summary."""
        self.ind += 1
        self.score[0] -= (len(''.join(self.summary[: self.ind]))-len(''.join(self.summary[: self.ind-1]))) // 2

        if self.summary[: self.ind] == self.summary or len(".".join(self.summary[: self.ind + 1])) > 1990:  # noqa:PLR2004
            self.view.remove_item(self)

        await interaction.message.edit(content=f"Excerpt: {". ".join(self.summary[:self.ind])}.", view=self.view)
        await interaction.response.defer()


class GuessButton(discord.ui.Button):
    """Button to open guess modal."""

    def __init__(self, *, info: _Button, comp: _Comp) -> None:
        super().__init__(
            style=info.style,
            label=info.label,
            disabled=info.disabled,
            custom_id=info.custom_id,
            url=info.url,
            emoji=info.emoji,
            row=info.row,
            sku_id=info.sku_id,
        )
        self.ranked = comp.ranked
        self.article = comp.article
        self.score = comp.score

    async def callback(self, interaction: discord.Interaction) -> None:
        """Open guess modal."""
        guess_modal = GuessInput(
            title="Guess!", comp=_Comp(ranked=self.ranked, article=self.article, score=self.score)
        )
        guess_modal.add_item(discord.ui.TextInput(label="Your guess", placeholder="Enter your guess here..."))
        await interaction.response.send_modal(guess_modal)


class GuessInput(discord.ui.Modal):
    """Input feild for guessing."""

    def __init__(
        self, *, title: str = MISSING, timeout: float | None = None, custom_id: str = MISSING, comp: _Comp
    ) -> None:
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)
        self.ranked = comp.ranked
        self.score = comp.score
        self.article = comp.article

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Guess the article."""
        if (
            SequenceMatcher(None, self.children[0].value.lower(), self.article.title().lower()).ratio()
            >= ACCURACY_THRESHOLD
        ):
            embed = make_embed(self.article)
            # TODO: For Some Reason this doesnt work, it got mad
            """await interaction.message.edit(view=None)"""
            msg = f"Congratulations {interaction.user.mention}! You figured it out, your score was {self.score[0]}!"
            await interaction.response.send_message(content=msg, embed=embed, ephemeral=self.ranked)
            print(self.ranked)
            if self.ranked:
                print(self.score[0])
                user = interaction.user
                try:
                    db_ref_user = await DATA.get_user(interaction.guild_id, user.id)
                    await DATA.update_value_for_user(
                        guild_id=interaction.guild_id,
                        user_id=user.id,
                        key="times_played",
                        value=db_ref_user["times_played"] + 1,
                    )
                    await DATA.update_value_for_user(
                        guild_id=interaction.guild_id,
                        user_id=user.id,
                        key="score",
                        value=db_ref_user["score"] + self.score[0],
                    )
                    await DATA.update_value_for_user(
                        guild_id=interaction.guild_id,
                        user_id=user.id,
                        key="last_played",
                        value=datetime.now(UTC).timestamp(),
                    )
                    await DATA.update_value_for_user(
                        guild_id=interaction.guild_id, user_id=user.id, key="wins", value=db_ref_user["wins"] + 1
                    )
                except NullUserError:
                    new_user = User(
                        user.global_name,
                        user.id,
                        times_played=1,
                        wins=1,
                        score=self.score,
                        last_played=datetime.now(UTC).timestamp(),
                    )
                    DATA.add_user(user.id, new_user, interaction.guild_id)
            return
        await interaction.response.send_message("That's incorect, please try again.", ephemeral=True)
        self.score[0] -= 5


class LinkListButton(discord.ui.Button):
    """Button for showing more links from the list."""

    def __init__(
        self,
        *,
        info: _Button,
        comp: _Comp,
        links: list[str],
        message: str,
    ) -> None:
        super().__init__(
            style=info.style,
            label=info.label,
            disabled=info.disabled,
            custom_id=info.custom_id,
            url=info.url,
            emoji=info.emoji,
            row=info.row,
            sku_id=info.sku_id,
        )
        self.ranked = comp.ranked
        self.score = comp.score
        self.message = message
        self.links = links

    async def callback(self, interaction: discord.Interaction) -> None:
        """Show 10 diffrent links."""
        if interaction.message.content:
            await interaction.message.edit(view=None)
        else:
            await interaction.message.delete()

        selected_links = []
        self.score[0] -= 10

        for _ in range(10):
            selected_links.append(self.links.pop(randint(0, len(self.links) - 1)))  # noqa: S311
            if len(self.links) == 1:
                selected_links.append(self.links.pop(0))
                break
        await interaction.response.send_message(
            content=f"{self.message}\n```{"\n".join(selected_links)}```",
            view=self.view,
            ephemeral=self.ranked,
            delete_after=180,
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
    async def wiki(interaction: discord.Interaction, ranked: _Ranked = _Ranked.NO) -> None:
        ranked: bool = bool(ranked.value)
        score = [1000]

        await interaction.response.send_message(content="Hello, we are processing your request...", ephemeral=ranked)
        article = await rand_wiki()
        print(article.title())

        links = [link.title() for link in article.linkedPages() if is_article_title(link.title())]
        backlinks = [link.title() for link in article.backlinks() if is_article_title(link.title())]

        excerpt = article.extract(chars=1200)

        for i in article.title().split():
            excerpt = excerpt.replace(i, "~~CENSORED~~")

        sentances = excerpt.split(". ")

        excerpt_view = discord.ui.View()
        guess_button = GuessButton(
            info=_Button(label="Guess!", style=discord.ButtonStyle.success),
            comp=_Comp(ranked=ranked, article=article, score=score),
        )
        excerpt_button = ExcerptButton(
            info=_Button(label="Show more", style=discord.ButtonStyle.primary), summary=sentances, score=score
        )

        excerpt_view.add_item(excerpt_button)
        excerpt_view.add_item(guess_button)

        await interaction.followup.send(
            content=f"Excerpt: {sentances[0]}.",
            view=excerpt_view,
            wait=True,
            ephemeral=ranked,
        )

        view = discord.ui.View()
        link_button = LinkListButton(
            info=_Button(
                label="Show more links in article",
            ),
            comp=_Comp(score=score, ranked=ranked),
            links=links,
            message="Links in article:",
        )
        backlink_button = LinkListButton(
            info=_Button(
                label="Show more articles that link to this one",
            ),
            comp=_Comp(score=score, ranked=ranked),
            links=backlinks,
            message="Articles that link to this one:",
        )

        view.add_item(link_button)
        view.add_item(backlink_button)

        await interaction.followup.send(view=view, wait=True, ephemeral=ranked)
        await interaction.delete_original_response()
