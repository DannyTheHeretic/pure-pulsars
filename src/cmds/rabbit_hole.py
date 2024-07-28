"""Logic for the rabbit hole command.

This command interacts with the Wikipedia API and the Google Gemini API to
curate a Wikipedia experience, getting lost down a "rabbit hole" of information.
"""

import json
import logging
import os
import random

import discord
import google.generativeai as genai
from discord import Embed, app_commands
from discord.app_commands.errors import CommandInvokeError
from discord.errors import NotFound
from google.api_core.exceptions import ResourceExhausted
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
    """Create an embed message for Wikipedia.

    Args:
    ----
    summary (dict): The summary of the Wikipedia article.

    Returns:
    -------
    discord.Embed: The embed message.

    """
    embed_msg = Embed(title=summary["Title"], description=summary["Intro"], url=summary["URL"], color=0xFFFFFF)
    for section, sentences in summary["Sections"].items():
        embed_msg.add_field(name=section, value="\n".join([f"- {sentence}" for sentence in sentences]), inline=False)
    embed_msg.set_image(url=summary["Image"])
    embed_msg.set_footer(text="To explore more Wikipedia topics, click one of the buttons below.")
    return embed_msg


class WikiButtons(discord.ui.View):
    """Buttons for exploring more Wikipedia articles."""

    def __init__(self, pages: list[Page]) -> None:
        """Initialize the WikiButtons class.

        Args:
        ----
        pages (list[Page]): The Wikipedia pages to explore.

        """
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
    """Functions to help the rabbit hole."""
    try:
        # Generate a summary and return an embed message
        text = article.extract(intro=False)
        response = model.generate_content(text)
        summary = json.loads(response.text)

        # Add additional information to the summary
        summary["Title"] = article.title()
        summary["URL"] = article.full_url()
        image_url = article.page_image()
        try:
            image_url = image_url.latest_file_info.url
        except AttributeError:
            image_url = None
        summary["Image"] = image_url

        # Create an embed message with the summary
        embed = make_embed(summary)

        # Get 3 random Wikipedia pages from the article
        related_pages = random.sample(tuple(article.linkedPages()), 3)

        await interaction.followup.send(embed=embed, view=WikiButtons(related_pages))
    except json.JSONDecodeError:
        logging.info("Failed to decode JSON response: %s", response.text)
        await interaction.followup.send("Failed to generate a summary. Please try again.")
    except ResourceExhausted:
        await interaction.followup.send("Your API key is rate limited. Please try again later.")
    except NotFound as e:
        logging.info("Rabbit Hole:\nFunc: rabbit_hole_helper\nException %s", e)
    except CommandInvokeError as e:
        logging.info("Rabbit Hole:\nFunc: rabbit_hole_helper\nException %s", e)


def main(tree: app_commands.CommandTree) -> None:
    """Command to create a Wiki rabbit hole."""

    @tree.command(
        name="rabbit-hole",
        description="Dive into wiki-knowledge with Rabbit Hole — information overload through random exploration.",
    )
    async def rabbit_hole(interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)

        try:
            # Get a random Wikipedia article
            article = await rand_wiki()
        except NotFound as e:
            logging.info("Rabbit Hole:\nFunc: rabbit_hole\nException %s", e)
        except CommandInvokeError as e:
            logging.info("Rabbit Hole:\nFunc: rabbit_hole\nException %s", e)

        # Generate a summary, and return an embed message
        await rabbit_hole_helper(interaction, article)
