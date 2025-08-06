import mwparserfromhell as mw
import parse_liquipedia
import parse_liquipedia_html
import pandas as pd
import re
from LiquipediaPage import LiquipediaPage
from parse_liquipedia import SectionNotFoundException
from bs4 import BeautifulSoup
from bs4.element import Tag



class Tournament(LiquipediaPage):
    def __init__(self, game, name, user="initial python testing(github.com/louzhou)", throttle=0, action = "query"):
        super().__init__(game, name, user=user, throttle=throttle, action = action)
        
    def get_info(self, infobox_name = "Infobox league"): 
        return super().get_info(infobox_name)

    def _get_matches_wc(self):
        sections = []
        parses = []
        str_parsed = mw.parse(self.raw_str)
        headings = [heading.title.strip().lower()  for heading in str_parsed.filter_headings()]
        results_sections = ['results'] if "results" in headings else ["group stage", "playoffs"]
        for section in str_parsed.get_sections(include_lead=False, include_headings=True):
            #exists probably a cleaner solution to find relevant headers
            heading = section.filter_headings()[0].title.strip().lower() 
            #find all results sections
            
            
            if heading in results_sections:
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
    
    def _get_matches_html(self):
        #get matchlists
        souped = BeautifulSoup(self.get_raw_str(), "html.parser")
        matchlists = souped.select(
        "div.general-collapsible.brkts-matchlist"
        )
        all_matches = []
        for matchlist in matchlists:
            header = matchlist.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"])
            header = header.get_text().split("[")[0] if header else None
            title = matchlist.select("div.brkts-matchlist-title")[0].get_text().replace(" Show Hide", "")
            matches = matchlist.find_all("div", class_ = "brkts-popup brkts-match-info-popup")
            for match in matches:
                parsed = parse_liquipedia_html.parse_match_html(match)
                parsed['stage'] = header
                parsed['substage'] = title
                all_matches.append(parsed)
        #parse brackets
        brackets = souped.select('div[class="brkts-bracket"]')
        for round in brackets:
            header = round.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"])
            header = header.get_text().split("[")[0] if header else None
            subround_names = round.select('div[class="brkts-header brkts-header-div"]')

        
            subbrackets = round.find_all("div", class_="brkts-round-body", recursive = False)
            for subbracket in subbrackets:
                closest_header = subbracket.find_previous("div", class_="brkts-round-header")
                subround_names = [subround_name.contents[0] for subround_name in closest_header]
                subround_names = [name for name in subround_names if str(name).lower().strip() != "qualified"]
                output = parse_liquipedia_html.parse_bracket_recursive_html(subbracket, subround_names)
                for sub_round, body in output.items():
                    for match in body:
                        parsed = parse_liquipedia_html.parse_match_html(match)
                        parsed['stage'] = header
                        parsed['substage'] = sub_round
                        all_matches.append(parsed)
        #get single matches(mostly showmatches or grand-finals where the finalists are weirdly determined)
        single_matches = souped.find_all("div", class_ = "brkts-popup brkts-popup brkts-match-info-flat")
        for match in single_matches:
            header = match.find_previous("span", class_="mw-headline").get_text()
            parsed = parse_liquipedia_html.parse_match_html(match)
            parsed['stage'] = header
            parsed['substage'] = header
            all_matches.append(parsed)


        if len(all_matches) > 0:
            return pd.concat(all_matches)
        raise SectionNotFoundException("No matches found")

    def get_results(self, results_name = None):
        raise AttributeError("")

    def get_matches(self):
        if self.action == "query":
            return self._get_matches_wc()
        return self._get_matches_html()
    
    def get_participants(self):
        if self.action == "query":
            return self._get_participants_wc()
        return self._get_participants_html()
    
    def _get_participants_html(self):
        raw_str = BeautifulSoup(self.get_raw_str(), "html.parser")
        participants = []
        for team in raw_str.find_all("div", class_ = "teamcard toggle-area toggle-area-1"):
            team_dict = {}
            header = team.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"])
            header = header.get_text().split("[")[0] if header else None
            team_dict['name'] = team.find("center").get_text() if team.find("center") else None
            nums = team.find("table", class_ = "wikitable wikitable-bordered list active").find_all("tr")


            team_dict['qualification'] = team.find("td", class_ = "teamcard-qualifier").get_text() if team.find("td", class_ = "teamcard-qualifier") else None
            team_dict['stage_enter'] = header

            for num in nums:
                text = str(num.get_text()).split()
                team_dict[f"p{text[0]}"] = text[1]
            participants.append(team_dict)
        if len(participants) == 0:
            raise SectionNotFoundException("Could not find participants section")
        return pd.DataFrame(participants)
        

    def _get_participants_wc(self):
        team_dfs = []    
        str_parsed = mw.parse(self.raw_str)
        for section in str_parsed.get_sections(include_lead=False, include_headings=True):
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
        if self.action == "query": return self._get_talent_wc()
        return self._get_talent_html()
    
  

    def _get_talent_html(self):
            #no explitict talent section in html, have to scan for ids
        souped = BeautifulSoup(self.get_raw_str(), "html.parser")
        all_talent = []
        talent_section = talent_span.parent if (talent_span := souped.find("span", {"id": "Broadcast_Talent"})) else None
        #could change depending on title, look in the future
        talent_container = talent_section.find_all("div", class_="tabs-content") if talent_section else None
        template_boxes = []
        if not talent_container:
            talent_container = talent_section.find_next_sibling("div") if talent_section else None
        if isinstance(talent_container, Tag):
                template_boxes = [
                        box for box in talent_container.find_all("div", class_="template-box")
                        if not box.find("div", class_="template-box")  # deepest level check
                    ] + [box for box in talent_container.find_all("ul")]    
        if not template_boxes and talent_section:
            template_boxes = list(filter(None, [talent_section.find_next("ul")]))
        for role_box in template_boxes:
            role_title = role_box.find("b")
            if role_title:
                if not isinstance(role_box, Tag) or not isinstance(role_title, Tag):
                    raise Exception("Unable to parse role box, not a bs4 Tag")
                role_name = role_title.get_text(strip=True).rstrip(":")
                
                for li in role_box.find_all("li"):
                    text = li.get_text().split("\n")
                    if len(text) > 1:
                        continue
                    flag = li.find("a")
                    country = flag['title'] if flag else None
                    talent_roles = {}
                    match = re.search(r'\xa0([^\xa0(]+)\xa0\(([^)]+)\)', text[0])
                    if match:
                        talent_roles['displayname'] = match.group(1).strip()
                        talent_roles['fullname'] = match.group(2).strip()
                        talent_roles['country'] = country
                    talent_roles["role"] = role_name
                    all_talent.append(talent_roles)
        if len(all_talent) == 0:
            raise SectionNotFoundException("Could not find talent section")
        return pd.DataFrame(all_talent).drop_duplicates(subset="fullname", keep='last', inplace=False) 





    def _get_talent_wc(self):
        talent_stage = 1
        broadcast_df = []
        str_parsed = mw.parse(self.raw_str)
        for section in str_parsed.get_sections(include_lead=False, include_headings=True):
            heading = section.filter_headings()[0].title.strip().lower()
            if heading in ["broadcast talent", "talent"]:
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
        #because of ul and div mixing for talent, we need to do both which leads to double counting occassionally
        #might be a fix but seems difficult without sacrificing not counting some
    
    def get_prizes(self):
        if self.action == "query": return self._get_prizes_wc
        return self._get_prizes_html()

    def _get_prizes_html(self):
        souped = BeautifulSoup(self.get_raw_str(), "html.parser")
        prize_pools = souped.find_all("div", class_ = "csstable-widget collapsed general-collapsible prizepooltable")
        df_list = []
        for prize_pool in prize_pools:
            header = prize_pool.find("div", class_ = "csstable-widget-row prizepooltable-header")
            headers = [h.get_text(strip=True).lower() for h in header.select(".csstable-widget-cell")] 
            rows = []

            col_map = {idx: col_name for idx, col_name in enumerate(headers)}
            prize_rows = prize_pool.select("div.csstable-widget-row:not(.prizepooltable-header):not(.ppt-toggle-expand)")
            for row in prize_rows:
                row_dict = {}
                cells = row.select(".csstable-widget-cell")
                teams = row.find_all("div", class_ = "block-team")
                teams =  [team.get_text() for team in teams]
                #print(teams)
                current_idx = 0

                for cell in cells:
                    if not cell.find("div", class_="block-team"):
                        colname = col_map[current_idx]
                        row_dict[colname] = cell.get_text(strip=True)
                    current_idx += 1
                    #colname = col_map[idx]
                    #print(cell.get_text())
                row_dict["teams"] = teams
                rows.append(row_dict)
            df_list.append(pd.DataFrame(rows))
        if len(df_list) == 0:
            raise SectionNotFoundException("Could not find prizes section")
        return df_list[0] if len(df_list) == 1 else df_list

    def _get_prizes_wc(self):
        prizes = []
        str_parsed = mw.parse(self.raw_str)
        for section in str_parsed.get_sections(include_headings= True, include_lead= False):
            heading = section.filter_headings()[0].title.strip().lower()
            if heading == "prize pool":
                if "prize pool start" in str(section):
                    prize_df = parse_liquipedia.parse_expanded_prize_pool(section)
                else:
                    prize_df = parse_liquipedia.parse_prizes(section)
                prizes.append(prize_df)

        return pd.concat(prizes)
   
    