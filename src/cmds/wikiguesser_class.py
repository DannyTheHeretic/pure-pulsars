import logging
import secrets
from abc import ABC, abstractmethod
from typing import NamedTuple

import discord
from discord import ButtonStyle, Enum
from discord.utils import MISSING
from pywikibot import Page

from wikiutils import make_embed, search_wikipedia

ACCURACY_THRESHOLD = 0.8
MAX_LEN = 1990


class _Button(NamedTuple):
    style: ButtonStyle = ButtonStyle.secondary
    label: str | None = None
    disabled: bool = False
    custom_id: str | None = None
    url: str | None = None
    emoji: str | discord.Emoji | discord.PartialEmoji | None = None
    row: int | None = None
    sku_id: int | None = None
    links: list[str] | None = None
    owners: list[discord.User] | None = None
    message: str | None = None
    private: bool | None = None


class _Ranked(Enum):
    YES = 1
    NO = 0


class WinLossManagement(ABC):
    """Class that contains abstract methods that define what happens upon winning and what happens upon losing."""

    def __init__(self, winargs: dict, lossargs: dict) -> None:
        super().__init__()
        self.winargs = winargs
        self.lossargs = lossargs

    @abstractmethod
    async def _on_win(self) -> None:
        pass

    @abstractmethod
    async def _on_loss(self) -> None:
        pass


class _Comp(NamedTuple):
    score: list[int]
    winlossmanager: WinLossManagement | None = None
    ranked: bool = False
    article: Page = None
    user: int = 0


class GiveUpButton(discord.ui.Button):
    """Button for exiting/"giving up" on game."""

    _end_message: str = "Thank you for trying!"

    def __init__(self, *, info: _Button, article: Page, view: discord.ui.View) -> None:
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

        # TODO(teald): This may be better handled with a GameState class, or
        # something that can be more easily accessed/passed around.
        self.article = article
        self._view = view

    async def callback(self, interaction: discord.Interaction) -> None:
        """Exit the game."""
        # TODO(teald): Ensure the score is saved properly.
        logging.warning("Score saving is not yet implemented for exiting the game.")

        # Exit the game.
        logging.info("GiveUpButton handling exit for %s.", interaction)

        msg = self._end_message
        article = self.article
        embed = make_embed(article)
        embed.set_footer(text=msg)
        await interaction.response.send_message(embed=embed)
        await self.clean_view(view=self._view)
        await interaction.message.edit(content=interaction.message.content, view=self._view)

    @staticmethod
    async def clean_view(*, view: discord.ui.View) -> None:
        """Clean a view of interactible things (e.g., buttons).

        This method is only static because it's likely useful elsewhere.
        """
        # TODO(teald): Probably better as a helper function.
        logging.debug("Clearing child objects: %s", list(view.children))

        view.clear_items()


class ExcerptButton(discord.ui.Button):
    """Button for revealing more of the summary."""

    def __init__(
        self,
        *,
        info: _Button,
        summary: str,
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
        self.summary = summary
        self.score = info.score
        self.ind = 1
        self.owners = info.owners
        self.private = info.private

    async def callback(self, interaction: discord.Interaction) -> None:
        """Reveal more of the summary."""
        await interaction.response.defer()  # TODO: THIS LINE RAISES AN ERROR ON EVERY PRESS BUT IT WORKS AS EXPECTED
        if interaction.user not in self.owners:
            await interaction.response.send_message("You may not interact with this", ephemeral=True)
            return
        self.ind += 1
        self.score[0] -= (len("".join(self.summary[: self.ind])) - len("".join(self.summary[: self.ind - 1]))) // 2

        if self.summary[: self.ind] == self.summary or len(".".join(self.summary[: self.ind + 1])) > MAX_LEN:
            self.view.remove_item(self)
        await interaction.edit_original_response(
            content=f"Excerpt: {". ".join(self.summary[:self.ind])}.", view=self.view
        )
        await interaction.response.defer()


class GuessButton(discord.ui.Button):
    """Button to open guess modal."""

    def __init__(self, *, info: _Button, comp: _Comp, owners: list[discord.User]) -> None:
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
        self.user = comp.user
        self.owners = owners
        self.winlossmanager = comp.winlossmanager

    async def callback(self, interaction: discord.Interaction) -> None:
        """Open guess modal."""
        if interaction.user not in self.owners:
            await interaction.response.send_message("You may not interact with this", ephemeral=True)
            return
        self.guess_modal = GuessInput(
            title="Guess!",
            comp=_Comp(
                ranked=self.ranked,
                article=self.article,
                score=self.score,
                user=self.user,
                winlossmanager=self.winlossmanager,
            ),
        )
        self.guess_modal.add_item(discord.ui.TextInput(label="Your guess", placeholder="Enter your guess here..."))
        await interaction.response.send_modal(self.guess_modal)


class GuessInput(discord.ui.Modal):
    """Input feild for guessing."""

    def __init__(
        self,
        *,
        title: str = MISSING,
        timeout: float | None = None,
        custom_id: str = MISSING,
        comp: _Comp,
    ) -> None:
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)
        self.ranked = comp.ranked
        self.score = comp.score
        self.user = comp.user
        self.article = comp.article
        self.winlossmanager = comp.winlossmanager

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Guess the article."""
        await interaction.response.defer()
        page = await search_wikipedia(self.children[0].value)
        if page.title() == self.article.title():
            await self.winlossmanager.on_win()
            await interaction.followup.send(
                "Good job", ephemeral=True
            )  # * IMPORTANT, you must respond to the interaction for the modal to close
            # * or else it will just say something went wrong
            return
        await self.winlossmanager.on_loss()
        await interaction.followup.send(
            "bad job", ephemeral=True
        )  # * IMPORTANT, you must respond to the interaction for the modal to close
        # * or else it will just say something went wrong
        self.score[0] -= 5


class LinkListButton(discord.ui.Button):
    """Button for showing more links from the list."""

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
        self.score = comp.score
        self.message = info.message
        self.links = info.links
        self.owners = info.owners
        self.private = info.private

    async def callback(self, interaction: discord.Interaction) -> None:
        """Show 10 diffrent links."""
        if interaction.user not in self.owners:
            await interaction.response.send_message("You may not interact with this", ephemeral=True)
            return

        selected_links = []
        self.score[0] -= 10
        for _ in range(10):
            selected_links.append(self.links.pop(secrets.randbelow(len(self.links) - 1)))
            if len(self.links) == 1:
                selected_links.append(self.links.pop(0))
                break
        if selected_links == []:
            await interaction.response.send_message("No more links!")
        logging.info("Private: %s", self.private)
        await interaction.response.send_message(
            content=f"{self.message}\n```{"\n".join(selected_links)}```",
            view=self.view,
            delete_after=180,
            ephemeral=self.private,
        )
        if len(self.links) == 0:
            self.view.remove_item(self)
