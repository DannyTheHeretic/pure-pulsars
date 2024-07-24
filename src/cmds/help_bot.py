import discord
from discord import app_commands


def main(tree: app_commands.CommandTree) -> None:
    """Create a wikiguesser command."""

    @tree.command(
        name="help",
        description="Responds with Help",
    )
    async def help_me(interaction: discord.Interaction) -> None:
        resp = "```"
        for i in tree.get_commands():
            resp += f"{i.name} : {i.description}\n"
        resp += "```"
        await interaction.response.send_message(content=resp, ephemeral=True)
