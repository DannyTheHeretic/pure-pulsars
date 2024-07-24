import logging

import discord
from discord import app_commands

from cmds import wikiguesser_class
from cmds.wikiguesser_class import _Button, _Comp, _Ranked
from wikiutils import is_article_title, make_embed, rand_wiki, update_user

ACCURACY_THRESHOLD = 0.8
MAX_LEN = 1990


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


def main(tree: app_commands.CommandTree) -> None:
    """Create Wiki Guesser command."""

    @tree.command(
        name="wiki-guesser",
        description="Starts a game of wiki-guesser! Try and find what wikipedia article your in.",
    )
    @app_commands.describe(ranked = "Do you want to play ranked?")
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
                logging.critical("Wierd error occured %s", e)
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
                info=_Button(label="Guess!", style=discord.ButtonStyle.success),
                comp=_Comp(ranked=ranked, article=article, score=score, user=interaction.user.id),
                owners=owners,
                winlossmanager=WinLossFunctions(args, args),
            )
            excerpt_button = wikiguesser_class.ExcerptButton(
                info=_Button(label="Show more", style=discord.ButtonStyle.primary),
                summary=sentances,
                score=score,
                owners=owners,
                private=ranked,
            )

            give_up_button = wikiguesser_class.GiveUpButton(
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
                info=_Button(
                    label="Show more links in article",
                    links=links,
                    message="Links in article:",
                    owners=owners,
                    private=ranked,
                ),
                comp=_Comp(score=score),
            )

            view.add_item(link_button)

            await interaction.followup.send(view=view, wait=True, ephemeral=ranked)
            await interaction.delete_original_response()
        except discord.app_commands.errors.CommandInvokeError as e:
            logging.critical("Exception %s", e)
