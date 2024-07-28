import logging
import os
import re

import aiohttp
import discord
from discord import app_commands
from pint import UnitRegistry
from pywikibot import Page

from cmds import wikiguesser_class
from cmds.wikiguesser_class import GameType, _Button
from wikiutils import get_articles_with_categories, make_embed, make_img_embed

UREG = UnitRegistry()

WEIGHT_PATTERN = re.compile(r"(\d+ ?(?:kg|tons|lbs|oz|g|pounds|grams))")


class IncompatibleAnimalError(Exception):
    """Error to be thrown if wikipedia animal and/or animal api fail to provide a valid weight range."""

    def __init__(self) -> None:
        super().__init__("No valid animal weights")


class WinLossFunctions(wikiguesser_class.WinLossManagement):
    """The Basic Win Loss Function for WikiAnimal."""

    def __init__(self, winargs: dict, lossargs: dict) -> None:
        super().__init__(winargs, lossargs)

    async def on_win(self) -> None:
        """Clean up on win."""
        interaction: discord.Interaction = self.winargs["interaction"]
        article = self.winargs["article"]
        embed = make_embed(article)
        msg = f"Congratulations {interaction.user.mention}! You guessed correctly!"
        await interaction.followup.send(content=msg, embed=embed)

    async def on_loss(self) -> None:
        """Clean up on loss."""
        interaction: discord.Interaction = self.lossargs["interaction"]
        await interaction.followup.send("Sorry, try again.", ephemeral=True)


class GiveUpButton(discord.ui.Button):
    """Button for exiting/"giving up" on game."""

    # TODO(Gobleizer): Switch to a wikiguesser_class version of GiveUpButton
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


async def find_animal_weight(animal_name: str) -> list[str]:
    """Determine animal's weight ranges based on article text."""
    api_url = f"https://api.api-ninjas.com/v1/animals?name={animal_name}"
    async with (
        aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session,
        session.get(api_url, headers={"X-Api-Key": os.environ["NINJA_API_KEY"]}) as response,
    ):
        if not response.ok:
            logging.error("Error requesting animal data: %s", response.status)
            raise IncompatibleAnimalError
        animal_data = await response.json()
    if animal_data:
        weight_str = animal_data[0].get("characteristics").get("weight")
    else:
        raise IncompatibleAnimalError
    if weight_str is None:
        raise IncompatibleAnimalError
    weight_str = weight_str.replace(",", "")
    weight_phrases = re.findall(WEIGHT_PATTERN, weight_str)
    if weight_phrases:
        weight_ranges = [UREG.Quantity(weight) for weight in weight_phrases]
        if len(weight_ranges) % 2 == 0:
            return [weight_ranges[0], weight_ranges[1]]
        return [weight_ranges[0]]
    raise IncompatibleAnimalError


async def find_new_animal(interaction: discord.Interaction) -> dict:
    """Return random animal's information."""
    try:
        articles = await get_articles_with_categories(["Mammals of the United States"], 1)
        await interaction.followup.send("Still chasing animals...")
        article = articles[0]
        animal_name = article.title().split(" ")[-1]
        logging.info("The current wikianimal is %s", animal_name)
        weight_ranges = await find_animal_weight(animal_name)
    except IncompatibleAnimalError:
        return await find_new_animal(interaction)
    return {"name": animal_name, "article": article, "weight_ranges": weight_ranges}


def main(tree: app_commands.CommandTree) -> None:
    """Create Wiki Animal command."""

    @tree.command(
        name="wiki-animal",
        description="Starts a game of wiki-animal! Try and guess the animal's mass!",
    )
    async def wiki(interaction: discord.Interaction) -> None:
        logging.info("Catching animal, wikipedia is slow, please standby.")
        try:
            ranked = False
            owners = [*interaction.guild.members]
            score = [1000]
            await interaction.response.send_message(
                content="Starting a game of Wiki Animal, one moment while we catch your animal."
            )

            animal_info = await find_new_animal(interaction)

            article = animal_info.get("article")
            hint_view = discord.ui.View()

            animal_name = animal_info.get("name")

            args = {"interaction": interaction, "ranked": ranked, "article": article, "scores": score}

            guess_button = wikiguesser_class.GuessButton(
                info=_Button(
                    label="Guess!",
                    style=discord.ButtonStyle.success,
                    article=article,
                    score=score,
                    user=interaction.user.id,
                    game_type=GameType.wikianimal,
                    owners=owners,
                    winlossmanager=WinLossFunctions(args, args),
                    animal_info=animal_info,
                )
            )

            give_up_button = GiveUpButton(
                info=_Button(label="Give up", style=discord.ButtonStyle.danger),
                article=article,
                view=hint_view,
            )

            hint_view.add_item(guess_button)

            hint_view.add_item(give_up_button)

            img_embed = make_img_embed(
                article=article, error_message="Sorry this animal's image is missing. Good Luck!"
            )

            await interaction.followup.send(
                content=f"Guess the {animal_name}'s weight.",
                view=hint_view,
                wait=True,
                embed=img_embed,
                ephemeral=ranked,
            )

            await interaction.delete_original_response()
        except discord.app_commands.errors.CommandInvokeError as e:
            logging.critical("Exception %s", e)
