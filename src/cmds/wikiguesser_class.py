"""Class(es) for managing wiki-guesser logic."""

import logging
import secrets
from abc import ABC, abstractmethod
from typing import NamedTuple

import discord
from discord import ButtonStyle, Enum
from discord.errors import NotFound
from discord.utils import MISSING
from pywikibot import Page
from pywikibot.exceptions import InvalidTitleError

from wikiutils import loss_update, make_embed, search_wikipedia

ACCURACY_THRESHOLD = 0.8
MAX_LEN = 1990


class GameType(Enum):
    """Possible games to be played."""

    wikiguesser = 0
    wikianimal = 1


class _Ranked(Enum):
    YES = 1
    NO = 0


class WinLossManagement(ABC):
    """Class that contains abstract methods that define what happens upon winning and what happens upon losing."""

    def __init__(self, winargs: dict, lossargs: dict) -> None:
        """Initialize the WinLossManagement class.

        Args:
        ----
        winargs (dict): Arguments for winning.
        lossargs (dict): Arguments for losing.

        """
        super().__init__()
        self.winargs = winargs
        self.lossargs = lossargs

    @abstractmethod
    async def on_win(self) -> None:
        """Clean up on win."""

    @abstractmethod
    async def on_loss(self) -> None:
        """Clean up on loss."""


class _Button(NamedTuple):
    """NamedTuple for button information."""

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
    score: list[int] | None = None
    winlossmanager: WinLossManagement | None = None
    ranked: bool = False
    article: Page = None
    user: int = 0
    game_type: GameType = GameType.wikiguesser


class GiveUpButton(discord.ui.Button):
    """Button for exiting/"giving up" on game."""

    _end_message: str = "Thank you for trying!"

    def __init__(self, *, info: _Button, view: discord.ui.View) -> None:
        """Initialize the GiveUpButton class.

        Args:
        ----
        info (_Button): Information about the button.
        view (discord.ui.View): The view to clean up.

        """
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

        self.ranked = info.ranked
        self.article = info.article
        self._view = view

    async def callback(self, interaction: discord.Interaction) -> None:
        """Exit the game."""
        logging.info("GiveUpButton handling exit for %s.", interaction)
        msg = self._end_message
        article = self.article
        embed = make_embed(article)
        embed.set_footer(text=msg)
        for i in [interaction.guild_id, 0]:
            await loss_update(i, user=interaction.user)
        try:
            await interaction.response.send_message(embed=embed, ephemeral=self.ranked)
            await self.clean_view(view=self._view)
            await interaction.message.edit(content=interaction.message.content, view=self._view)
        except NotFound:
            logging.info("Its okay, no worries")

    @staticmethod
    async def clean_view(*, view: discord.ui.View) -> None:
        """Clean a view of interactible things (e.g., buttons).

        This method is only static because it's likely useful elsewhere.
        """
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
        """Initialize the ExcerptButton class.

        Args:
        ----
        info (_Button): Information about the button.
        summary (str): The summary to reveal.

        """
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
        try:
            await interaction.response.defer()

            if interaction.user not in self.owners:
                await interaction.response.send_message("You may not interact with this", ephemeral=True)
                return
            self.ind += 1
            self.score[0] -= (len("".join(self.summary[: self.ind])) - len("".join(self.summary[: self.ind - 1]))) // 2

            if self.summary[: self.ind] == self.summary or len(".".join(self.summary[: self.ind + 1])) > MAX_LEN:
                self.view.remove_item(self)
            await interaction.edit_original_response(
                content=f"Excerpt: {".".join(self.summary[:self.ind])}.", view=self.view
            )
        except NotFound:
            logging.info("Its okay, no worries")


class GuessButton(discord.ui.Button):
    """Button to open guess modal."""

    def __init__(self, *, info: _Button) -> None:
        """Initialize the GuessButton class.

        Args:
        ----
        info (_Button): Information about the button.

        """
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
        self.info = info
        self.ranked = info.ranked
        self.article = info.article
        self.score = info.score
        self.user = info.user
        self.owners = info.owners
        self.winlossmanager = info.winlossmanager

    async def callback(self, interaction: discord.Interaction) -> None:
        """Open guess modal."""
        try:
            if interaction.user not in self.owners:
                await interaction.response.send_message("You may not interact with this", ephemeral=True)
                return
            self.guess_modal = GuessInput(
                title="Guess!",
                info=self.info,
            )
            self.guess_modal.add_item(discord.ui.TextInput(label="Your guess", placeholder="Enter your guess here..."))
            await interaction.response.send_modal(self.guess_modal)
        except NotFound:
            logging.info("Its okay, no worries")


class GuessInput(discord.ui.Modal):
    """Input feild for guessing."""

    def __init__(
        self,
        *,
        title: str = MISSING,
        timeout: float | None = None,
        custom_id: str = MISSING,
        info: _Button,
    ) -> None:
        """Initialize the GuessInput class.

        This class manages displaying a modal for guessing the article, and
        retrieving input from the user.

        Args:
        ----
        title (str): The title of the modal.
        timeout (float | None): The time until the modal times out.
        custom_id (str): The custom ID of the modal.
        info (_Button): Information about the button.

        """
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)
        self.info = info
        self.ranked = info.ranked
        self.score = info.score
        self.user = info.user
        self.article = info.article
        self.game_type = info.game_type
        self.winlossmanager = info.winlossmanager

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Guess the article."""
        user_input = self.children[0].value
        logging.info("user input %s", user_input)
        logging.info("info %s", self.info)
        logging.info("game_type wikiguesser %s", GameType.wikiguesser)
        logging.info(self.game_type == GameType.wikiguesser)
        logging.info(self.game_type == GameType.wikianimal)
        try:
            if self.game_type == GameType.wikiguesser:
                await wikiguesser_on_submit(self.info, interaction, user_input)
            elif self.game_type == GameType.wikianimal:
                await wikianimal_on_submit(self.info, interaction, user_input)
        except NotFound:
            logging.info("Its okay, no worries")


async def wikiguesser_on_submit(info: _Button, interaction: discord.Interaction, user_guess: str) -> None:
    """Guess the article.

    Args:
    ----
    info (_Button): Information about the button.
    interaction (discord.Interaction): The interaction object.
    user_guess (str): The user's guess.

    """
    await interaction.response.defer()
    page = await search_wikipedia(user_guess)
    try:
        if page.title() == info.article.title():
            await info.winlossmanager.on_win()
            await interaction.followup.send(
                "Good job", ephemeral=True
            )  # * IMPORTANT, you must respond to the interaction for the modal to close
            # * or else it will just say something went wrong
            return
    except InvalidTitleError:
        await interaction.followup.send(content="Sorry, the article title was not valid.")
    except AttributeError:
        await interaction.followup.send(
            content="Sorry, an error with that article occured, please try a different one."
        )
    await info.winlossmanager.on_loss()
    await interaction.followup.send(
        "bad job", ephemeral=True
    )  # * IMPORTANT, you must respond to the interaction for the modal to close
    # * or else it will just say something went wrong
    info.score[0] -= 5


async def wikianimal_on_submit(info: _Button, interaction: discord.Interaction, user_guess: str) -> None:
    """Handle the user's guess for the animal game.

    Args:
    ----
    info (_Button): Information about the button.
    interaction (discord.Interaction): The interaction object.
    user_guess (str): The user's guess.

    """
    print(info)
    print(interaction)
    print(user_guess)
    print("well you made it this far")


class LinkListButton(discord.ui.Button):
    """Button for showing more links from the list."""

    def __init__(self, *, info: _Button) -> None:
        """Initialize the LinkListButton class.

        Args:
        ----
        info (_Button): Information about the button.

        """
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
        self.score = info.score
        self.message = info.message
        self.links = info.links
        self.owners = info.owners
        self.private = info.private

    async def callback(self, interaction: discord.Interaction) -> None:
        """Show 10 diffrent links."""
        try:
            if interaction.user not in self.owners:
                await interaction.response.send_message("You may not interact with this", ephemeral=True)
                return

            if not self.links:
                self.view.remove_item(self)
                await interaction.message.edit(view=self.view)
                await interaction.response.send_message("No more links!", ephemeral=True)
                return

            selected_links = []
            self.score[0] -= 10
            for _ in range(10):
                selected_links.append(self.links.pop(secrets.randbelow(len(self.links))))
                if len(self.links) == 1:
                    selected_links.append(self.links.pop(0))
                    break

            logging.info("Private: %s", self.private)
            await interaction.response.send_message(
                content=f"{self.message}\n```{"\n".join(selected_links)}```",
                view=self.view,
                delete_after=180,
                ephemeral=self.private,
            )
            if not interaction.message.content:
                await interaction.message.delete()
                return
            await interaction.message.edit(view=None)
        except NotFound:
            logging.info("Its okay, no worries")
