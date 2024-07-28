import json
import logging
import os
import random

import discord
import google.generativeai as genai
from discord import Embed, app_commands
from pywikibot import Page

from wikiutils import rand_wiki

sys_ins = """Objective: Summarize a Wikipedia article in a concise and informative manner, retaining key details and ensuring readability. Do not return any commentary or anything else, except the requested summary.

Instructions:
- Intro: Write a brief summary of the article's intro. This should provide an overview of the most important points in 2-3 sentences.
- Sections: Identify and summarize the main sections of the article. Each section should have its own heading and a 1-2 sentence summary. Include 4-6 sections that cover the most significant aspects of the topic.
- Categories: Provide adjacent categories for further exploration. This should include 3 categories and their respective Wikipedia URLs that are relevant to the topic (but not about the topic itself).

Output the summary in the following JSON format:
{
    "Intro": "Brief summary of the article's intro.",
    "Sections": {
        "Section Name": ["Sentence 1", "Sentence 2"],
        "Section Name": ["Sentence 1", "Sentence 2"],
    },
    "Categories": [
        {"Name": "Category 1", "URL": "Wikipedia URL"},
        {"Name": "Category 2", "URL": "Wikipedia URL"},
        {"Name": "Category 3", "URL": "Wikipedia URL"},
    ],
}

Do not format the message with ```json```, as it is not neccessary. Return the JSON object as a string.
"""

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=sys_ins)


def make_embed(summary: dict) -> Embed:
    """Create an embed message for Wikipedia."""
    embed_msg = Embed(title=summary["Title"], description=summary["Intro"], url=summary["URL"], color=0xFFFFFF)
    for section, sentences in summary["Sections"].items():
        embed_msg.add_field(name=section, value="\n".join([f"- {sentence}" for sentence in sentences]), inline=False)
    embed_msg.set_image(url=summary["Image"])
    embed_msg.set_footer(text="To explore more Wikipedia topics, click one of the buttons below.")
    return embed_msg


class WikiButtons(discord.ui.View):
    """Buttons for exploring more Wikipedia articles."""

    def __init__(self, pages: list[Page]) -> None:
        super().__init__(timeout=None)
        self.pages = pages
        self.create_buttons()

    def create_buttons(self) -> None:
        """Create buttons for each Wikipedia article."""

        def create_callback(page: Page) -> discord.ui.Button.callback:
            async def button_callback(interaction: discord.Interaction) -> None:
                await interaction.response.defer(thinking=True, ephemeral=True)
                await rabbit_hole_helper(interaction, page)

            return button_callback

        for page in self.pages:
            button = discord.ui.Button(label=page.title(), style=discord.ButtonStyle.green)
            button.callback = create_callback(page)
            self.add_item(button)


async def rabbit_hole_helper(interaction: discord.Interaction, article: Page) -> None:
    """Helper function for the rabbit hole command."""  # noqa: D401
    try:
        # Generate a summary and return an embed message
        text = article.extract(intro=False)
        response = model.generate_content(text)
        try:
            summary = json.loads(response.text)
        except json.JSONDecodeError:
            logging.critical("Failed to decode JSON response: %s", response.text)
            await interaction.followup.send("Failed to generate a summary. Please try again.")
            return

        # Add additional information to the summary
        summary["Title"] = article.title()
        summary["URL"] = article.full_url()
        image_url = article.page_image()
        try:
            image_url = image_url.latest_file_info.url
        except AttributeError:
            try:
                image_url = image_url.oldest_file_info.url
            except AttributeError:
                image_url = "https://wikimedia.org/static/images/project-logos/enwiki-2x.png"
        summary["Image"] = image_url

        # Create an embed message with the summary
        embed = make_embed(summary)

        # Get 3 random Wikipedia pages from the article
        related_pages = random.sample(tuple(article.linkedPages()), 3)

        await interaction.followup.send(embed=embed, view=WikiButtons(related_pages))
    except discord.app_commands.errors.CommandInvokeError as e:
        logging.critical("Exception %s", e)


def main(tree: app_commands.CommandTree) -> None:
    """Command to create a Wiki rabbit hole."""

    @tree.command(
        name="rabbit-hole",
        description="Dive into wiki-knowledge with Rabbit Hole — information overload through random exploration.",
    )
    async def rabbit_hole(interaction: discord.Interaction) -> None:
        try:
            await interaction.response.defer(thinking=True, ephemeral=True)

            # Get a random Wikipedia article, generate a summary, and return an embed message
            article = await rand_wiki()
            await rabbit_hole_helper(interaction, article)
        except discord.app_commands.errors.CommandInvokeError as e:
            logging.critical("Exception %s", e)
