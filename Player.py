import parse_liquipedia
import parse_liquipedia_html
import re
from LiquipediaPage import LiquipediaPage
from bs4 import BeautifulSoup
from bs4.element import Tag
import pandas as pd
import mwparserfromhell as mw


class Player(LiquipediaPage):
    def __init__(self, game, name, user="initial python testing(github.com/louzhou)", throttle=0, action = "query"):
        super().__init__(game, name, user=user, throttle=throttle, action = action)

    def get_info(self, infobox_name: str = "Infobox league"):
        if self.action == "query": return self._get_info_wc(infobox_name = infobox_name)
        return self._get_info_html()
    
    def _get_info_html(self):
        info_dict = super()._get_info_html()

        #parse previous teams
        souped = BeautifulSoup(self.get_raw_str(), "html.parser")
        history_entries = parse_liquipedia_html.parse_team_history(souped)
        
        info_dict['team_history'] = pd.DataFrame(history_entries)
        return info_dict

    def _get_info_wc(self, infobox_name="Infobox player"):
        info_dict =  super().get_info(infobox_name)
        info_dict['team_history'] = parse_liquipedia.parse_player_team_history(info_dict['team_history']) if 'team_history' in info_dict.keys() else None
        return info_dict
    
    def get_gear(self):
        if self.action == "query": return self._get_gear_wc()
        return self._get_gear_html()

    def _get_gear_html(self):
        all_data = []
        souped = BeautifulSoup(self.get_raw_str(), "html.parser")
        sections = parse_liquipedia_html.get_all_under_header(souped,  "Gear_and_Settings")
        for table in sections:
            if table.get("class") and any("table" in c for c in table.get("class")):
                table = parse_liquipedia_html.parse_wikitable_hdhd(table, combine_tables= True, rm_1 = True)
                all_data.append(table)
                #print(table)
        if len(all_data) == 0:
            raise parse_liquipedia.SectionNotFoundException("Could not find gear section")
        return all_data
    
    def _get_gear_wc(self):
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
    def get_achievements(self):
        if self.action == "query": raise parse_liquipedia.SectionNotFoundException("Cannot parse achievements section using action = query, try action = parse")
        return parse_liquipedia_html.get_achievements(self.action, BeautifulSoup(self.get_raw_str()))

        
