import mwparserfromhell as mw
import parse_liquipedia
import pandas as pd
import re
from LiquipediaPage import LiquipediaPage
from parse_liquipedia import SectionNotFoundException
#TODO: Future work - add support for ability to query multiple tournaments into one 


class Tournament(LiquipediaPage):
    def __init__(self, game, name, user="initial python testing(github.com/louzhou)", throttle=0):
        super().__init__(game, name, user=user, throttle=throttle)
        
    def get_matches(self):
        sections = []
        parses = []
        for section in self.raw_str.get_sections(include_lead=False, include_headings=True):
            #exists probably a cleaner solution to find relevant headers
            heading = section.filter_headings()[0].title.strip().lower() 
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
            lowest_sections = parse_liquipedia.get_lowest_subsections(parse)
            
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
    
    def get_info(self, infobox_name = "Infobox league"): 
        return super().get_info(infobox_name)

    def get_participants(self):
        team_dfs = []    
        for section in self.raw_str.get_sections(include_lead=False, include_headings=True):
            heading = section.filter_headings()[0].title.strip().lower()
            if heading == "participants":
                #if multiple subsections of teams
                lowest_section = parse_liquipedia.get_lowest_subsections(section)
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
   
    