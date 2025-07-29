import regex as re
from datetime import datetime
import mwparserfromhell as mw
import pandas as pd
# functions to parse liquipedia data
def parse_team_name(name):
    return re.search(r"\{\{TeamOpponent\|([^}|]+)", name)[1]

def parse_date(wiki_time_str):

    tz_match = re.search(r"\{\{Abbr/([A-Z]+)\}\}", wiki_time_str)
    timezone = tz_match.group(1) if tz_match else None

    date_str = re.sub(r"\{\{.*?\}\}", "", wiki_time_str).strip()

    dt = datetime.strptime(date_str, "%B %d, %Y - %H:%M")

    return dt, timezone
def parse_map(map):
    wikicode = mw.parse(map)

    template = wikicode.filter_templates()[0]

    map_data = {param.name.strip(): param.value.strip_code().strip() for param in template.params}
    return map_data
import re

def ensure_round_unique(parsed):
    seen_keys = []
    seen_values = []
    new_parsed = []
    iter = 2
    #duplicated keys(usually from competition stage - see 2025 blast bounty spring qual), just add _{num} to end
    for key, value in parsed:
        if key in seen_keys and value not in seen_values:
            key = f"{key}_{iter}"
            iter += 1
        else:
            seen_keys.append(key)
            seen_values.append(value)
        new_parsed.append((key, value))
    return new_parsed




def parse_is_finished(finished_str):
    return finished_str == "true"
def parse_series_data(series_info, regex, cleaning_function = lambda x: x):
    parsed =re.findall(regex, str(series_info), re.DOTALL)

    #print(parsed)
    return {key: cleaning_function(value) for key, value in parsed}

def parse_series(series_info, game):
    #get games:
    pattern = r"(map\d+)\s*=\s*(\{\{Map\|.*?\}\})"
    matches = re.findall(pattern, str(series_info), re.DOTALL)
    matches = pd.DataFrame([parse_map(match_data) for match_data in matches])

    #get teams:
    pattern = r"(opponent\d+)\s*=\s*(\{\{TeamOpponent\|.*?\}\})"
    team_names = parse_series_data(series_info, pattern, parse_team_name)

    #get date:
    pattern = r"(date)=(.+?\{\{Abbr/[A-Z]+\}\})\|"
    date = parse_series_data(series_info, pattern)

    
    
    matches[['opponent_1', 'opponent_2']] = team_names['opponent1'], team_names['opponent2']

    matches['date'] = date['date'] if 'date' in date else None
    #game-specific stuff probably changes here
    if game == 'counterstrike':
        #get hltv id:
        pattern = r"(hltv)=([0-9]+)|"
        hltv_id = parse_series_data(series_info, pattern)
        matches['hltv_id'] = hltv_id['hltv'] if 'hltv' in hltv_id else None
    return matches


def parse_grouped_games(name, info, game):
    alldfs = []
    for subinfo in info:
        if isinstance(subinfo, str):
            subinfo = mw.parse(subinfo)
        for template in subinfo.filter_templates(recursive=True):
            if template.name.matches("Matchlist") or template.name.matches("SingleMatch"):
                for subtemplate in template.params:
                    if "title=" in str(subtemplate):
                        name = subtemplate.split("=")[1]
                    if "{{Match" in subtemplate or "{{SingleMatch" in subtemplate:
                        match_df = parse_series(subtemplate, game)
                        match_df['stage'] = name
                        alldfs.append(match_df)
    return alldfs

def parse_playoff_data(info, game):
    alldfs = []
    for subinfo in info:
        #first try to get stage name from the RxMxheader 
        regex = (
            r"(\|R\d+M\d+header=[^\n]+)"      #turn into tuple of (|RxMxheader=name, text)
            r"(.*?)"                          
            r"(?=\|R\d+M\d+header=|\Z)"       
        )
        if len(re.findall(regex, str(subinfo), re.DOTALL)) > 0:
            stages = parse_series_data(subinfo, regex)
            stages = {key.split("=")[1]: v for key, v in stages.items()}
        else:
            #if fails, look at <!--stage-->
            regex =  r'<!--\s*(.*?)\s*-->\s*(.*?)(?=\s*<!--\s*\w+|$)'
            stages = parse_series_data(subinfo, regex)

        for stage, text in stages.items():
            matches = re.split(r'\|R\d+M\d+=', text)
            for match in matches:
                if "{{Match" in match:
                    match_df = parse_series(match, game)
                    match_df['stage'] = stage
                    alldfs.append(match_df)
    return alldfs
def parse_game_groups(stage, info, game):
    if "Bracket" in info[0]:
        new_games =  pd.concat(parse_playoff_data(info, game))
    else:
        new_games =  pd.concat(parse_grouped_games(stage, info, game))
    return new_games