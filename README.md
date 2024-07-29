<!-- Banner -->
<figure style="margin: auto; max-height: 200px; padding: 10px 5px 20px 5px;">
   <picture>
      <source media="(prefers-color-scheme: dark)" srcset="docs/assets/Logo/banner_1_no_background_dark_mode.png">
      <img src="docs/assets/Logo/banner_1_no_background.png" align="center">
   </picture>
</figure>

<br>

`Wiki-Wabbit` is a discord bot that brings the fun of bingeing Wikipedia articles to your dicord server!

# Directory

+ [Features](#Features)
+ [Technical Points](#Technical-Points)
+ [Install Guide](#Install-Guide)
  + [Discord Token](#Discord-Token)
  + [Firebase Service Account](#Firebase-Service-Account)
  + [Gemma API Key](#Gemma-API-Key)
  + [API Ninjas API Key](#API-Ninjas-Key)
  + [Env Settings](#Env-Settings)
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

+ Firebase
+ Google's Gemini API
+ Ninja API

# Install Guide

We require a few resources to get our bot up and running.
The first thing we need is a discord api token.

### Discord Token
<!-- Install guide. -->
[Goto the Discord Application Page](https://discord.com/developers/applications) you should see this screen.
<figure style="margin: auto; max-height: 200px; padding: 10px 5px 20px 5px;">
   <picture>
      <img src="docs/assets/discord_application_page.png" align="center">
   </picture>
</figure>

After that go and create a discord application by clicking the `New Application` button

Now go down to bot and click `Reset Token` that will be your discord token, put it somewhere safe for later.
While here be sure to turn on the 3 switches below `Privileged Gateway Intents`
 + Presence Intent
 + Server Members Intent
 + Message Content Intent

You should also goto `Installation` and goto the Install Link, add your bot to your discord server with this.

### Firebase Service Account

[Go to the Firebase Console](https://console.firebase.google.com/) and click the get started with a Firebase project
Its name can be anything, so dont worry about that.
But after its made, click on the build tab on the left hand of the screen and scroll down to `Realtime Database`, this will be our database for the bot.
<figure style="margin: auto; max-height: 200px; padding: 10px 5px 20px 5px;">
   <picture>
      <img src="docs/assets/realtime_create.png" align="center">
   </picture>
</figure>

After this we still need how to tell the bot what firebase account we are.
So head to project settings, it should pop up if you click on the gear near `Project Overview`.
From there navigate to `Service Accounts` and click `Generate a New Private Key`. Put that in a safe place that you can get to easily.
And thats all for Firebase.

### Gemini API Key
One of our Commands makes use of AI, and since we don't want to force the end user to run a complex AI model, we are using the Google Gemma free plan.

[Goto the Google AI Studio](https://aistudio.google.com/app/apikey) and just click `Create API key`.
Once you have your key, you can store that somewhere safe for later.
Well that was easy.

### API Ninjas Key
[Goto API Ninjas](https://api-ninjas.com/api/animals) and create an account. After you make it, [goto your profile](https://api-ninjas.com/profile).
From here scroll down a bit and click `Show API Key`, copy it, and write it down somewhere for later.

Now that we have all of our keys and service accounts. Its time to configure the bot

### Env Settings.
We have included a [config.env](config.env) to allow you to easily have everything set up.
TOKEN is your discord api token
CERT_PATH is your Firebase Service Account file path.
GEMINI_API_KEY is your gemma api key.
NINJA_API_KEY is your API Ninjas api key.

after you set these, be sure rename config.env to just .env so the docker knows what to use.

