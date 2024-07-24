import logging
import secrets

import discord
from discord import Enum, app_commands
from discord.utils import MISSING
from pywikibot import Page

from cmds import wikiguesser_class
from cmds.wikiguesser_class import _Button, _Comp
from wikiutils import is_article_title, make_embed, rand_wiki, search_wikipedia, update_user

ACCURACY_THRESHOLD = 0.8
MAX_LEN = 1990


class _Ranked(Enum):
    YES = 1
    NO = 0


class WinLossFunctions(wikiguesser_class.WinLossManagement):
    """The Basic Win Loss Function."""

    def __init__(self, winargs: dict, lossargs: dict) -> None:
        super().__init__(winargs, lossargs)

    async def _on_win(self) -> None:
        interaction: discord.Interaction = self.winargs["interaction"]
        ranked: bool = self.winargs["ranked"]
        scores: list[int] = self.winargs["scores"]
        article = self.winargs["article"]
        embed = make_embed(article)
        # TODO: For Some Reason this doesnt work, it got mad
        msg = f"Congratulations {interaction.user.mention}! You figured it out, your score was {scores[0]}!"
        await interaction.followup.send(content=msg, embed=embed)
        if ranked:
            user = interaction.user
            for i in [interaction.guild_id, 0]:
                await update_user(i, user, scores[0])

    async def _on_loss(self) -> None:
        interaction: discord.Interaction = self.lossargs["interaction"]
        await interaction.followup.send("That's incorrect, please try again.", ephemeral=True)


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
        self.score[0] -= (len("".join(self.summary[: self.ind])) - len("".join(self.summary[: self.ind - 1]))) // 2

        if self.summary[: self.ind] == self.summary or len(".".join(self.summary[: self.ind + 1])) > MAX_LEN:
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
        self.user = comp.user

    async def callback(self, interaction: discord.Interaction) -> None:
        """Open guess modal."""
        guess_modal = GuessInput(
            title="Guess!", comp=_Comp(ranked=self.ranked, article=self.article, score=self.score, user=self.user)
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
        self.user = comp.user
        self.article = comp.article

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Guess the article."""
        if self.ranked and interaction.user.id != self.user:
            await interaction.response.send_message(
                "You cannot guess because you were not the on who started this ranked game of wiki-guesser.",
                ephemeral=True,
            )
            return

        page = await search_wikipedia(self.children[0].value)
        if page.title() == self.article.title():
            embed = make_embed(self.article)
            # TODO: For Some Reason this doesnt work, it got mad
            msg = f"Congratulations {interaction.user.mention}! You figured it out, your score was {self.score[0]}!"
            await interaction.response.send_message(content=msg, embed=embed)
            if self.ranked:
                user = interaction.user
                for i in [interaction.guild_id, 0]:
                    await update_user(i, user, self.score[0])
            await interaction.message.edit(view=None)
            return
        await interaction.response.send_message("That's incorrect, please try again.", ephemeral=True)
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
            selected_links.append(self.links.pop(secrets.randbelow(len(self.links) - 1)))
            if len(self.links) == 1:
                selected_links.append(self.links.pop(0))
                break
        await interaction.response.send_message(
            content=f"{self.message}\n```{"\n".join(selected_links)}```",
            view=self.view,
            delete_after=180,
        )
        if len(self.links) == 0:
            self.view.remove_item(self)


def main(tree: app_commands.CommandTree) -> None:
    """Create Wiki Guesser command."""

    @tree.command(
        name="wiki-guesser",
        description="Starts a game of wiki-guesser! Try and find what wikipedia article your in.",
    )
    async def wiki(interaction: discord.Interaction, ranked: _Ranked = _Ranked.NO) -> None:
        try:
            ranked: bool = bool(ranked.value)
            owners = [interaction.user] if ranked else [*interaction.guild.members]
            score = [1000]
            if ranked:
                await interaction.response.send_message(
                    content=f"Starting a game of **Ranked** Wikiguesser for {owners[0].mention}"
                )
            else:
                await interaction.response.send_message(content="Starting a game of Wikiguesser")

            # * I was encoutering an warning that happened sometimes that said 'rand_wiki' was never awaited but
            # * when I ran the command again it didn't appear, so I'm just running this twice if it doesn't work the
            # * first time
            try:
                article = await rand_wiki()
            except AttributeError as e:
                logging.criticle("Wierd error occured %s", e)
                article = await rand_wiki()
            logging.info("The current wikiguesser title is %s", article.title())

            links = [link.title() for link in article.linkedPages(total=50) if is_article_title(link.title())]

            excerpt = article.extract(chars=1200)

            for i in article.title().split():
                excerpt = excerpt.replace(i, "~~CENSORED~~")
                excerpt = excerpt.replace(i.lower(), "~~CENSORED~~")

            sentances = excerpt.split(". ")
            args = {"interaction": interaction, "ranked": ranked, "article": article, "scores": score}
            excerpt_view = discord.ui.View()
            guess_button = wikiguesser_class.GuessButton(
                info=wikiguesser_class.Button(label="Guess!", style=discord.ButtonStyle.success),
                comp=wikiguesser_class.Comp(ranked=ranked, article=article, score=score, user=interaction.user.id),
                owners=owners,
                winlossmanager=WinLossFunctions(args, args),
            )
            excerpt_button = wikiguesser_class.ExcerptButton(
                info=wikiguesser_class.Button(label="Show more", style=discord.ButtonStyle.primary),
                summary=sentances,
                score=score,
                owners=owners,
                private=ranked,
            )

            give_up_button = GiveUpButton(
                info=_Button(label="Give up", style=discord.ButtonStyle.danger),
                article=article,
                view=excerpt_view,
            )

            excerpt_view.add_item(excerpt_button)
            excerpt_view.add_item(guess_button)
            if ranked:
                await interaction.followup.send(f"# RANKED WIKIGUESSER FOR {owners[0].mention}", ephemeral=True)

            excerpt_view.add_item(give_up_button)

            await interaction.followup.send(
                content=f"__**Excerpt**__: {sentances[0]}.", view=excerpt_view, wait=True, ephemeral=ranked
            )

            view = discord.ui.View()
            link_button = wikiguesser_class.LinkListButton(
                info=wikiguesser_class.Button(
                    label="Show more links in article",
                ),
                comp=wikiguesser_class.Comp(score=score),
                links=links,
                message="Links in article:",
                owners=owners,
                private=ranked,
            )

            view.add_item(link_button)

            await interaction.followup.send(view=view, wait=True, ephemeral=ranked)
            await interaction.delete_original_response()
        except discord.app_commands.errors.CommandInvokeError as e:
            logging.critical("Exception %s", e)
