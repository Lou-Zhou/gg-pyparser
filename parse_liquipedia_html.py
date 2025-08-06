import pandas as pd
from collections import defaultdict
from bs4.element import Tag
import regex as re
import parse_liquipedia
#parse liquipedia pages html style
def parse_bracket_recursive_html(bracket, subround_names, output = None):
    if output is None:
        output = defaultdict(list)
    closest_header = bracket.find_previous("div", class_="brkts-round-header")
    closest_header  = [subround_name.contents[0] for subround_name in closest_header]
    closest_header  = [name for name in closest_header  if str(name).lower().strip() != "qualified"]
    #recheck headers
    if set(closest_header).isdisjoint(set(subround_names)):
        #no common between original header list and now new closest header list, new header list takes over
        subround_names = closest_header

    #recursive method to parse through bracket
    names_copied = subround_names.copy()
    subbodies = []
    for child in bracket.find_all("div", recursive=False):  
        #find all brkts-round-body in the next-next level
        subbodies = subbodies + child.find_all("div", class_="brkts-round-body", recursive=False)
    matches = bracket.find_all("div", class_="brkts-round-center", recursive=False)
    last_round = names_copied.pop()
    output[last_round] = output[last_round] + matches
    for div in subbodies:
        parse_bracket_recursive_html(div, names_copied, output = output)
    return output

def parse_side_scores_html(table):
    scores_with_halves = []
    half_counter = 1
    ot_counter = 1
    
    for td in table.select("td"):
        classes = td.get("class", [])
        val = int(td.get_text(strip=True)) if td.get_text() else None
        
        if any("brkts-cs-score-color-ct" in c for c in classes) or any("brkts-cs-score-color-t" in c for c in classes):
            side = "T" if any("brkts-cs-score-color-ct" in c for c in classes) else "CT"
            label = f"Half_{half_counter}"
            if half_counter > 2:
                label = f"OT_{ot_counter}"
                ot_counter += 1
            half_counter += 1
            scores_with_halves.append((label, side, val))
        
    
    return scores_with_halves

def parse_match_html(match):
    countdown = match.find("span", class_ = "match-info-countdown")
    time = countdown.get_text() if countdown else None
    lhs_tag = match.select_one(".match-info-header-opponent-left")
    lhs_url, lhs_title = None, None
    if lhs_tag:
        lhs_url, lhs_title = lhs_tag.select_one(".name a")['href'], lhs_tag.select_one(".name a")['title']
    rhs_url, rhs_title = None, None
    rhs_tag = match.select_one(".match-info-header-opponent:not(.match-info-header-opponent-left)")
    if rhs_tag:
        rhs_url, rhs_title =  rhs_tag.select_one(".name a")['href'], rhs_tag.select_one(".name a")['title']
    games = match.find_all("div", class_ = "brkts-popup-body-element brkts-popup-body-game")
    parsed_games = []
    for game in games:
        map_tag = game.select_one("a")
        map_name = map_tag.get_text(strip=True)

        left_table = game.select_one("div[style*='direction:ltr'] table")
        left_scores = parse_side_scores_html(left_table)
        left_scores = {f"{half}_{side}": score for half, side, score in left_scores}

        right_table = game.select_one("div[style*='direction:rtl'] table")
        right_scores = parse_side_scores_html(right_table)
        right_scores = {f"{half}_{side}": score for half, side, score in right_scores}
        map_dict = {"t1": lhs_title, "t1_url": lhs_url, "t2": rhs_title, "t2_url": rhs_url, "map": map_name, 
                    "t1_scores": left_scores, "t2_scores": right_scores, "time": time}
        parsed_games.append(map_dict)

    return pd.DataFrame(parsed_games)

def get_all_under_header(str_bs4, id):
    #parses all under a specified header until a header of the same level is reached
    header = str_bs4.find("span", class_="mw-headline", id= id)
    data = []
    if header:
        header_tag = header.find_parent(re.compile("^h[1-6]$"))
        header_level = int(header_tag.name[1])  if header_tag else -1
        siblings = header_tag.find_next_siblings() if header_tag else []
        for sib in siblings:
            if isinstance(sib, Tag):
                # Check if sibling itself is a header
                if sib.name in [f"h{i}" for i in range(1, 7)]:
                    sib_level = int(sib.name[1])
                    if sib_level <= header_level:
                        break
                data.append(sib)
    return data

def parse_wikitable_hdhd(table, larger_header = True, combine_tables = False, rm_1 = False):
    """Parses a header-data-header-data wikitable - returns either:
    if larger_header is True
        A dictionary of string - list pairings mapping the larger_header name to a list of dictionaries where each entry in the list describes 
        a row in the table
    if larger_header is False
        a list of dictionaries where each entry in the list describes a row in the table
    
    """

    
    # Extract headers from the first <tr> with <th> tags
    rows = table.find_all("tr")
    total_title = ""
    if larger_header:
        total_title = rows[0].find('th')
        for tag in total_title.find_all(["sup", "small", "div"]):
            tag.decompose()
        total_title = total_title.get_text(strip=True)
        rows = rows[1:]
    prev_row_length = -1
    header_row = []
    table_data = []
    
    for row in rows:
        cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"]) if len(td.get_text(strip = True)) != 0]
        if len(cells) == prev_row_length:
            #same header
            if not (len(cells) == 1 and rm_1):
                table_data.append({header:val for header, val in zip(header_row, cells)})
        else:
            header_row = cells
            prev_row_length = len(header_row)
    if combine_tables:
        combined = {}
        for d in table_data:
            combined.update(d)
        table_data = combined

    if len(total_title) > 0: 
        table_data = {total_title: table_data}
    if isinstance(table_data, dict) and len(table_data) == 1:
        return list(table_data.values())[0]
    return table_data





def parse_wikitable_achievements(table):
    header_row = table.find("tr") 
    headers = [th.get_text(strip=True) for th in header_row.find_all("th") if th.get_text(strip = True)]

    rows = []
    for tr in table.find_all("tr")[1:]:
        if tr.get("style") == "display:none":
            continue
        
        cells = tr.find_all(["td", "th"])
        if not cells:
            continue
        cell_values = []
        for c in cells:
            a_tag = c.find("a")
            team_span = c.find("span", class_="team-template-image-icon")
            vod_span = c.find("span", class_ = "plainlinks vodlink")
            #parse team
            if team_span and a_tag and a_tag.has_attr("href"):
                team_name = a_tag.get("title", a_tag.get_text(strip=True))
                team_href = a_tag["href"]
                cell_values.append(f"{team_name} ({team_href})")
            elif vod_span and a_tag and a_tag.has_attr("href"):
                cell_values.append(a_tag['href'])
            else:
                text = c.get_text(" ", strip=True)
                if len(text) > 0: cell_values.append(text)

        if len(cell_values) > len(headers):
            cell_values[5] = f"{cell_values[5]} vs {cell_values[6]}"
            cell_values.pop(6)
        if len(cell_values) == len(headers):
            rows.append(dict(zip(headers, cell_values)))

    df_results = pd.DataFrame(rows)
    return df_results


def parse_team_history(soup_str):
    history_div = soup_str.find("div", string="History")
    history_div = history_div.find_next("div", class_="infobox-center") if history_div else None
    history_entries = []
    current_game = None  
    if isinstance(history_div, Tag):
        for element in history_div.children:
            if isinstance(element, Tag) and element.name == "b":
                game_name = element.get_text(strip=True)
                current_game = game_name

            if isinstance(element, Tag) and element.name == "div" and element.has_attr("style") and "font-size:100%" in element["style"]:
                date_div = element.find(
                        "div",
                        style=lambda v: isinstance(v, str) and "float:left" in v
                    )
                dates = date_div.get_text(strip=True) if date_div else None

                team_div = element.find(
                        "div",
                        style=lambda v: isinstance(v, str) and "float:right" in v
                    )
                team_name, team_href = None, None
                team_link = team_div.find("a") if team_div else None
                if isinstance(team_link, Tag):
                    team_name = team_link.get_text(strip=True)
                    team_href = team_link["href"] if team_link and team_link.has_attr("href") else None
                
                note_tag = team_div.find("i") if team_div else None
                note = None
                if isinstance(note_tag, Tag):
                    note = note_tag.get_text(strip=True)
                history_entries.append({
                    "game": current_game,
                    "start_date": dates.split(" –")[0].strip() if dates else None,
                    "end_date": dates.split(" –")[1].strip() if dates else None,
                    "team": team_name,
                    "link": team_href,
                    "note": note
                })
    return history_entries
            
def build_tab_map(data):
    year_map = {}
    for li in data.select(".nav-tabs li[class^='tab']"):
        year_text = li.get_text(strip=True)
        data_count = li.get("class")[0]
        if year_text != "Show All":
            num = re.findall(r'\d+', data_count)
            num = "".join(map(str, num))
            if num in year_map:
                break #found a nested tab, just break out
            year_map[num] = year_text
    year_div_map = {}
    for div in data.select(".tabs-content > div[class^='content']"):
        data_count = div.get("class")[0]
        num = re.findall(r'\d+', data_count)
        num = "".join(map(str, num))
        year = year_map.get(num)
        if year in year_div_map:
            break
        if year:
            year_div_map[year] = div
    return year_div_map

def parse_single_tab(tab, year = None):
    output = []
    entries = tab.find_all("li")
    for entry in entries:
        entry_dict = {}
        date, text = entry.get_text().split(" - ")
        entry_dict['date'] = date
        entry_dict['text'] = text
        entry_dict['year'] = year if year else entry.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"]).get_text(strip = True)
        output.append(entry_dict)
    return output


def parse_wikitable_players(table):
    player_rows = table.find_all("tr", class_ = "Player")
    data = []
    for player_row in player_rows:
        player_dict = {}
        for element in player_row.find_all("td"):
            element_class = element.get("class")[0] if element.get("class") else None
            if not element_class:
                continue
            text = element.get_text(strip = True) 
            if element_class == "Date":
                element_class, text = text.split(":")[0:2]
            if element_class:
                player_dict[element_class] = re.sub(r"\[[^\]]*\]", "", text)#remove citations
        data.append(player_dict)
                
    

    return pd.DataFrame(data)

def parse_wikitable_standins(table):
    header_row = table.find_all("tr")[1]
    headers = [th.get_text(strip=True) for th in header_row.find_all("th") if th.get_text(strip = True)]
    headers[3] = f"{headers[3]}_{headers[2]}"
    headers[4] = f"{headers[4]}_{headers[2]}"
    headers.pop(2)
    rows = []
    for tr in table.find_all("tr")[2:]:
        player_data = []
        for element in tr.find_all("td"):
            if element.find("span", class_ = "flag"):
                continue
            hyperlinks = element.find("a")

            if hyperlinks:
                text = hyperlinks['title']
            else:
                text = element.get_text(strip = True)
            if text == "None": player_data.append(text) #append extra "None" to keep columns in check if not replacing anyone
            if len(text) > 0:
                player_data.append(text)
            #if len(text) == 0: continue
            #if len(text) == 1: text = text[0]
            
            #player_data.append(text)
        rows.append(dict(zip(headers, player_data)))
    df_results = pd.DataFrame(rows)
    return df_results

def parse_players_raw(text, game):
    all_players = []
    if not text.get("class"):
        return all_players
    if 'table-responsive' in text.get("class"):
        tables = [text]
    else: tables = text.find_all("div", class_ = "table-responsive")
    for table in tables:
        if "notable temporary stand-ins" in table.get_text().lower():
            player_df = parse_wikitable_standins(table)
            player_df['status'] = 'standin'
        else:
            #print(table)
            player_df = parse_wikitable_players(table)
            player_df['status'] = table.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"]).get_text(strip = True) if table.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"]) else None
        player_df['game'] = game
        all_players.append(player_df)
    return all_players

def get_achievements(action, bs4_str):
    if action == "query":
        raise parse_liquipedia.SectionNotFoundException("Cannot find results using a wikicode parsing method, use the html parsing instead")
    all_data = []
    achievements_section = get_all_under_header(bs4_str, "Achievements")
    for section in achievements_section:
        if section.get("class") and any("table" in c for c in section.get("class")):
            table = parse_wikitable_achievements(section)
            all_data.append(table)
    if len(all_data) == 1: return all_data[0]
    if len(all_data) == 0: raise parse_liquipedia.SectionNotFoundException("Could not find results section")
    return all_data