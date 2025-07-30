import regex as re
from datetime import datetime
import mwparserfromhell as mw
import pandas as pd
import numpy as np
# functions to parse liquipedia data

def parse_team_name(name):
    return re.search(r"\{\{TeamOpponent\|([^}|]+)", name)[1]

def parse_map(map):
    wikicode = mw.parse(map)

    template = wikicode.filter_templates()[0]

    map_data = {param.name.strip(): param.value.strip_code().strip() for param in template.params}
    if len(map_data) == 0:
        raise Exception(f"No maps were found in {map}")
    return map_data


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

def parseTeam(text):
    #get name
    match = re.search(r"\|\s*team\s*=\s*([^|}]+)", text)
    team = match.group(1).strip() if match else None
        
    #get qualification method
    match = re.search(r"\|\s*qualifier\s*=\s*([^|}]+)", text)
    qualifier =  match.group(1).strip("/[") if match else None

    match = re.findall(r"\b(p\d+|c)\s*=\s*([^\s|}]+)", text)
    players = {k: v for k, v in match} if match else None
    #find dnps
    match = re.search(r"\b(xxdnp)\s*=\s*(true)\b", text)
    dnps = (value for key, value in  match.groups()) if match else ()
        
    team_dict = {"team": team, "qualifier": qualifier, "dnps": dnps}
    team_dict.update(players)
    return pd.Series(team_dict)

#get broadcast talent
def parseBroadcaster(text):
    #get broadcast role
    match = re.search(r"\|\s*position\s*=\s*([^|}]+)", text)
    position = match.group(1).strip() if match else None
        
    #get broadcast language
    match = re.search(r"\|\s*lang\s*=\s*([^|}]+)", text)
    language =  match.group(1).strip() if match else None

    match = re.findall(r"\|b\d+\s*=\s*([^\|}]+)", text)
    names = [m.strip() for m in match]

    return pd.DataFrame(data = {
        "name": names,
        "language": [language] * len(names),
        "position": [position] * len(names)
    })
def parse_prizes(text):
    slots_raw = re.findall(r"\{\{Slot\|([^}]*)\}\}", str(text))

    #slots = [(slot.split("=")[0], slot.split("=")[1]) for slot in slots]
    slots_tuples = [
        re.findall(r"(\w+)=([^|]+)", slot)  # captures key and value
        for slot in slots_raw
    ]
    match = re.findall(r"(qualifies\d+name)=([^\|}]+)", str(text))
    #build maping of future qualifying events
    qualifications = {re.sub(r"qualifies(\d+)name", r"qualified\1", k): v.strip() for k, v in match}
    qualifications.update({"none":None})
    dict_rows = []
    for pairs in slots_tuples:
        slot_dict = dict(pairs)
        for key in list(slot_dict.keys()):
            if re.match(r"qualified\d+", key):
                slot_dict["qualifying"] = key  
                slot_dict.pop('key', None)

        if "qualifying" not in slot_dict:
            slot_dict["qualifying"] = "none"

        dict_rows.append(slot_dict)
    df = pd.DataFrame(dict_rows)
    df['qualifying'] = df['qualifying'].map(qualifications)
    df['count'] = df['count'].fillna(1)
    df['teams'] = np.empty((len(df), 0)).tolist()
    return df

def parse_expanded_prize_pool(text):
    match = re.findall(r"\{\{prize pool slot\b(?:[^{}]|\{\{[^{}]*\}\})*\}\}", 
                    str(text), re.DOTALL | re.IGNORECASE)
    all_placements = []
    for placement in match:
        parts = [p.strip() for p in placement.split("|") if p.strip()]

        data = {}
        team_names = []

        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                data[key.strip()] = value.strip()
            else:
                # Standalone part is likely team name
                team_name = part.strip()
                team_names.append(team_name)
        data['team'] = [team for team in team_names if "{" not in team]
        data['localprize'] = data['localprize'].strip("[") if 'localprize' in data else None
        data = {
                (k.strip("{}") if isinstance(k, str) else k): 
                (v.strip("{}") if  isinstance(v, str) else v)
                for k, v in data.items()
            }
        all_placements.append(data)
    return pd.DataFrame(all_placements)