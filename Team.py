import parse_liquipedia
import parse_liquipedia_html
import pandas as pd
import re
from LiquipediaPage import LiquipediaPage
from bs4 import BeautifulSoup
import mwparserfromhell as mw
class Team(LiquipediaPage):
    def __init__(self, game, name, user="initial python testing(github.com/louzhou)", throttle=0, action = "query"):
        super().__init__(game, name, user=user, throttle=throttle, action = action)
    

    def get_info(self, infobox_name = "Infobox team"): 
        info_dict =  super().get_info(infobox_name)
        for entry, text in info_dict.items():
            pattern = r"\{\{Flag\|(\w+)\}\}\s*(?:\[\[[^\|\]]+\|([^\]]+)\]\]|\[\[([^\]]+)\]\]|([A-Za-z0-9\-\s]+))"

            matches = re.findall(pattern, text)
            if len(matches) > 0:
                matches = [tuple(x for x in t if x) for t in matches]
                info_dict[entry] = [{"country": t1, "name": t2} for t1, t2 in matches]
        return info_dict

    def get_news(self):
        if self.action == "query": return self._get_news_wc()
        return self._get_news_html()

    def _get_news_html(self):
        souped = BeautifulSoup(self.get_raw_str(), "html.parser")
        timeline_data = parse_liquipedia_html.get_all_under_header(souped, "Timeline")
        tabbed_data = []
        for data in timeline_data:
            if data.get("class") and  any("tabs" in c for c in data.get("class")):
                timeline_table = parse_liquipedia_html.build_tab_map(data)
                tabbed_data.append(pd.concat([pd.DataFrame(parse_liquipedia_html.parse_single_tab(text, year)) for year, text in timeline_table.items()]))
            else:
                tabbed_data.append(pd.DataFrame(parse_liquipedia_html.parse_single_tab(data)))
        pd.concat(tabbed_data)

    def _get_news_wc(self):
        news_data = []
        parsed = mw.parse(self.raw_str)
        for section in parsed.get_sections(include_lead=False, include_headings=True):
            header = section.filter_headings()[0].title.strip().lower()
            if header == "timeline":
                year_text_map = parse_liquipedia.get_name_content_map(str(section))
                for year, text in year_text_map.items():
                    entries = text.split("\n")
                    for entry in entries:
                        data = parse_liquipedia.parse_news_str(entry)
                        if data != -1:
                            data['year'] = year
                            news_data.append(data)
        return pd.DataFrame(news_data)
    
    def get_players(self):
        if self.action == "query":
            return self._get_people("player roster")
        return self._get_people_html(id = "Player Roster")
    
    def get_organization(self):
        if self.action == "query":
            return self._get_people("organization")
        return self._get_people_html(id = "Organization")

    def _get_people_html(self, id):
    #game.find_all("div", class_ = "table-responsive")
        souped = BeautifulSoup(self.get_raw_str(), "html.parser")
        all_players = []
        for section in parse_liquipedia_html.get_all_under_header(souped, id = id):
            tab_map = parse_liquipedia_html.build_tab_map(section)
            if len(tab_map) == 0:
                all_players = all_players + parse_liquipedia_html.parse_players_raw(section, self.game)
            else:
                for game, text in tab_map.items():
                    all_players = all_players + parse_liquipedia_html.parse_players_raw(text, game)
                        #notable stand-ins:
                
                
        return pd.concat(all_players)

    def _get_people(self, header):
        all_people = []
        stand_ins = []
        parsed = mw.parse(self.raw_str)
        for section in parsed.get_sections(include_lead=False, include_headings=True):
            sec_title = section.filter_headings()[0].title.strip().lower()
            if sec_title == header:
                #get players(non standins)
                
                people = re.findall(r"\{\{Person\|((?:[^{}]|\{\{[^{}]*\}\})*)\}\}", str(section), re.DOTALL)
                for person in people:
                    person_dict = parse_liquipedia.parse_person(person)
                    if 'role' in person_dict and "abbr" in person_dict['role'].lower():
                        person_dict['role'] = re.split("[|/]", person_dict['role'])[-1].strip("}")
                    all_people.append(person_dict)
                people = re.findall(r"\{\{Stand-in\|((?:[^{}]|\{\{[^{}]*\}\})*)\}\}", str(section), re.DOTALL)
                for person in people:
                    person_dict = parse_liquipedia.parse_person(person)
                    stand_ins.append(person_dict)
        if len(stand_ins) > 0:
            return {"players": pd.DataFrame(all_people), "stand_ins": pd.DataFrame(stand_ins)}
        return pd.DataFrame(all_people)
    def get_results(self):
        if self.action == "query":
            raise parse_liquipedia.SectionNotFoundException("Cannot parse results section using action = query, try action = parse")
    
        souped = BeautifulSoup(self.get_raw_str(), "html.parser")
        timeline_data = parse_liquipedia_html.get_all_under_header(souped, "Results")
        for data in timeline_data:
            if data.get("class") and  any("tabs" in c for c in data.get("class")):
                timeline_table = parse_liquipedia_html.build_tab_map(data)
                return {k: parse_liquipedia_html.parse_wikitable_achievements(v) for k,v in timeline_table.items()}
        raise parse_liquipedia.SectionNotFoundException("Could not find results table")