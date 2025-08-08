"""
Module for representing and extracting information about a general liquipedia page.

Defines the liquipedia page class, provides
methods to fetch and parse general page data such as the infobox

Classes
-------
LiquipediaPage
    Represents an individual page and provides methods to extract structured information
    about the page's infobox and other helper functions

Dependencies
------------
- BeautifulSoup
- pandas
- mwparserfromhell: For parsing MediaWiki markup.
- parse_liquipedia, Custom module for parsing specific data blocks.

Raises
------
UnknownParsingMethodException
    Raised when the parsing method is not "action" or "query"
"""
from typing import Dict, Union,Optional, Type, TypeVar, List
import warnings
import mwparserfromhell as mw
from bs4 import BeautifulSoup
from bs4.element import Tag
import re
import pandas as pd
from ggpyscraper.parse_liquipedia import parse_liquipedia_wc
T = TypeVar('T', bound='LiquipediaPage')
class UnknownParsingMethodException(Exception):
    """Exception raised when the parsing method is not html or wikicode"""
class LiquipediaPage:
    """
    A class to represent a liquipedia page.

    ...

    Attributes
    ----------
    game: str
        The game being played
    name: str
        The page name, found by liquipedia.com/game/(name)
    user: str
        The user, as requested by liquipedia ToS
    action: str
        Whether html(action = "parse") or wikicode(action = "query") parsing should occur
    raw_str: str
        The raw string describing the text of the player's page

    Methods
    -------
    get_info(infobox_name = "Infobox player")
        Parses information from the players infobox
    get_raw_str()
        Gets the raw string describing the page's text
    """
    def __init__(self, game : str, name : str,
                user : str = "initial python testing(github.com/louzhou)",
                action : str= "query") -> None:
        """
        Creates a LiquipediaPage object

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
        if action not in ["query", "parse"]:
            raise UnknownParsingMethodException("Unknown Parsing Method")
        self.user = user
        self.game = game
        self.name = name
        self.action = action
        self.raw_str = self._make_request()


    def get_raw_str(self):
        """Returns the page's raw text"""
        return self.raw_str


    def _make_request(self) -> str:
        """Makes the API call depending on whether to use html or wikicode parsing"""
        raw_str = list(parse_liquipedia_wc.make_request(self.user,
                                                    self.game,self.name, self.action).values())[0]
        if self.action == "query":
            match = re.search(r"#REDIRECT\s*\[\[(.*?)\]\]", raw_str, flags=re.IGNORECASE)
            if match:
                #check if redirect is needed
                new_name = match.group(1)
                raw_str = list(parse_liquipedia_wc.make_request(self.user,
                                                    self.game, new_name, self.action).values())[0]

            return str(raw_str)
        else:
            souped = BeautifulSoup(raw_str, "html.parser")
            redirect = souped.find("div", class_ = "redirectMsg")
            redirect = redirect.find("a") if redirect else None
            if isinstance(redirect, Tag):
                new_name = redirect.get("href") if redirect else None
                if isinstance(new_name, str):
                    new_name = new_name.rsplit("/", 1)[1]
                    raw_str = list(parse_liquipedia_wc.make_request(self.user, self.game,
                                                                new_name, self.action).values())[0]
            return str(raw_str)

    def get_info(self, infobox_name: str = "Infobox league"
                 ) -> Dict[str, Union[str, pd.DataFrame, List[Dict[str, str]]]]:
        """Gets the information from the page's infobox """
        if self.action == "query":
            return self._get_info_wc(infobox_name)
        return self._get_info_html()

    def _get_info_html(self) -> Dict[str, Union[str, pd.DataFrame, List[Dict[str, str]]]]:
        """Private method to get page's infobox using a html parse"""
        souped = BeautifulSoup(self.get_raw_str(), "html.parser")
        infoboxes = souped.select('div[class="fo-nttax-infobox"]')
        if len(infoboxes) == 0:
            raise parse_liquipedia_wc.SectionNotFoundException("Infobox Section not Found")
        if len(infoboxes) > 1:
            warnings.warn("Multiple infoboxes detected, taking first one found", UserWarning)
        infobox = infoboxes[0]

        rows = infobox.find_all("div", class_="infobox-cell-2 infobox-description")
        info = {}

        for row in rows:
            key = row.get_text(strip=True).rstrip(":")
            value_div = row.find_next_sibling("div")
            value = [a.get_text(strip=True) for a in value_div.find_all("a") if
                     a.get_text(strip=True)]
            if len(value) <= 1:
                value = value_div.get_text("", strip = True)
            info[key] = value
        return info



    def _get_info_wc(self, infobox_name:str
                     ) -> Dict[str, Union[str, pd.DataFrame, List[Dict[str, str]]]]:
        """Private method to get page's infobox using a wikicode parse"""
        infobox_dict = {}
        str_parsed = mw.parse(self.raw_str)
        for template in str_parsed.filter_templates():
            if template.name.matches(infobox_name):
                for param in template.params:
                    key = str(param.name).strip()
                    value = str(param.value).strip()
                    infobox_dict[key] = value
                self.name = infobox_dict['name'] if (self.name is None
                                                     and "name" in infobox_dict) else self.name
                break
        return infobox_dict
    @classmethod
    def from_raw_str(
        cls: Type[T],
        response: str,
        game: Optional[str] = None,
        name: Optional[str] = None,
        user: str = "initial python testing(github.com/louzhou)",
        action: str = "query"
    ) -> T:
        """Alternate constructor to build a liquipedia page object from the raw text"""
        obj = cls.__new__(cls)
        obj.user = user
        obj.raw_str = response
        obj.game = game
        obj.name = name
        if action not in ["query", "action"]:
            raise UnknownParsingMethodException("Unknown Parsing Method")
        return obj
