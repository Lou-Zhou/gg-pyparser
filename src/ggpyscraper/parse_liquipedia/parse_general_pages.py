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
def parse_collapsable_tables(soup : BeautifulSoup) -> pd.DataFrame:
    """
    Parses a beautifulsoup collapsible table

    Parameters
    ----------
        soup : BeautifulSoup
            A beautifulsoup object to parse
    
    Returns
    -------
        pd.DataFrame:
            A pandas dataframe describing the results of all the tables

    """
    tables = soup.select("table.wikitable.collapsible")
    player_data = []
    for table in tables:
        rows = table.find_all('tr')
        headers = rows[:2]
        large_header = headers[0].get_text()
        subheaders = headers[1].find_all("th")
        header_map = dict(zip(range(len(subheaders)),
                                [h.get_text(strip = True) for h in subheaders]))
        for person in rows[2:]:
            header_idx = 0
            elements = person.find_all("td")
            person_dict = {'type': large_header}
            for element in elements:
                header = header_map[header_idx]
                links = element.find_all("a")
                link_list = []
                for link in links:
                    link_list.append(link.get("href"))
                link_list = list(set(link_list))
                person_dict[header] = element.get_text(strip = True)
                if len(link_list) > 0:
                    if header.lower() == "links":
                        person_dict[header] = link_list
                    else:
                        person_dict[f"{header}_links"] = link_list
                header_idx += 1
                #print(person_dict)
            player_data.append(person_dict)
        #county_players = {"country": country, "name": player.get_text() for player in players}
    return pd.DataFrame(player_data)

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
    raw_str = liquipedia_page.LiquipediaPage(game = game, name = name,
                                             action = "html").get_raw_str()
    tournament_data = []
    souped = BeautifulSoup(raw_str, "html.parser")
    cell_name = "div"
    rows = souped.find_all("div", class_ = "divRow")
    if len(rows) == 0:
        rows = souped.find_all("div", class_ = "gridRow")
        cell_name = "grid"
    for row in rows:
        cells = row.find_all("div", class_ = f"{cell_name}Cell")
        row_data = {}
        for cell in cells:
            cell_class = cell.get("class")
            text = list(set([val for val in cell.get_text(separator= "|").split("|")
                             if len(val.strip()) > 0]))
            if "Header" in cell_class:
                cell_class.remove("Header")
            hrefs = list(set([href['href'] for href in cell.find_all('a')]))
            header_name = cell_class[-1]
            if "Place" not in header_name and "Qualified" not in header_name:
                #if not teams, then don't keep separated
                text = "".join(text)
            if "EventDetails" in header_name:
                #don't know true header, must infer
                if "Left" in header_name:
                    #this is wayyyy to stringent, rework moving forward
                    header_name = "Date" if "55" in header_name else header_name
                    header_name = "Location" if "60" in header_name else header_name
                if "Right" in header_name:
                    header_name = "Prize" if "45" in header_name else header_name
                    header_name = "PlayerNumber" if "40" in header_name else header_name
            text = text[0] if isinstance(text, list) and len(text) == 1 else text
            row_data[header_name] = text
            if len(hrefs) > 0:
                row_data[f"{header_name}_links"] = hrefs
        tournament_data.append(row_data)
    return pd.DataFrame(tournament_data)

def parse_teams(region: str, game: str) -> pd.DataFrame:
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
    name = f"Portal:Teams/{region}"
    raw_str = liquipedia_page.LiquipediaPage(game = game,
                                            name = name, action = "html").get_raw_str()
    soup = BeautifulSoup(str(raw_str), "html.parser")

    active_teams = parse_collapsable_tables(soup)
    active_teams['active'] = True
    #parse inactive teams
    inactive = []
    if game == "counterstrike":
        tables = soup.select("table.wikitable.smwtable")
        for table in tables:
            inactive.append({'type': table.get_text(strip = True), 'active': False,})
        
    else:
        disbanded = soup.find("span", id = "Disbanded_teams").findNext('div')
        for li in disbanded.find_all('li'):
            inactive.append({'type': li.get_text(strip = True), 'active' : False})
    inactive = pd.DataFrame(inactive)
    return pd.concat([active_teams, inactive]).rename(columns = {"type": "team"})

def parse_players(region: str, game: str) -> pd.DataFrame:
    """
    Parses general teams pages like https://liquipedia.net/counterstrike/Portal:Players/Europe

    Parameters
    ----------
        region: str
            The region of interest, found from 
            https://liquipedia.net/{game}/Portal:Players/{region}
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
                                            name = name, action = "html").get_raw_str()
    soup = BeautifulSoup(str(raw_str), "html.parser")
    tables = soup.find_all("table", class_=["wikitable", "collapsible"])
    if game == "counterstrike":
        #cs has a different player style for some reason
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
    else:
        soup = BeautifulSoup(raw_str)
        return parse_collapsable_tables(soup)

def parse_banned_players(game : str, company: str = None) -> pd.DataFrame:
    """
    Parses banned players page

    Parameters
    ----------
        company: str
            The company banning the players, found from 
            https://liquipedia.net/{game}/Banned_Players/{company}
            If no company, use None
        game: str
            The game being played
    
    Returns
    -------
        pd.DataFrame
            A dataframe describing the contents of the banned players webpage
    """
    name = f"Banned_Players/{company}"
    if company is None:
        name = "Banned_players"
    raw_str = liquipedia_page.LiquipediaPage(game = game,
                                            name = name, action = "html").get_raw_str()
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

def parse_transfers(name:str, game:str) -> pd.DataFrame:
    """
    Parses transfers page

    Parameters
    ----------
        name: str
            The time period considered, found from
            https://liquipedia.net/counterstrike/{name}
            Usually "Transfers/{time}" or "Player_Transfers/{time}"

        game: str
            The game being played
    
    Returns
    -------
        pd.DataFrame
            A dataframe describing the contents of transfers page
    """
    raw_str = liquipedia_page.LiquipediaPage(game = game,
                                            name = name, action = "html").get_raw_str()
    soup = BeautifulSoup(str(raw_str), "html.parser")
    tables = soup.find_all("div", class_ = "divTable mainpage-transfer Ref")
    transfers_list = []

    for table in tables:
        transfers  = table.find_all("div", class_ = "divRow")
        for transfer in transfers:
            transfer_dict = {}
            date = transfer.find("div", class_ = "divCell Date")
            transfer_dict['date'] = date.get_text()

            # Extract player names
            transfer_dict['names'] = [
            block.select_one(".name a").get_text(strip=True)
            for block in transfer.select("div.block-player")
            ]
            transfer_dict['name_links'] = [
            link.find("a")['href'] for link in
            transfer.select("div.block-player")
            ]
            # Extract old and new team titles
            for key, class_name in [("old", "divCell Team OldTeam"),
                                     ("new", "divCell Team NewTeam")]:
                team_div = transfer.find("div", class_=class_name)
                a_tag = team_div.find("a") if team_div else None
                transfer_dict[key] = a_tag['title'] if a_tag else None
                if a_tag:
                    transfer_dict[f"{key}_link"] = a_tag['href']
            transfers_list.append(transfer_dict)
    return pd.DataFrame(transfers_list)
