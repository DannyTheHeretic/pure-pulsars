import logging
import os
import re

import aiohttp
import discord
from discord import NotFound, app_commands
from discord.app_commands.errors import CommandInvokeError
from pint import UnitRegistry

import button_class
from button_class import GameType, GiveUpButton, GuessButton, _Button
from wikiutils import UA, make_img_embed, search_wikipedia

UREG = UnitRegistry()

WEIGHT_PATTERN = re.compile(r"(\d+ ?(?:kg|tons|lbs|oz|g|pounds|grams))")


class IncompatibleAnimalError(Exception):
    """Error to be thrown if wikipedia animal and/or animal api fail to provide a valid weight range."""

    def __init__(self) -> None:
        super().__init__("No valid animal weights")


class WinLossFunctions(button_class.WinLossManagement):
    """The Basic Win Loss Function for WikiAnimal."""

    def __init__(self, winargs: dict, lossargs: dict) -> None:
        super().__init__(winargs, lossargs)

    async def on_win(self) -> None:
        """Clean up on win."""

    async def on_loss(self) -> None:
        """Clean up on loss."""


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
        api_url = "https://en.wikipedia.org/wiki/Special:RandomInCategory?wpcategory=Mammals of the United States"
        async with (
            aiohttp.ClientSession(headers={"UserAgent": UA}, timeout=aiohttp.ClientTimeout(total=20)) as session,
            session.get(api_url) as response,
        ):
            if response.ok:
                loc = str(response.real_url)
                title = loc.split("=")[1].split("&")[0]
        article = await search_wikipedia(title)
        animal_name = article.title().split(" ")[-1]
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

            guess_button = GuessButton(
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
                    view=hint_view,
                )
            )

            give_up_button = GiveUpButton(
                info=_Button(label="Give up", style=discord.ButtonStyle.danger, article=article),
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
        except CommandInvokeError as e:
            logging.info("Wiki-Animal:\nFunc: main\nException %s", e)
        except NotFound as e:
            logging.info("Wiki-Animal:\nFunc: main\nException %s", e)
