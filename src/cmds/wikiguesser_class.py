from abc import ABC, abstractmethod
from random import randint
from typing import NamedTuple

import discord
from discord import ButtonStyle, Enum
from discord.utils import MISSING
from pywikibot import Page

from wikiutils import search_wikipedia

ACCURACY_THRESHOLD = 0.8


class Button(NamedTuple):
    style: ButtonStyle = ButtonStyle.secondary
    label: str | None = None
    disabled: bool = False
    custom_id: str | None = None
    url: str | None = None
    emoji: str | discord.Emoji | discord.PartialEmoji | None = None
    row: int | None = None
    sku_id: int | None = None


class Comp(NamedTuple):
    score: list[int]
    ranked: bool = False
    article: Page = None
    user: int = 0


class _Ranked(Enum):
    YES = 1
    NO = 0

class WinLossManagement(ABC):
    """Class that contains static methods that define what happens upon winning and what happens upon losing."""

    def __init__(self, winargs: dict, lossargs: dict) -> None:
        super().__init__()
        self.winargs = winargs
        self.lossargs = lossargs
    @abstractmethod
    async def on_win(self) -> None:  # noqa: D102
        pass
    @abstractmethod
    async def on_loss(self) -> None:  # noqa: D102
        pass

class ExcerptButton(discord.ui.Button):
    """Button for revealing more of the summary."""

    def __init__(self, *, info: Button, summary: str, score: list[int], owners: list[discord.User], private: bool) -> None:  # noqa: PLR0913
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
        if interaction.user not in self.owners:
            await interaction.response.send_message("You may not interact with this", ephemeral=True)
            return
        self.ind += 1
        self.score[0][0] -= (len("".join(self.summary[: self.ind])) - len("".join(self.summary[: self.ind - 1]))) // 2

        if self.summary[: self.ind] == self.summary or len(".".join(self.summary[: self.ind + 1])) > 1990:  # noqa:PLR2004
            self.view.remove_item(self)
        if self.private:
            await interaction.response.send_message(content=f"Excerpt: {". ".join(self.summary[:self.ind])}.", view=self.view, ephemeral=True)
        await interaction.edit_original_response(content=f"Excerpt: {". ".join(self.summary[:self.ind])}.", view=self.view)
class GuessButton(discord.ui.Button):
    """Button to open guess modal."""

    def __init__(self, *, info: Button, comp: Comp, owners: list[discord.User], winlossmanager: WinLossManagement) -> None:
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
        self.winlossmanager = winlossmanager
    async def callback(self, interaction: discord.Interaction) -> None:
        """Open guess modal."""
        if interaction.user not in self.owners:
            await interaction.response.send_message("You may not interact with this", ephemeral=True)
            return
        guess_modal = GuessInput(
            title="Guess!", comp=Comp(ranked=self.ranked, article=self.article, score=self.score, user=self.user), winlossmanager=self.winlossmanager
        )
        guess_modal.add_item(discord.ui.TextInput(label="Your guess", placeholder="Enter your guess here..."))
        await interaction.response.send_modal(guess_modal)


class GuessInput(discord.ui.Modal):
    """Input feild for guessing."""

    def __init__(  # noqa: PLR0913
            self, *, title: str = MISSING, timeout: float | None = None, custom_id: str = MISSING, comp: Comp, winlossmanager: WinLossManagement
    ) -> None:
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)
        self.ranked = comp.ranked
        self.score = comp.score
        self.user = comp.user
        self.article = comp.article
        self.winlossmanager = winlossmanager

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Guess the article."""
        # if self.ranked and interaction.user.id != self.user:
        #     await interaction.response.send_message(
        #         "You cannot guess because you were not the on who started this ranked game of wiki-guesser.",
        #         ephemeral=True,  # noqa: ERA001
        #     )  # noqa: ERA001, RUF100
        #     return  # noqa: ERA001
        # This is probably redundant because GuessButton already checks for owners

        page = await search_wikipedia(self.children[0].value)
        if page.title() == self.article.title():
            await self.winlossmanager.on_win()
            return
        await self.winlossmanager.on_loss()
        self.score[0][0] -= 5
        self.stop()


class LinkListButton(discord.ui.Button):
    """Button for showing more links from the list."""

    def __init__(  # noqa: PLR0913
        self,
        *,
        info: Button,
        comp: Comp,
        links: list[str],
        message: str,
        owners : list[discord.User],
        private: bool
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
        #     await interaction.delete_original_response()

        selected_links = []
        self.score[0][0] -= 10
        for _ in range(10):
            selected_links.append(self.links.pop(randint(0, len(self.links) - 1)))  # noqa: S311
            if len(self.links) == 1:
                selected_links.append(self.links.pop(0))
                break
        if selected_links == []:
            await interaction.response.send_message('No more links!')
        await interaction.response.send_message(
            content=f"{self.message}\n```{"\n".join(selected_links)}```",
            view=self.view,
            delete_after=180,
            ephemeral=self.private
        )
        if len(self.links) == 0:
            self.view.remove_item(self)

