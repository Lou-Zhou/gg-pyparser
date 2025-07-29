import mwparserfromhell as mw
import time
import requests
import parse_liquipedia
import pandas as pd
import re
class Tournament:
    def __init__(self, game, tournament_name, user = "initial python testing(github.com/louzhou)", throttle = 0):
        self.user = user
        self.game = game
        self.tournament_name = tournament_name
        self.throttle = throttle
        self.html_string = self._make_request()
        

    def get_raw_html(self):
        return self.html_string    
    
    def _make_request(self):
        headers = {
            "User-Agent": self.user,
            "Accept-Encoding": "gzip"
        }
        #intentional throttle to keep with terms and conditions
        time.sleep(self.throttle)
        response = requests.get(
            f"https://liquipedia.net/{self.game}/api.php",
            headers=headers,
            params={
                "action": "query",
                "prop": "revisions",
                "rvprop": "content",
                "titles": self.tournament_name,
                "rvslots": "main",
                "format": "json"
            }
        )
        response = response.json()['query']['pages']
        id = list(response.keys())[0]
        return mw.parse(response[id]['revisions'][0]['slots']['main']['*'])
    
    def get_info(self):
        infobox_dict = {}
        for template in self.html_string.filter_templates():
            if template.name.matches("Infobox league"):
                for param in template.params:
                    key = str(param.name).strip()
                    value = str(param.value).strip()
                    infobox_dict[key] = value
                return infobox_dict
    def get_matches(self):
        sections = []
        parses = []
        for section in self.html_string.get_sections(include_lead=False, include_headings=True):
            heading = section.filter_headings()[0].title.strip().lower()
            if heading == "results":
                results = section.get_sections(include_lead=False, include_headings=False)
                
                parse = mw.parse(results)
                
                parses.append(parse) #incase of multiple "results" sections
                added_sections = [section.filter_headings()[0].title.strip().lower()  for section in parse.get_sections(include_lead=False, include_headings=True)]
                if len(added_sections) > 0: sections = sections + added_sections

        games_df = []
        #there is definitely a cleaner way to do this...
        groups =  [item for item in set(sections) if 
                   re.search(r"group\s+[a-z]\b(?!\s+\w)", item) or "playoffs" in item or re.search(r"round\s+[1-9]\b(?!\s+\w)", item) or
                   "play-in stage" in item]

        for parse in parses:
            sections = parse.get_sections(include_lead=False, include_headings=True)
            if len(sections) == 0:#if singular part / match(usually showmatch) / weird format like Blast Bounty
                stage = "playoffs" if "Bracket" in parse else "group_stage"

                new_games = parse_liquipedia.parse_game_groups(stage, [parse], self.game)
                new_games['stage_group'] = stage
                games_df.append(new_games)
                continue
            for section in parse.get_sections(include_lead=False, include_headings=True):
                stage = section.filter_headings()[0].title.strip().lower()
                if stage in groups:
                    info = section.get_sections(include_lead=False, include_headings=False)
                    match = re.search(r"\{\{[^|]+\|([^}]+)\}\}", stage, re.I)
                    if match:
                        stage = match.group(1).strip().lower()
                    new_games = parse_liquipedia.parse_game_groups(stage, info, self.game)
                    new_games['stage_group'] = stage
                    games_df.append(new_games)
        matches = pd.concat(games_df, ignore_index=True)
        #bandaid fix - TODO - look into this duplication problem for swiss stage matches and when the results are at different levels(e.g. showmatch at level 1 but actual tournament at level 3)       
        return matches.drop_duplicates(subset=matches.columns.difference(['stage_group'])) 

class csTournament(Tournament):
    def __init__(self, tournament_name, user="initial python testing(github.com/louzhou)", throttle=0):
        super().__init__("counterstrike", tournament_name, user=user, throttle=throttle)