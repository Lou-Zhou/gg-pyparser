import mwparserfromhell as mw
from bs4 import BeautifulSoup
import regex as re
import parse_liquipedia
from bs4.element import Tag
import warnings
class UnknownParsingMethodException(Exception):
    pass
class LiquipediaPage:
    def __init__(self, game, name, user = "initial python testing(github.com/louzhou)", throttle = 0, action = "query"):
        #support for action = query only, future work for action = parse(html form)
        if action not in ["query", "parse"]:
            raise UnknownParsingMethodException("Unknown Parsing Method")
        self.user = user
        self.game = game
        self.name = name
        self.action = action
        self.throttle = throttle
        self.raw_str = self._make_request()
        

    def get_raw_str(self):
        return self.raw_str  


    def _make_request(self):
        raw_str = list(parse_liquipedia.make_request(self.user, self.game, self.throttle, self.name, self.action).values())[0]
        if self.action == "query":
            match = re.search(r"#REDIRECT\s*\[\[(.*?)\]\]", raw_str, flags=re.IGNORECASE)
            if match:
                #check if redirect is needed
                new_name = match.group(1)
                raw_str = list(parse_liquipedia.make_request(self.user, self.game, self.throttle, new_name, self.action).values())[0]
            
            return str(raw_str)
        else:
            #TODO: deal with case of html redirect
            return str(raw_str)
        
            
    def get_info(self, infobox_name: str = "Infobox league"):
        if self.action == "query":
            return self._get_info_wc(infobox_name)
        return self._get_info_html()
        

    def _get_info_html(self):
        souped = BeautifulSoup(self.get_raw_str(), "html.parser")
        infoboxes = souped.select('div[class="fo-nttax-infobox"]')
        if len(infoboxes) == 0:
            raise parse_liquipedia.SectionNotFoundException("Infobox Section not Found")
        if len(infoboxes) > 1:
            warnings.warn("Multiple infoboxes detected, taking first one found", UserWarning)
        infobox = infoboxes[0]

        rows = infobox.find_all("div", class_="infobox-cell-2 infobox-description")
        info = {}

        for row in rows:
            key = row.get_text(strip=True).rstrip(":")
            value_div = row.find_next_sibling("div")
            value = [a.get_text(strip=True) for a in value_div.find_all("a") if a.get_text(strip=True)]
            if len(value) <= 1:
                value = value_div.get_text("", strip = True)
            info[key] = value
        return info



    def _get_info_wc(self, infobox_name):
        infobox_dict = {}
        str_parsed = mw.parse(self.raw_str)
        for template in str_parsed.filter_templates():
            if template.name.matches(infobox_name):
                for param in template.params:
                    key = str(param.name).strip()
                    value = str(param.value).strip()
                    infobox_dict[key] = value
                self.name = infobox_dict['name'] if self.name is None and "name" in infobox_dict else self.name
                break
        return infobox_dict
    @classmethod
    def from_raw_str(cls, response,game = None,name = None, user="initial python testing(github.com/louzhou)", throttle=0, action = "query"):
        #alternate constructor to build from the raw string, used when parsing multiple tournaments
        obj = cls.__new__(cls)
        obj.user = user
        obj.game = game
        obj.name = name
        obj.throttle = throttle
        if action not in ["query", "action"]:
            raise UnknownParsingMethodException("Unknown Parsing Method")
        return obj