import discord
from discord import app_commands
from cmds.wikiguesser import *



def main(tree: app_commands.CommandTree):
    @tree.command(
        name="challenge",
        description="Challenge someone to a game of wikiguesser!"
    )
    async def challenge(interaction: discord.Interaction, user: discord.User, points_to_win: int):
        """Create Wiki Guesser command."""
        try:
            ranked: bool = bool(ranked.value)
            score = [1000]

            await interaction.response.send_message(content="Hello, we are processing your request...")
            article = await rand_wiki()
            print(article.title())

            links = [link.title() for link in article.linkedPages() if is_article_title(link.title())]

            excerpt = article.extract(chars=1200)

            for i in article.title().split():
                excerpt = excerpt.replace(i, "~~CENSORED~~")
                excerpt = excerpt.replace(i.lower(), "~~CENSORED~~")

            sentances = excerpt.split(". ")

            excerpt_view = discord.ui.View()
            guess_button = GuessButton(
                info=Button(label="Guess!", style=discord.ButtonStyle.success),
                comp=Comp(ranked=ranked, article=article, score=score, user=interaction.user.id),
            )
            excerpt_button = ExcerptButton(
                info=Button(label="Show more", style=discord.ButtonStyle.primary), summary=sentances, score=score
            )

            excerpt_view.add_item(excerpt_button)
            excerpt_view.add_item(guess_button)

            await interaction.followup.send(
                content=f"Excerpt: {sentances[0]}.",
                view=excerpt_view,
                wait=True,
            )

            view = discord.ui.View()
            link_button = LinkListButton(
                info=Button(
                    label="Show more links in article",
                ),
                comp=Comp(score=score),
                links=links,
                message="Links in article:",
            )

            view.add_item(link_button)

            await interaction.followup.send(view=view, wait=True)
            await interaction.delete_original_response()
        except discord.app_commands.errors.CommandInvokeError as e:
            print(e)