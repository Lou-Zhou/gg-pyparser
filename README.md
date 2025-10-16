# gg-pyparser
<!-- badges: start -->
![PyPI - Version](https://img.shields.io/pypi/v/gg-pyparser?style=for-the-badge)
[![License](https://img.shields.io/github/license/Lou-Zhou/gg-pyscraper?style=for-the-badge)](https://github.com/Lou-Zhou/gg-pyscraper/blob/main/LICENSE)
[![Python Version](https://img.shields.io/badge/python-%3E%3D3.8-blue?style=for-the-badge)](...)

<!-- badges: end -->

`gg-pyparser` is a Python package designed to query and scrape esports data from [liquipedia.net](https://liquipedia.net). With Liquipedia’s standardized formatting and multitude of supported esports, this package can parse data for more than 55 different video games. 

## Installation

We can use [pip](https://pip.pypa.io/en/stable/) to install gg-pyparser.

```bash
pip install gg-pyparser
```

## Usage

### Liquipedia Pages
There are three different types of liquipedia pages that we can parse: **tournaments, teams, and players**. To parse any of these objects, the following page details are required:

**game** – the video game title the page belongs to, we can find the needed string from `https://liquipedia.net/{game}/{page_name}`. For example, the game string for Counter-Strike 2 is `counterstrike` as found from `https://liquipedia.net/counterstrike/Autimatic`.

**name** – the name of the page of interest, this can be found from `https://liquipedia.net/{game}/{page_name}`. For example, the page name for `https://liquipedia.net/counterstrike/Autimatic` is `Autimatic`.

**user** – the exact page name on Liquipedia, as requested by the [Liquipedia API Terms of Use](https://liquipedia.net/api-terms-of-use), which should describe the projects and any contact information.

**action** – For these pages, `gg-pyparser` currently only supports wikicode parsing(the markup language of the website), `action = wikicode`, but because some pages are automatically generated, meaning that the wikicode does not yield relevant results, an html parse is currently in development(`action = html`). Currently, the html parse is only avaliable for counter-strike pages.

#### Tournament
``` python
from gg-pyparser.liquipedia_objects import tournament
t = tournament.Tournament(game = "counterstrike", name = "ELEAGUE/2018/Major",
                           user = "gg-pyparser-example(github.com/lou-zhou)",
                           action = "wikicode"
                          )#defaults action = "wikicode"
#get all matches - N.B. Since only the playoffs appear on the page,
# only the playoff matches will be returned. If we want to look at other stages, we would look at
# name = "ELEAGUE/2018/Major/{Stage Name}" 
t.get_results()

#get relevant information about the tournament
t.get_info()

#get the participants in the tournament
t.get_participants()

# get the prize pool of the tournament
t.get_prizes()

# get the talent of the tournament(the announcers, commentators, etc.)
t.get_talent()
```

#### Player
``` python
from gg-pyparser.liquipedia_objects import player
t = player.Player(game = "counterstrike", name = "autimatic",
                           user = "gg-pyparser-example(github.com/lou-zhou)",
                           action = "wikicode"
                          )#defaults action = "wikicode"
#get the gear used by the player
t.get_gear()

#get relevant information about the player
t.get_info()
```
#### Team
```python
from gg-pyparser.liquipedia_objects import team
t = team.Team(game = "counterstrike", name = "Cloud9",
                           user = "gg-pyparser-example(github.com/lou-zhou)",
                           action = "wikicode"
                          )#defaults action = "wikicode"
#get the news around the team(e.g. transfers)
t.get_news()

#get relevant information about the team
t.get_info()

#get members of the organization(e.g. CEO)
t.get_organization()

#get historical list of players
t.get_players()
```

### Parsing "General" Liquipedia Pages
To facilitate getting page names, `gg-pyparser` is also able to parse pages displaying lists of teams, players, or tournaments(e.g. [liquipedia.net/counterstrike/S-Tier_Tournaments](https://liquipedia.net/counterstrike/S-Tier_Tournaments)).

**N.B.** This parse uses an html parse, meaning that the rate limiting for the liquipedia API is significantly more stringent than wikicode parsing. Try not to call these html parses with high volume.
```python
from gg-pyparser.parse_liquipedia import parse_general_pages
#parsing tournament pages ex: https://liquipedia.net/counterstrike/S-Tier_Tournaments
parse_general_pages.parse_tournaments(name = "S-Tier_Tournaments", 
                    game =  "counterstrike",
                    user =  "gg-pyparser-example(github.com/lou-zhou)")

#parsing transfer pages ex: https://liquipedia.net/counterstrike/Transfers/2025
parse_general_pages.parse_transfers(name = "Transfers/2025",  
                game =  "counterstrike",
                user =  "gg-pyparser-example(github.com/lou-zhou)")

#parsing team pages ex: https://liquipedia.net/counterstrike/Portal:Teams/Europe
parse_general_pages.parse_teams(region= "Europe", 
            game = "counterstrike", 
            user =  "gg-pyparser-example(github.com/lou-zhou)")

#parsing player pages ex: https://liquipedia.net/counterstrike/Portal:Players/Europe
parse_general_pages.parse_players(region= "Europe", 
        game = "counterstrike", user =  "gg-pyparser-example(github.com/lou-zhou)")
#parsing player pages ex: https://liquipedia.net/counterstrike/Banned_Players/Valve
#N.B. for games where there is no tournament specific bans, company is set to None
parse_general_pages.parse_banned_players(game = "counterstrike", 
            user = "gg-pyparser-example(github.com/lou-zhou)",
            company = "Valve")

```
### Parsing Multiple Liquipedia Pages
With rate-limiting as described by the [Liquipedia API Terms of Use](https://liquipedia.net/api-terms-of-use), to avoid being blocked, `ggparserpy` allows multiple wikicode page returns from a single request using `parse_liquipedia.parse_multiple_liquipedia_pages`. This function builds a dictionary between the page_names and the corresponding Python `liquipedia_object`.
```python
#Ex: parsing IEM Cologne and Autimatic's Page
from gg-pyparser.parse_liquipedia import parse_multiple_liquipedia_pages

parse_multiple_liquipedia_pages.create_multiple_pages(game = "counterstrike",
        page_names = ["Intel_Extreme_Masters/2025/Cologne", "Autimatic"],
        user = "gg-pyparser-example(github.com/lou-zhou)",
        page_ts = ["tournament", "player"])
#page_names is a list of strings describing the page names of each page
#page_ts is a list of strings of page types, valid elements of "tournament", "player", "team"
```

## Important Note

Because this library relies the Liquipedia API, calls are subject to following the [Liquipedia API Terms of Use](https://liquipedia.net/api-terms-of-use), including rate-limiting of **1 call per 2 seconds for wikicode requests** and **1 call per 30 seconds for html requests**.

For reference, a call occurs whenever the user calls a ```Tournament, Team, or Player``` object is created(with the exception being with `parse_multiple_liquipedia_pages` where mutiple pages are generated from one call). I strongly recommend reviewing the Terms of Use and implementing throttling between requests to prevent exceeding these limits and risking an IP ban.

## Issues and Bugs
This library is designed as a general solution for parsing data across a diverse range of esports, each with unique tournament formats and prize pool structures. As an early-stage project maintained by an undergraduate student with limited professional software development experience, bugs are to be expected. Feedback and bug reports are encouraged and can be submitted via [Issues](https://github.com/Lou-Zhou/gg-pyscraper/issues)

## Contributing
Contributions are more than welcome! If you're interested in contributing to this library, please make a [Pull Request](https://github.com/Lou-Zhou/gg-pyscraper/pulls).

## Author and Acknowledgement
- Lou Zhou  
    - [Website](https://lou-zhou.github.io/)  
    - [LinkedIn](https://www.linkedin.com/in/lou-zhou/)  
    - [Github](https://github.com/Lou-Zhou)

Data used by this project is sourced from [Liquipedia](https://liquipedia.net/), which is licensed under the Creative Commons Attribution-ShareAlike 3.0 License (CC BY-SA 3.0). In compliance with the license terms, please attribute Liquipedia as the source when using or redistributing this data.


