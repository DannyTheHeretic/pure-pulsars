"""Challenge command for the Wiki Guesser game.

This command allows users to challenge other users to a game of Wiki Guesser.


CODE JAM NOTE:
-------------
It has not been implemented yet, and may not be implemented by the end of the
game jam. The code is here for future reference.
"""

import asyncio

import discord
from discord import app_commands


def main(tree: app_commands.CommandTree) -> None:
    """Command to challenge people to a game of wiki-guesser."""

    @tree.command(name="challenge", description="Challenge someone to a game of wikiguesser!")
    async def challenge(interaction: discord.Interaction, user: discord.User, points_to_win: int) -> None:
        """Create Wiki Guesser command.

        Args:
        ----
        interaction (discord.Interaction): The interaction object.
        user (discord.User): The user to challenge.
        points_to_win (int): The number of points required to win.


        Note:
        ----
        This command will create a private thread between the two users, and the game will begin
        in 10 seconds. The game will be played in the thread, and the thread will be deleted after
        the game ends.

        Warning:
        -------
        This command is not yet implemented.

        """
        if interaction.channel.type in [discord.ChannelType.public_thread, discord.ChannelType.private_thread]:
            await interaction.response.send_message(
                "You silly billy! This command won't work in a thread", ephemeral=True
            )
            return
        thread = await interaction.channel.create_thread(
            name=f"Wikiguesser between {user.name} and {interaction.user.name}",
            type=discord.ChannelType.private_thread,
        )
        await interaction.response.send_message("Join the newly created thread to play, GAME BEGINS IN 10")
        await thread.add_user(user)
        await thread.add_user(interaction.user)
        await countdown(interaction=interaction)
        await thread.send(points_to_win)
        await thread.delete()

    async def countdown(interaction: discord.Interaction) -> None:
        """Countdown to the start of the game."""
        for i in range(9, -1, -1):
            await interaction.edit_original_response(
                content=f"Join the newly created thread to play, GAME BEGINS IN {i}"
            )
            await asyncio.sleep(1)
