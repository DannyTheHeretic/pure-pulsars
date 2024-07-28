import asyncio

import discord
from discord import app_commands

from wikiutils import make_embed, search_wikipedia


def main(tree: app_commands.CommandTree) -> None:
    """Create a wikiguesser command."""

    @tree.command(
        name="never",
        description="Who knows what this does.",
    )
    async def never_gonna_give_you_up(interaction: discord.Interaction, user: discord.User) -> None:
        await interaction.response.send_message(
            f"Starting deathmatch between {user.mention} and {interaction.user.mention}..."
        )
        article = await search_wikipedia("Rickrolling")
        await asyncio.sleep(1)
        embed = make_embed(article)
        embed.description = (
            f"{article.extract(chars=400)}...([read more](https://www.youtube.com/watch?v=dQw4w9WgXcQ))"
        )
        embed.set_image(url="https://upload.wikimedia.org/wikipedia/en/f/f7/RickRoll.png")
        await interaction.followup.send(embed=embed)
