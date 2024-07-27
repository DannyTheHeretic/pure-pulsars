import logging

import discord
from discord import app_commands
from pint import UnitRegistry
from pywikibot import Page

from cmds import wikiguesser_class
from cmds.wikiguesser_class import GameType, _Button, _Comp
from wikiutils import make_embed, make_img_embed, rand_wiki

ureg = UnitRegistry()


class WinLossFunctions(wikiguesser_class.WinLossManagement):
    """The Basic Win Loss Function for WikiAnimal."""

    def __init__(self, winargs: dict, lossargs: dict) -> None:
        super().__init__(winargs, lossargs)

    async def _on_win(self) -> None:
        interaction: discord.Interaction = self.winargs["interaction"]
        article = self.winargs["article"]
        embed = make_embed(article)
        msg = f"Congratulations {interaction.user.mention}! You guessed correctly!"
        await interaction.followup.send(content=msg, embed=embed)

    async def _on_loss(self) -> None:
        interaction: discord.Interaction = self.lossargs["interaction"]
        await interaction.followup.send("Guess higher or lower.", ephemeral=True)


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


def find_animal_weight(article: Page) -> tuple[str, ...]:
    """Determine animal's weight ranges based on article text"""
    # TODO(Gobleizer): scrape article for weight data
    print("find animal weight")
    return ("1lb", "3lb", "20 kg", "40 kilos")


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
            await interaction.response.send_message(content="Starting a game of Wiki Animal")

            # * I was encoutering an warning that happened sometimes that said 'rand_wiki' was never awaited but
            # * when I ran the command again it didn't appear, so I'm just running this twice if it doesn't work the
            # * first time
            try:
                article = await rand_wiki()
            except AttributeError as e:
                logging.critical("Wierd error occured %s", e)
                article = await rand_wiki()
            logging.info("The current wikiguesser title is %s", article.title())

            weight_ranges = find_animal_weight(article)

            hint_view = discord.ui.View()

            animal_name = article.title()

            args = {"interaction": interaction, "ranked": ranked, "article": article, "scores": score}

            guess_button = wikiguesser_class.GuessButton(
                info=_Button(label="Guess!", style=discord.ButtonStyle.success),
                comp=_Comp(
                    ranked=ranked,
                    article=article,
                    score=score,
                    user=interaction.user.id,
                    game_type=GameType.wikianimal,
                ),
                owners=owners,
                winlossmanager=WinLossFunctions(args, args),
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
