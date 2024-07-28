<!-- Banner -->
<figure style="margin: auto; max-height: 200px; padding: 10px 5px 20px 5px;">
   <picture>
      <source media="(prefers-color-scheme: dark)" srcset="docs/assets/banner_1_no_background_dark_mode.png">
      <img src="docs/assets/banner_1_no_background.png" align="center">
   </picture>
</figure>

<br>
`Wiki-Wabbit` is a discord bot that brings the fun of bingeing Wikipedia articles to your dicord server!

# Features

| Command         | Description                                                                |
|-----------------|----------------------------------------------------------------------------|
| `/wiki-guesser` | Starts a game of wiki-guesser! Try and find what wikipedia article you're in. |
| `/wiki-random`  | Get a random wikipedia article.                                            |
| `/wiki-animal`  | Starts a game of wiki-animal! Try and guess the animal's mass!             |
| `/rabbit-hole`  | Dive into wikipedia with AI-guided random exploration!                     |
| `/wiki-search`  | Get a Wikipedia article that you searched for.                             |
| `/leaderboard`  | Returns your guild's leaderboard.                                          |
| `/user-info`    | Returns your stats.                                                        |
| `/reset-scores` | Reset scores of all users in this guild for this guild.                    |
| `/never`        | Never use this command! :surprised:                                        |
| `/sync`         | Sync the command tree.                                                     |
| `/help`         | Display a message with much of the same info as this table has.            |


# Technical Points

<!-- Any interesting technical points you'd like to include go below here. -->

`Wiki-Wabbit` uses `pywikibot` and the Wikipedia REST API. Alongside that, it also makes use of:

+ Google's Gemini API
+ Firebase
