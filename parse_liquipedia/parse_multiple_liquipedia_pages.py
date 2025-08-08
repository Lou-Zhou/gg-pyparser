"""
Module with functions parsing multiple liquipedia objects with only one call

Dependencies
------------
- parse_liquipedia
- liquipedia_objects

Classes
-------
PageTypeRegistry
    Class defining mapping between strings and classes

Raises
------
MethodNotFoundException
    Raised when calling an invalid method on a liquipedia_object

"""
from typing import Callable, Optional, Union, List, Dict, Any
import parse_liquipedia_wc
from liquipedia_objects import player, team, tournament

class MethodNotFoundException(Exception):
    """Exception raised when calling an invalid method on a liquipedia_object"""

class PageTypeRegistry:
    """Class defining mapping between strings and classes"""
    _registry = {}

    @classmethod
    def register(cls, type_name: str) -> Callable:
        """
        Registers a class under a given string type name.

        Parameters
        ----------
        type_name : str
            The string identifier for the class (e.g., "player", "team").
        
        Returns
        -------
        Callable
            A decorator that registers the decorated class under the specified type name.
        """
        def inner(page_class):
            cls._registry[type_name.lower()] = page_class
            return page_class
        return inner

    @classmethod
    def get_class(cls, type_name : str) -> Optional[type]:
        """
        Retrieves the class associated with the type_name
        """
        return cls._registry.get(type_name.lower())

# Register the actual classes, not subclasses or functions
PageTypeRegistry.register("tournament")(tournament.Tournament)
PageTypeRegistry.register("team")(team.Team)
PageTypeRegistry.register("player")(player.Player)

def create_multiple_pages(game : str,page_names : List[str], page_ts : Union[List[str], str],
                        user : str ="initial python testing(github.com/louzhou)",
                        action : str= "query") -> Dict[str, Any]:
    """
        Helper function to get many pages in one api call

        Parameters
        ----------
        game: str
            The game being played
        page_names: List[str]
            The page names, found by liquipedia.com/game/(name)
        page_ts: Union[List[str], str]
            Types of pages being parsed
        user: str
            The user, as requested by liquipedia ToS
        action: str
            Whether html(action = "parse") or wikicode(action = "query") parsing should occur
        
        Returns
        -------
            Dict[str, Any]
                A dictionary mapping page names to the corresponding liquipedia_page object
    """
    page_types = page_ts if isinstance(page_ts, list) else [page_ts.lower()] * len(page_names)
    response = parse_liquipedia_wc.make_request(
            user, game, "|".join(page_names), action
        )
    objects = {}
    for name, ptype in zip(page_names, page_types):
        page_class = PageTypeRegistry.get_class(ptype)
        if page_class is None:
            raise ValueError(f"Page class for type '{ptype}' is not registered.")
        raw_str = response[name.lower().strip()]
        obj = page_class.from_raw_str(raw_str, game, name, user=user, throttle=0)
        objects[name] = obj
    return objects
