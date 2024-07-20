# `[Wikipedia geoguesser thing WIP]`

# Features

+ (✔️) Guess based on a short censored exerpt the topic of a wikipedia article.
   + Can show related articles, show more links within the article?
+ (✔️) Get random featured page from the last 8 years.
+ (⌨️)Rabbit hole stuff
+ (⌨️) Database w/ global & server-wide leaderboards
+ Pop quizzes(?)

# TODO

- [X] Broad project details
   - [X] Name?
      - [X] `WikiWabbit`
      - [ ] `rabbit hole 🐇`
      - [ ] Wikiguesser
   - [X] Logo/icon?
      - [X] The One Pinned In General
- [ ] Plan for project
   - [ ] What are the core backend components/interactions we want a user to have?
      - [ ] What of these are handled entirely by `discord.py`?
      - [ ] Which require logic on our end?
      - [x] What dependencies can fill in the gaps/make our live easier?
         - [x] Wikipedia API library
         - [x] firebase.io (scores/etc)
         - [x] `python-dotenv` (for secrets)
   - [ ] What is the average "experience"
      - [ ] i.e., from wanting to start a session with the bot to finishing the
            session, what does each step look like, ideally?
      - [ ] What non-code components might enhance the expecience? (e.g.,
            images, graphics)
      - [ ] Are there any important special cases?
         - [x] Help & app info
- [ ] Coding/etc.
   - [ ] Do we want to review each other's code?
      - [ ] Do we want to lock the main branch at some point so it's ~stable?
            If so, when?
   - [ ] Would anyone prefer to pair-program (i.e., code together with another
         person through VSCode or the github vscode thing)?
   - [ ] Are we good with the linting rules in the template? Do we want
         anything else?
- [ ] Database
   - [ ] What interactions should admins have with server stats (Should we make commands?)
     - [ ] Remove user score
     - [ ] Reset scores
