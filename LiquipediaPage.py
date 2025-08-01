import mwparserfromhell as mw
import time
import requests
import regex as re
import parse_liquipedia

class LiquipediaPage:
    def __init__(self, game, name, user = "initial python testing(github.com/louzhou)", throttle = 0):
        self.user = user
        self.game = game
        self.name = name
        self.throttle = throttle
        self.raw_str = self._make_request()
        

    def get_raw_str(self):
        return self.raw_str  


    def _make_request(self):
        raw_str = list(parse_liquipedia.make_request(self.user, self.game, self.throttle, self.name).values())[0]
        match = re.search(r"#REDIRECT\s*\[\[(.*?)\]\]", raw_str, flags=re.IGNORECASE)
        if match:
            #check if redirect is needed
            new_name = match.group(1)
            raw_str = parse_liquipedia.make_request(self.user, self.game, self.throttle, new_name)
        return mw.parse(raw_str)
        
            

    def get_info(self, infobox_name):
        infobox_dict = {}
        for template in self.raw_str.filter_templates():
            if template.name.matches(infobox_name):
                for param in template.params:
                    key = str(param.name).strip()
                    value = str(param.value).strip()
                    infobox_dict[key] = value
                self.name = infobox_dict['name'] if self.name is None and "name" in infobox_dict else self.name
                break
        return infobox_dict
    @classmethod
    def from_raw_str(cls, response,game = None,name = None, user="initial python testing(github.com/louzhou)", throttle=0):
        #alternate constructor to build from the raw string, used when parsing multiple tournaments
        obj = cls.__new__(cls)
        obj.user = user
        obj.game = game
        obj.name = name
        obj.throttle = throttle
        obj.raw_str = mw.parse(response)
        return obj