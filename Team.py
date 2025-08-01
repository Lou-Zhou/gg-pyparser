import parse_liquipedia
import pandas as pd
import re
from LiquipediaPage import LiquipediaPage

class Team(LiquipediaPage):
    def __init__(self, game, name, user="initial python testing(github.com/louzhou)", throttle=0):
        super().__init__(game, name, user=user, throttle=throttle)
    
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
        news_data = []
        for section in self.raw_str.get_sections(include_lead=False, include_headings=True):
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

    def _get_people(self, header):
        all_people = []
        stand_ins = []
        for section in self.raw_str.get_sections(include_lead=False, include_headings=True):
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
    
    def get_players(self):
        return self._get_people("player roster")
    
    def get_organization(self):
        return self._get_people("organization")
    
