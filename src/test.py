import wikipediaapi

t = wikipediaapi.Wikipedia(user_agent="CoolBot/0.0 (https://example.org/coolbot/) generic-library/0.0")
w = wikipediaapi.WikipediaPage(wiki=t, title="")
if w:
    print(w.backlinks)
