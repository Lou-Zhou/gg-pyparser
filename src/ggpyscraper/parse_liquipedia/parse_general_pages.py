"""
Module to parse the general Liquipedia pages

Dependencies
------------
- BeautifulSoup
- pandas
- liquipedia_page: Base class for interacting with Liquipedia.
"""
import pandas as pd
from bs4 import BeautifulSoup
from ggpyscraper.liquipedia_objects import liquipedia_page
def parse_tournaments(name : str, game: str) -> pd.DataFrame:
    """
    Parses general tournament pages like https://liquipedia.net/counterstrike/S-Tier_Tournaments

    Parameters
    ----------
        name: str
            Name of the page, found from https://liquipedia.net/counterstrike/{page}
        game: str
            The game being played
    
    Returns
    -------
        pd.DataFrame
            A dataframe describing the contents of the tournament webpage
    """
    raw_str = liquipedia_page.LiquipediaPage(game = game,
                                             name = name, action = "parse").get_raw_str()
    soup = BeautifulSoup(str(raw_str), "html")
    all_tournaments = []
    for tournament in soup.find_all("div", class_ = "gridRow"):
        tourn_dictionary = {}
        tier_cell = tournament.find("div", class_="gridCell Tier Header")
        if tier_cell and (links := tier_cell.find_all("a")) and links[-1].has_attr("title"):
            tourn_dictionary["tier"] = links[-1]["title"]
        else:
            tourn_dictionary["tier"] = None

        tournament_cell = tournament.find("div", class_ = "gridCell Tournament Header")
        link_tag = tournament_cell.find("a") if tournament_cell else None
        tourn_dictionary["link"] = link_tag.get("href") if link_tag else None
        tourn_dictionary["title"] = link_tag.get("title") if link_tag else None

        date =  tournament.find("div", class_ = "gridCell EventDetails Date Header")
        tourn_dictionary['date'] = date.get_text() if date else None
        prize = tournament.find("div", class_ = "gridCell EventDetails Prize Header")
        tourn_dictionary['prize_pool'] = prize.get_text() if prize else None

        #get location
        location = tournament.find("div", class_="gridCell EventDetails Location Header")
        tourn_dictionary['location'] = location.get_text() if location else None

        # get placements
        first = tournament.find("div", class_="gridCell Placement FirstPlace Blank")
        tourn_dictionary['first'] = first.get_text() if first else None

        second = tournament.find("div", class_="gridCell Placement SecondPlace Blank")
        tourn_dictionary['second'] = second.get_text() if second else None

        if not tourn_dictionary['first']:
            first = tournament.find("div", class_="gridCell Placement FirstPlace")
            tourn_dictionary['first'] = first.get_text() if first else None
        if not tourn_dictionary['second']:
            second = tournament.find("div", class_="gridCell Placement SecondPlace")
            tourn_dictionary['second'] = second.get_text() if second else None

        if not tourn_dictionary.get('first') and not tourn_dictionary.get('second'):
            qualifiers = tournament.find("div", class_="gridCell Placement Qualified")
            if qualifiers:
                teams = [team.get_text() for team in qualifiers.select(".team-template-text a")]
            else:
                qualifiers = tournament.find("div", class_="gridCell Placement Qualified Blank")
                if qualifiers:
                    teams = [team.get_text() for team in qualifiers.select(".team-template-text")]
                else:
                    teams = []
            tourn_dictionary['qualified'] = teams

        all_tournaments.append(tourn_dictionary)

    return pd.DataFrame(all_tournaments)

def parse_teams(region, game):
    """
    Parses general teams pages like https://liquipedia.net/counterstrike/Portal:Teams/Europe

    Parameters
    ----------
        region: str
            The region of interest, found from 
            https://liquipedia.net/counterstrike/Portal:Teams/{region}

        game: str
            The game being played
    
    Returns
    -------
        pd.DataFrame
            A dataframe describing the contents of the teams webpage
    """
    name = f"Portal:/Teams/{region}"
    raw_str = liquipedia_page.LiquipediaPage(game = game,
                                            name = name, action = "parse").get_raw_str()
    soup = BeautifulSoup(str(raw_str), "html")
    tables = soup.find_all("table", class_=["wikitable", "collapsible", "smwtable"])
    teams_data = []

    for table in tables:

        team_name_tag = table.find("th", colspan="2")
        disbanded = False
        if not team_name_tag:
            team_name = table.get_text(strip = True)
            disbanded = True
            players = []
        else:
            team_name = team_name_tag.get_text(strip=True)
            players = []
            for row in table.find_all("tr")[2:]:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    player_id = cols[0].get_text(strip=True)
                    real_name = cols[1].get_text(strip=True)
                    players.append({"id": player_id, "real_name": real_name})

        teams_data.append({
            "team": team_name,
            "players": players,
            "disbanded": disbanded
        })

    return pd.DataFrame(teams_data)

def parse_players(region, game):
    """
    Parses general teams pages like https://liquipedia.net/counterstrike/Portal:Players/Europe

    Parameters
    ----------
        region: str
            The region of interest, found from 
            https://liquipedia.net/counterstrike/Portal:Players/{region}
            N.B. For Africa and the Middle East, the region is "Africa_&_Middle_East" 
            not "Africa_%26_Middle_East"

        game: str
            The game being played
    
    Returns
    -------
        pd.DataFrame
            A dataframe describing the contents of the players webpage
    """
    name = f"Portal:Players/{region}"
    raw_str = liquipedia_page.LiquipediaPage(game = game,
                                            name = name, action = "parse").get_raw_str()
    soup = BeautifulSoup(str(raw_str), "html")
    tables = soup.find_all("table", class_=["wikitable", "collapsible"])
    player_dict = []
    for table in tables:
        country = table.find('th').get_text()
        players = table.find_all("td")
        for player in players:
            name = player.get_text().split(" - ")[1]
            tag = player.get_text().split(" - ")[0]
            player_dict.append({"country": country, "name":name, "tag":tag})
        #county_players = {"country": country, "name": player.get_text() for player in players}
    return pd.DataFrame(player_dict)


def parse_banned_players(company, game):
    """
    Parses banned players page

    Parameters
    ----------
        company: str
            The company banning the players, found from 
            https://liquipedia.net/{game}/Banned_Players/{company}

        game: str
            The game being played
    
    Returns
    -------
        pd.DataFrame
            A dataframe describing the contents of the banned players webpage
    """
    name = f"Banned_Players/{company}"
    raw_str = liquipedia_page.LiquipediaPage(game = game,
                                            name = name, action = "parse").get_raw_str()
    soup = BeautifulSoup(str(raw_str), "html")
    tables = soup.find_all("div", class_ = "divTable Ref")
    banned = []
    for table in tables:
        players = table.find_all("div", class_ = "divRow mainpage-transfer-neutral")
        for player in players:
            banned_dict = {}
            name = player.find("div", class_ = "divCell Name")
            banned_dict['name'] = name.get_text() if name else None

            team = player.find("div", class_ = "divCell Team")
            banned_dict["team"] = team.find("a").get("title") if team and team.find("a") else None

            for div in player.find_all("div", class_ = "divCell"):
                #this is really dumb but idk other ways to find reason besides parsing all divCells
                if div.get("class") == ['divCell']:
                    banned_dict['reason'] = div.get_text()

            start, end = player.find_all("div", class_ = "divCell Date")
            banned_dict['start'] = start.get_text() if start else None
            banned_dict['end'] = end.get_text() if end else None
            banned.append(banned_dict)

    return pd.DataFrame(banned)

def parse_transfers(time, game):
    """
    Parses transfers page

    Parameters
    ----------
        time: str
            The time period considered, found from
            https://liquipedia.net/counterstrike/Player_Transfers/{time}

        game: str
            The game being played
    
    Returns
    -------
        pd.DataFrame
            A dataframe describing the contents of transfers page
    """
    name = f"Player_Transfers/{time}"
    raw_str = liquipedia_page.LiquipediaPage(game = game,
                                            name = name, action = "parse").get_raw_str()
    soup = BeautifulSoup(str(raw_str), "html")
    tables = soup.find_all("div", class_ = "divTable mainpage-transfer Ref")
    transfers_list = []

    for table in tables:
        transfers  = table.find_all("div", class_ = "divRow mainpage-transfer-neutral")
        for transfer in transfers:
            transfer_dict = {}
            date = transfer.find("div", class_ = "divCell Date")
            transfer_dict['date'] = date.get_text()

            # Extract player names
            transfer_dict['names'] = [
            block.select_one(".name a").get_text(strip=True)
            for block in transfer.select("div.block-player")
            ]

            # Extract old and new team titles
            for key, class_name in [("old", "divCell Team OldTeam"),
                                     ("new", "divCell Team NewTeam")]:
                team_div = transfer.find("div", class_=class_name)
                a_tag = team_div.find("a") if team_div else None
                transfer_dict[key] = a_tag.get("title") if a_tag else None
            transfers_list.append(transfer_dict)
    return pd.DataFrame(transfers_list)
