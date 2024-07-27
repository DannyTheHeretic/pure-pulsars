import secrets
from abc import ABC, abstractmethod
from enum import Enum
from typing import NamedTuple

import discord
from discord import ButtonStyle
from discord.utils import MISSING
from pywikibot import Page

from wikiutils import search_wikipedia

ACCURACY_THRESHOLD = 0.8
MAX_LEN = 1990


class GameType(Enum):
    """Possible games to be played"""
    wikiguesser = 0
    wikianimal = 1


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
    # TODO: DOCSTRING
    score: list[int]
    ranked: bool = False
    article: Page = None
    user: int = 0
    game_type: GameType = GameType.wikiguesser


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


class ExcerptButton(discord.ui.Button):
    """Button for revealing more of the summary."""

    def __init__(
        self, *, info: _Button, summary: str, score: list[int], owners: list[discord.User], private: bool
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
        self.score = score
        self.ind = 1
        self.owners = owners
        self.private = private

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

    def __init__(
        self, *, info: _Button, comp: _Comp, owners: list[discord.User], winlossmanager: WinLossManagement
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
        self.article = comp.article
        self.score = comp.score
        self.user = comp.user
        self.game_type = comp.game_type
        self.owners = owners
        self.winlossmanager = winlossmanager

    async def callback(self, interaction: discord.Interaction) -> None:
        """Open guess modal."""
        if interaction.user not in self.owners:
            await interaction.response.send_message("You may not interact with this", ephemeral=True)
            return
        self.guess_modal = GuessInput(
            title="Guess!",
            comp=_Comp(
                ranked=self.ranked, article=self.article, score=self.score, user=self.user, game_type=self.game_type
            ),
            winlossmanager=self.winlossmanager,
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
        winlossmanager: WinLossManagement,
    ) -> None:
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)
        self.comp = comp
        self.ranked = comp.ranked
        self.score = comp.score
        self.user = comp.user
        self.article = comp.article
        self.game_type = comp.game_type
        self.winlossmanager = winlossmanager

    async def on_submit(self, interaction: discord.Interaction) -> None:
        user_input = self.children[0].value
        print("user input ", user_input)
        print("comp ", self.comp)
        print("game_type wikiguesser", GameType.wikiguesser)
        print(self.game_type == GameType.wikiguesser)
        print(self.game_type == GameType.wikianimal)
        if self.game_type == GameType.wikiguesser:
            await wikiguesser_on_submit(self.comp, interaction, user_input, self.winlossmanager)
        elif self.game_type == GameType.wikianimal:
            await wikianimal_on_submit(self.comp, interaction, user_input, self.winlossmanager)


async def wikiguesser_on_submit(
    comp: _Comp, interaction: discord.Interaction, user_guess: str, winlossmanager: WinLossManagement
) -> None:
    """Guess the article."""
    await interaction.response.defer()
    # if self.ranked and interaction.user.id != self.user:
    #     await interaction.response.send_message(
    #         "You cannot guess because you were not the on who started this ranked game of wiki-guesser.",
    #         ephemeral=True,  # noqa: ERA001
    #     )  # noqa: ERA001, RUF100
    #     return  # noqa: ERA001
    # This is probably redundant because GuessButton already checks for owners
    print("1")
    page = await search_wikipedia(user_guess)
    print("2")
    if page.title() == comp.article.title():
        print("3")
        await winlossmanager._on_win()
        await interaction.followup.send(
            "Good job", ephemeral=True
        )  # * IMPORTANT, you must respond to the interaction for the modal to close
        # * or else it will just say something went wrong
        return
    print("4")
    await winlossmanager._on_loss()
    print("5")
    await interaction.followup.send(
        "bad job", ephemeral=True
    )  # * IMPORTANT, you must respond to the interaction for the modal to close
    # * or else it will just say something went wrong
    comp.score[0] -= 5


async def wikianimal_on_submit(
    comp: _Comp, interaction: discord.Interaction, user_guess: str, winlossmanager: WinLossManagement
) -> None:
    print("well you made it this far")


class LinkListButton(discord.ui.Button):
    """Button for showing more links from the list."""

    def __init__(  # noqa: PLR0913
        self, *, info: _Button, comp: _Comp, links: list[str], message: str, owners: list[discord.User], private: bool
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
        self.score = comp.score
        self.message = message
        self.links = links
        self.owners = owners
        self.private = private

    async def callback(self, interaction: discord.Interaction) -> None:
        """Show 10 diffrent links."""
        if interaction.user not in self.owners:
            await interaction.response.send_message("You may not interact with this", ephemeral=True)
            return
        # if not interaction.message.content:
        #     await interaction.delete_original_response()  # noqa: ERA001

        selected_links = []
        self.score[0] -= 10
        for _ in range(10):
            selected_links.append(self.links.pop(secrets.randbelow((self.links) - 1)))
            if len(self.links) == 1:
                selected_links.append(self.links.pop(0))
                break
        if selected_links == []:
            await interaction.response.send_message("No more links!")
        await interaction.response.send_message(
            content=f"{self.message}\n```{"\n".join(selected_links)}```",
            view=self.view,
            delete_after=180,
            ephemeral=self.private,
        )
        if len(self.links) == 0:
            self.view.remove_item(self)
