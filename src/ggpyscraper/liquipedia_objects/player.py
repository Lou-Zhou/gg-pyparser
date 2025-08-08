"""
Module for representing and extracting information about esports players from Liquipedia.

Defines the Player class, inherits from LiquipediaPage and provides
methods to fetch and parse player-specific data such as team history, gear setup, and
achievements from Liquipedia. 

Classes
-------
Player
    Represents an individual player and provides methods to extract structured information
    about their competitive history, gear settings, and tournament achievements.

Dependencies
------------
- BeautifulSoup
- pandas
- mwparserfromhell: For parsing MediaWiki markup.
- parse_liquipedia, parse_liquipedia_html: Custom modules for parsing specific data blocks.
- LiquipediaPage: Base class for interacting with Liquipedia.
"""
from typing import Dict, List, Union
import re
from bs4 import BeautifulSoup
import pandas as pd
import mwparserfromhell as mw
from ggpyscraper.parse_liquipedia import parse_liquipedia_html, parse_liquipedia_wc
from ggpyscraper.liquipedia_objects import liquipedia_page


class Player(liquipedia_page.LiquipediaPage):
    """
    A class to represent a player.


    Methods
    -------
    get_info(infobox_name = "Infobox player"):
        Parses information from the players infobox
    get_gear()
        Parses information about the gear the player uses
    get_achievements()
        Parses information about the player's achievements(html only)
    
    """
    def __init__(self, game :str, name: str,
                 user: str ="initial python testing(github.com/louzhou)", action : str = "query"
                 ) -> None:
        """
        Creates a player object

        Parameters
        ----------
        game: str
            The game being played
        name: str
            The page name, found by liquipedia.com/game/(name)
        user: str
            The user, as requested by liquipedia ToS
        action: str
            Whether html(action = "parse") or wikicode(action = "query") parsing should occur
        """
        super().__init__(game, name, user=user, action = action)

    def get_info(self, infobox_name: str = "Infobox player"
    ) -> Dict[str, Union[str, pd.DataFrame, List[Dict[str, str]]]]:
        """
        Gets the information from a player's infobox

        Parameters
        ----------
            infobox_name: str
                The name of the infobox to parse, defaults to "infobox player", 
                custom to each type of object
        
        Returns
        -------
            Dict[str, str]
                A dictionary describing the contents of the infobox
        """
        if self.action == "query":
            return self._get_info_wc(infobox_name = infobox_name)
        return self._get_info_html()

    def _get_info_html(self) -> Dict[str, Union[str, pd.DataFrame, List[Dict[str, str]]]]:
        """
        Private method to get infobox data using an html parser

        Returns
        -------
            Dict[str, str]
                A dictionary describing the contents of the infobox
        """
        info_dict = super()._get_info_html()

        #parse previous teams
        souped = BeautifulSoup(self.get_raw_str(), "html.parser")
        history_entries = parse_liquipedia_html.parse_team_history(souped)
        team_history = pd.DataFrame(history_entries)
        team_history['game'] = team_history['game'].fillna(self.game)
        info_dict['team_history'] = team_history
        return info_dict

    def _get_info_wc(self, infobox_name : str ="Infobox player"
                     ) -> Dict[str, Union[str, pd.DataFrame, List[Dict[str, str]]]]:
        """
        Private method to get infobox data using a wikicode parser

        Parameters
        ----------
            infobox_name: str
                The name of the infobox to parse, defaults to "infobox player", 
                custom to each type of object

        Returns
        -------
            Dict[str, str]
                A dictionary describing the contents of the infobox
        """
        info_dict =  super().get_info(infobox_name)
        if 'team_history' in info_dict and isinstance(info_dict['team_history'], str):
            info_dict['team_history'] = parse_liquipedia_wc.parse_player_team_history(
                info_dict['team_history'])
        else:
            info_dict['team_history'] = pd.DataFrame()
        return info_dict

    def get_gear(self) -> Dict[str, pd.DataFrame]:
        """
        Gets information about the player's gear

        Returns
        -------
            Dict[str, pd.DataFrame]
                A dictionary mapping gear to the contents of each gear section
        """
        if self.action == "query":
            return self._get_gear_wc()
        return self._get_gear_html()

    def _get_gear_html(self):
        """
        Private method to parse gear information with html

        Returns
        -------
            Dict[str, pd.DataFrame]
                A dictionary mapping gear to the contents of each gear section
        """
        all_data = {}
        souped = BeautifulSoup(self.get_raw_str(), "html.parser")
        sections = parse_liquipedia_html.get_all_under_header(souped,  "Gear_and_Settings")
        for table in sections:
            if table.get("class") and any("table" in c for c in table.get("class")):
                table, title  = parse_liquipedia_html.parse_wikitable_hdhd(table, rm_1 = True)
                all_data[title] = table
                #print(table)
        if len(all_data) == 0:
            raise parse_liquipedia_wc.SectionNotFoundException("Could not find gear section")
        return all_data

    def _get_gear_wc(self):
        """
        Private method to parse gear information with wikicode

        Returns
        -------
            Dict[str, pd.DataFrame]
                A dictionary mapping gear to the contents of each gear section
        """
        parsed = mw.parse(self.get_raw_str())
        gear_dict = {}
        for section in parsed.get_sections(include_lead=False, include_headings=True):
            heading = section.filter_headings()[0].title.strip().lower()

            if heading == "gear and settings":
                for template in section.filter_templates():
                    if "table" in template.name.lower():
                        elements = re.findall(r"\|([^=|]+)=([^|]+)", str(template))
                        table_dict = {k.strip(): v.strip("}\n") for k, v in elements}
                        template_name = str(template.name).strip()
                        template_name = re.sub(r"\s*table$", "", template_name, flags=re.IGNORECASE)
                        gear_dict[template_name.lower()] = table_dict
            break
        return gear_dict
    def get_achievements(self) -> Union[List[pd.DataFrame],
                            List[Dict[str, pd.DataFrame]],
                            pd.DataFrame]:
        """
        Parse a player's achievements

        Returns
    -------
        Union[List[pd.DataFrame],
            List[Dict[str, pd.DataFrame]],
            pd.DataFrame]
            Either a list of dataframes, dictionaries mapping 
            headers to dataframes or just a dataframe describing the achievements section
        """
        if self.action == "query":
            raise parse_liquipedia_wc.SectionNotFoundException(
                "Cannot parse achievements section using action = query, try action = parse")
        return parse_liquipedia_html.parse_achievements(BeautifulSoup(
            self.get_raw_str(),"html.parser"))
