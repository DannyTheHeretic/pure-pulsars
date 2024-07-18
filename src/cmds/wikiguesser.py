import discord
from discord import app_commands

from wikiutils import is_text_link, rand_wiki


def main(tree:app_commands.CommandTree)->None:
    """Create Wiki Guesser command."""

    @tree.command(name="wiki-guesser", description="its the command thingy",
                  guild=discord.Object(id=1262497899925995563))
    async def wiki(interaction: discord.Interaction) -> None:
        await interaction.response.send_message(content="hello, we are processing ur request")

        article = rand_wiki()

        if not article:
            await interaction.followup.send(content="An error occured")
            return


        backlinks = [link for link in article.backlinks if is_text_link(link)]
        backlinks.reverse()
        await interaction.followup.send(content=f"```{'\n'.join(backlinks)[:1990]}```")
