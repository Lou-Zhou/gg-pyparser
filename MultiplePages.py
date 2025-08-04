import parse_liquipedia
from Team import Team
from Player import Player
from Tournaments import Tournament
class MethodNotFoundException(Exception):
    pass
class PageTypeRegistry:
    _registry = {}

    @classmethod
    def register(cls, type_name):
        def inner(page_class):
            cls._registry[type_name.lower()] = page_class
            return page_class
        return inner

    @classmethod
    def get_class(cls, type_name):
        return cls._registry.get(type_name.lower())

@PageTypeRegistry.register("tournament")
class TournamentPage(Tournament):
    pass

@PageTypeRegistry.register("team")
class TeamPage(Team):
    pass

@PageTypeRegistry.register("player")
class PlayerPage(Player):
    pass

def createMultiplePages(game,page_names, page_types, user="initial python testing(github.com/louzhou)", action = "query"):
    #helper function to get many pages in one api call
    page_types = page_types if isinstance(page_types, list) else [page_types.lower()] * len(page_names)
    
    response = parse_liquipedia.make_request(
            user, game, 0, "|".join(page_names), action
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
