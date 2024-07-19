import discord
from discord import app_commands

from wikiutils import make_embed, rand_wiki


def main(tree: app_commands.CommandTree) -> None:
    """Create Wiki Guesser command."""

    @tree.command(
        name="wiki-random",
        description="its the command thingy",
        guild=discord.Object(id=1262497899925995563),
    )
    async def wiki(interaction: discord.Interaction) -> None:
        await interaction.response.send_message(content="hello, we are processing ur request")
        article = rand_wiki()
        embed = make_embed(article=article)
        await interaction.followup.send(embed=embed)
        await interaction.delete_original_response()
