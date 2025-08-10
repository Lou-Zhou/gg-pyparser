"""
Module for representing and extracting information about a team.

Defines the Team class, provides
methods to fetch and parse team data like achievements

Classes
-------
Team
    Represents an individual team and provides methods to extract structured information
    about competitive history and news

Dependencies
------------
- BeautifulSoup
- pandas
- mwparserfromhell: For parsing MediaWiki markup.
- parse_liquipedia, parse_liquipedia_html, Custom modules for parsing specific data blocks.
- LiquipediaPage: Base class for interacting with Liquipedia.
"""
from typing import Dict, List, Union
import re
import pandas as pd
from bs4 import BeautifulSoup
import mwparserfromhell as mw
from ggpyscraper.parse_liquipedia import parse_liquipedia_html, parse_liquipedia_wc
from ggpyscraper.liquipedia_objects import liquipedia_page
ParsedValue = Union[str, pd.DataFrame, List[Dict[str, str]]]
class Team(liquipedia_page.LiquipediaPage):
    """
    A class to represent a liquipedia page.


    Methods
    -------
    get_info(infobox_name = "Infobox team")
        Parses information from the players infobox
    get_news()
        Get all news about the team
    get_players()
        Get all current and inactive players
    get_organization()
        Get all current and inactive organization members
    get_results()
        Get both the achievements and recent matches for a team
    """
    def __init__(self, game, name, user="initial python testing(github.com/louzhou)",
                  action = "wikicode"):
        """
        Creates a Team object

        Parameters
        ----------
        game: str
            The game being played
        name: str
            The page name, found by liquipedia.com/game/(name)
        user: str
            The user, as requested by liquipedia ToS
        action: str
            Whether html(action = "parse") or wikicode(action = "wikicode") parsing should occur
        """
        super().__init__(game, name, user=user, action = action)
    def get_info(self, infobox_name: str = "Infobox team"
                 ) -> Dict[str, Union[str, pd.DataFrame, List[Dict[str, str]]]]:
        """
        Gets the information from a team's infobox
        """
        info_dict =  super().get_info(infobox_name)
        for entry, text in info_dict.items():
            pattern = (
                r"\{\{Flag\|(\w+)\}\}\s*"
                r"(?:"
                    r"\[\[[^\|\]]+\|([^\]]+)\]\]"  # [[link|display]]
                    r"|"                           # or
                    r"\[\[([^\]]+)\]\]"            # [[link]]
                    r"|"                           # or
                    r"([A-Za-z0-9\-\s]+)"          # plain text fallback
                r")"
            )

            matches = re.findall(pattern, str(text))
            if len(matches) > 0:
                matches = [tuple(x for x in t if x) for t in matches]
                info_dict[entry] = [{"country": t1, "name": t2} for t1, t2 in matches]
        return info_dict

    def get_news(self) -> pd.DataFrame:
        """ Gets the data about a team's news """
        if self.action == "wikicode":
            return self._get_news_wc()
        return self._get_news_html()

    def _get_news_html(self) -> pd.DataFrame:
        """ Private method to get the data about a team's news using an html parse """
        souped = BeautifulSoup(self.get_raw_str(), "html.parser")
        timeline_data = parse_liquipedia_html.get_all_under_header(souped, "Timeline")
        tabbed_data = []
        for data in timeline_data:
            if data.get("class") and  any("tabs" in c for c in data.get("class")):
                timeline_table = parse_liquipedia_html.build_tab_map(data)
                tabbed_data.append(pd.concat
                                   ([pd.DataFrame(parse_liquipedia_html.
                                     parse_single_tab_history(text, year))
                                     for year, text in timeline_table.items()]))
            else:
                tabbed_data.append(pd.DataFrame(parse_liquipedia_html.
                                                parse_single_tab_history(data)))
        return pd.concat(tabbed_data)

    def _get_news_wc(self) -> pd.DataFrame:
        """ Private method to get the data about a team's news using wikicode parse """
        news_data = []
        parsed = mw.parse(self.raw_str)
        for section in parsed.get_sections(include_lead=False, include_headings=True):
            header = section.filter_headings()[0].title.strip().lower()
            if header == "timeline":
                year_text_map = parse_liquipedia_wc.get_name_content_map(str(section))
                for year, text in year_text_map.items():
                    entries = text.split("\n")
                    for entry in entries:
                        data = parse_liquipedia_wc.parse_news_str(entry)
                        if data != -1 and len(data) > 0:
                            data['year'] = year
                            news_data.append(data)
        return pd.DataFrame(news_data)

    def get_players(self) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """Gets information about a team's players"""
        if self.action == "wikicode":
            return self._get_people_wc("player roster")
        return self._get_people_html(header = "Player_Roster")

    def get_organization(self)  -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """Gets information about a team's organization"""
        if self.action == "wikicode":
            return self._get_people_wc("organization")
        return self._get_people_html(header = "Organization")

    def _get_people_html(self, header) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """Private method parsing a section describing people with html
        Parameters
        ----------
            header: str
                The name of the header of interest

        Returns
        -------
            Dict[str, pd.DataFrame]]
                A dataframe or dictionary of dataframes describing 
                information about the section's people
        """
    #game.find_all("div", class_ = "table-responsive")
        souped = BeautifulSoup(self.get_raw_str(), "html.parser")
        all_players = []
        for section in parse_liquipedia_html.get_all_under_header(souped, header = header):
            tab_map = parse_liquipedia_html.build_tab_map(section)
            if len(tab_map) == 0:
                all_players = all_players + parse_liquipedia_html.parse_players_raw(
                    section, self.game)
            else:
                for game, text in tab_map.items():
                    all_players = all_players + parse_liquipedia_html.parse_players_raw(
                        text, game)
        return pd.concat(all_players)

    def _get_people_wc(self, header) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """Private method parsing a section describing people with wikicode
        Parameters
        ----------
            header: str
                The name of the header of interest

        Returns
        -------
            Dict[str, pd.DataFrame]]
                A dataframe or dictionary of dataframes describing 
                information about the section's people
        """
        all_people = []
        stand_ins = []
        parsed = mw.parse(self.raw_str)
        for section in parsed.get_sections(include_lead=False, include_headings=True):
            sec_title = section.filter_headings()[0].title.strip().lower()
            if sec_title == header:
                #get players(non standins)
                people = re.findall(r"\{\{Person\|((?:[^{}]|\{\{[^{}]*\}\})*)\}\}",
                                    str(section), re.DOTALL)
                for person in people:
                    person_dict = parse_liquipedia_wc.parse_person(person)
                    if 'role' in person_dict and "abbr" in person_dict['role'].lower():
                        person_dict['role'] = re.split("[|/]", person_dict['role'])[-1].strip("}")
                    all_people.append(person_dict)
                people = re.findall(r"\{\{Stand-in\|((?:[^{}]|\{\{[^{}]*\}\})*)\}\}",
                                     str(section), re.DOTALL)
                for person in people:
                    person_dict = parse_liquipedia_wc.parse_person(person)
                    stand_ins.append(person_dict)
        if len(stand_ins) > 0:
            return pd.concat([pd.DataFrame(all_people),
            pd.DataFrame(stand_ins)])
        return pd.DataFrame(all_people)
    def get_results(self):
        """Parses results section for a team"""
        if self.action == "wikicode":
            raise parse_liquipedia_wc.SectionNotFoundException(
                "Cannot parse results section using action = query, try action = parse")

        souped = BeautifulSoup(self.get_raw_str(), "html.parser")
        timeline_data = parse_liquipedia_html.get_all_under_header(souped, "Results")
        for data in timeline_data:
            if data.get("class") and  any("tabs" in c for c in data.get("class")):
                timeline_table = parse_liquipedia_html.build_tab_map(data)
                return {k: parse_liquipedia_html.
                        parse_wikitable_achievements(v) for k,v in timeline_table.items()}
        raise parse_liquipedia_wc.SectionNotFoundException("Could not find results table")
    