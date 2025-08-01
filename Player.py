import parse_liquipedia
import re
from LiquipediaPage import LiquipediaPage

class Player(LiquipediaPage):
    def __init__(self, game, name, user="initial python testing(github.com/louzhou)", throttle=0):
        super().__init__(game, name, user=user, throttle=throttle)
    
    def get_info(self, infobox_name="Infobox player"):
        info_dict =  super().get_info(infobox_name)
        info_dict['team_history'] = parse_liquipedia.parse_player_team_history(info_dict['team_history']) if 'team_history' in info_dict.keys() else None
        return info_dict
    def get_gear(self):
        gear_dict = {}
        for section in self.raw_str.get_sections(include_lead=False, include_headings=True):
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
