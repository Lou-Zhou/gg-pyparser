import mwparserfromhell as mw
import time
import requests
import parse_liquipedia
import pandas as pd
import re
import json
def get_lowest_subsections(section):
    """
    Recursively gets all lowest-level subsections for a section.
    """
    subsections = section.get_sections(include_lead=False, include_headings=True)[1:]
    if not subsections:
        return [section]
    
    lowest = []
    for sub in subsections:
        lowest.extend(get_lowest_subsections(sub))
    return lowest#rm duplicates
class SectionNotFoundException(Exception):
    pass
class CouldNotReadJsonException(Exception):
    pass
class Tournament:
    def __init__(self, game, tournament_name, user = "initial python testing(github.com/louzhou)", throttle = 0):
        self.user = user
        self.game = game
        self.tournament_name = tournament_name
        self.throttle = throttle
        self.raw_str = self._make_request()
        

    def get_raw_str(self):
        return self.raw_str  


    def _make_request(self):
        headers = {
            "User-Agent": self.user,
            "Accept-Encoding": "gzip"
        }

        try:
            # Intentional throttle to comply with TOS
            time.sleep(self.throttle)

            # Network request
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
                },
                timeout=10
            )
            response.raise_for_status()  # Raises HTTPError for bad status codes



            try: 
                response = response.json()['query']['pages']
                id = list(response.keys())[0]
                return mw.parse(response[id]['revisions'][0]['slots']['main']['*'])
            except KeyError as e:
                raise CouldNotReadJsonException(f"Could not Read JSON Request Result, indicating potential input string issues: {e}")
            

        except requests.exceptions.Timeout:
            raise TimeoutError("Request to Liquipedia API timed out.")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Request to Liquipedia API failed: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error in _make_request: {e}")

    
    def get_info(self):
        infobox_dict = {}
        for template in self.raw_str.filter_templates():
            if template.name.matches("Infobox league"):
                for param in template.params:
                    key = str(param.name).strip()
                    value = str(param.value).strip()
                    infobox_dict[key] = value
                return infobox_dict
    def get_matches(self):
        sections = []
        parses = []
        for section in self.raw_str.get_sections(include_lead=False, include_headings=True):
            
            heading = section.filter_headings()[0].title.strip().lower() #probably a cleaner solution to find relevant headers
            #find all results sections
            if heading == "results":
                #results = section.get_sections(include_lead=False, include_headings=False)
                
                parse = mw.parse(section)
                
                parses.append(parse) #incase of multiple "results" sections

        games_df = []
        #for all the results sections
        for parse in parses:
            sections = parse.get_sections(include_lead=False, include_headings=True)

            # Handle single-section tournaments (no subsections)
            if not sections:
                stage = "playoffs" if "Bracket" in parse else "group_stage"
                new_games = parse_liquipedia.parse_game_groups(stage, [parse], self.game)
                new_games['stage_group'] = stage
                games_df.append(new_games)
                continue

            seen_stages = []
            lowest_sections = get_lowest_subsections(parse)
            
            for lowest in lowest_sections:

                stage = lowest.filter_headings()[0].title.strip().lower() 
                if str(lowest) in seen_stages or "{{Match" not in str(lowest):
                    continue
                seen_stages.append(str(lowest))

                match = re.search(r"\{\{[^|]+\|([^}]+)\}\}", stage, re.I)
                if match:
                    stage = match.group(1).strip().lower()

                info = lowest.get_sections(include_lead=False, include_headings=False)
                new_games = parse_liquipedia.parse_game_groups(stage, info, self.game)
                new_games['stage_group'] = stage
                games_df.append(new_games)
        if len(games_df) == 0:
            raise SectionNotFoundException("Could not find the results section on the page, ensure that the page has a results" \
            " section. If this tournament has stages, it is likely that the results section is in the stage pages")
        matches = pd.concat(games_df, ignore_index=True)
        
        return matches
    def get_participants(self):
        team_dfs = []    
        for section in self.raw_str.get_sections(include_lead=False, include_headings=True):
            heading = section.filter_headings()[0].title.strip().lower()
            if heading == "participants":
                #if multiple subsections of teams
                lowest_section = get_lowest_subsections(section)
                for lowest in lowest_section:
                    participant_stage = lowest.filter_headings()[0].title.strip().lower() 
                    pattern = r"\{\{[Tt]eam[Cc]ard(?=\n|\|).*?\}\}"
                    teams = re.findall(pattern, str(lowest), re.DOTALL)
                    #TODO: add notes parsing
                    for team in teams:
                        team_series = parse_liquipedia.parseTeam(team)
                        team_series['intro_stage'] = participant_stage
                        team_dfs.append(team_series)
        if len(team_dfs) == 0:
            raise SectionNotFoundException("Could not find participants section on the page, ensure that the page has a participants" \
            " section. If this is a stage of a larger tournament, it is likely that the participants section is in the tournament overview")
        team_dfs = pd.concat(team_dfs, axis = 1).T
        team_dfs.loc[:,'intro_stage'] = team_dfs['intro_stage'].str.strip("=")
        return team_dfs
    def get_talent(self):
        talent_stage = 1
        broadcast_df = []
        for section in self.raw_str.get_sections(include_lead=False, include_headings=True):
            heading = section.filter_headings()[0].title.strip().lower()
            if heading == "broadcast talent":
                parse = mw.parse(section)
                pattern = r"\{\{[Bb]roadcasterCard.*?\}\}"
                roles = re.findall(pattern, str(parse), re.DOTALL)
                for role in roles:
                    role_df = parse_liquipedia.parseBroadcaster(role)
                    role_df['talent_stage'] = talent_stage
                    broadcast_df.append(role_df)
                talent_stage += 1
        if len(broadcast_df) == 0:
            raise SectionNotFoundException("Could not find talent section on the page, ensure that the page has a talent" \
            "section. If this is a stage of a larger tournament, it is likely that the talent section is in the tournament overview")
        return pd.concat(broadcast_df)
    def get_prizes(self):
        prizes = []
        for section in self.raw_str.get_sections(include_headings= True, include_lead= False):
            heading = section.filter_headings()[0].title.strip().lower()
            if heading == "prize pool":
                if "prize pool start" in str(section):
                    prize_df = parse_liquipedia.parse_expanded_prize_pool(section)
                else:
                    prize_df = parse_liquipedia.parse_prizes(section)
                prizes.append(prize_df)

        return pd.concat(prizes)

class csTournament(Tournament):
    def __init__(self, tournament_name, user="initial python testing(github.com/louzhou)", throttle=0):
        super().__init__("counterstrike", tournament_name, user=user, throttle=throttle)