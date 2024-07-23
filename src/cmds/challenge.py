import asyncio

import discord
from discord import app_commands

import cmds.wikiguesser


def main(tree: app_commands.CommandTree):
    @tree.command(
        name="challenge",
        description="Challenge someone to a game of wikiguesser!"
    )
    async def challenge(interaction: discord.Interaction, user: discord.User, points_to_win: int):
        """Create Wiki Guesser command."""
        if interaction.channel.type in [discord.ChannelType.public_thread, discord.ChannelType.private_thread]:
            await interaction.response.send_message("You silly billy! This command won't work in a thread", ephemeral=True)
            return
        thread = await interaction.channel.create_thread(name=f"Wikiguesser between {user.name} and {interaction.user.name}", type=discord.ChannelType.private_thread)
        await interaction.response.send_message("Join the newly created thread to play, GAME BEGINS IN 10")
        await thread.add_user(user)
        await thread.add_user(interaction.user)
        await countdown(interaction=interaction)
        await thread.send("YOOOOOOOOOOOOOOOO")
        # CODE GOES HERE

        await thread.delete()
    async def countdown(interaction: discord.Interaction) -> None:
        for i in range(9, -1, -1):
            await interaction.edit_original_response(content=f"Join the newly created thread to play, GAME BEGINS IN {i}")
            await asyncio.sleep(1)
