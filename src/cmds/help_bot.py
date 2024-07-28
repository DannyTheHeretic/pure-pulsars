"""Help command for the bot."""

import discord
from discord import app_commands


def main(tree: app_commands.CommandTree) -> None:
    """Create a help command."""

    @tree.command(
        name="help",
        description="Responds with help",
    )
    async def help_me(interaction: discord.Interaction) -> None:
        """Display help text from commands available in the bot comamnd tree."""
        resp = "```"
        for i in tree.get_commands():
            resp += f"{i.name} : {i.description}\n"
        resp += "```"
        await interaction.response.send_message(content=resp, ephemeral=True)
