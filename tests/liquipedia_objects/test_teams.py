"""Testing the team class"""
import unittest
from pathlib import Path
import pandas as pd
from ggpyscraper.liquipedia_objects import team
from ggpyscraper import parse_multiple_liquipedia_pages

GAME = "counterstrike"
TEAMS = ['Evil_Geniuses.ca', 'G2_Esports']
test = team.Team(game = "counterstrike", name = "G2_Esports",
                 action = "html", user = "ggpyparser-testing(github.com/Lou-Zhou)")
#get_info, news, roster, organization, results(achievements), results(recent matches)
#WC: 26, 70, 69, 24, none, none
#HTML: 10, 70, 69, 24, 10, 10

#get_info, news, roster, organization, results(achievements), results(recent matches)
#WC: 12, 2, 9, 1, none, none
#HTML: 6, 2, 9, 1, 4, 10
INFOS_wc = dict(zip(TEAMS, [12, 26]))
INFOS_html = dict(zip(TEAMS, [6, 10]))

NEWS = dict(zip(TEAMS, [2, 71]))

ROSTER = dict(zip(TEAMS, [9, 69]))
ORGANIZATION = dict(zip(TEAMS, [1, 24]))
ACHIEVEMENTS = dict(zip(TEAMS, [4, 10]))
RECENT_MATCHES = dict(zip(TEAMS, [10, 10]))


BASE_PATH = Path("tests/assets/team")
class Testteams(unittest.TestCase):
    """Test the team class"""

    @classmethod
    def setUpClass(cls):
        # Build wikicode-backed Tournament objects (one network call batching page names)
        cls.all_teams_wikicode = parse_multiple_liquipedia_pages.create_multiple_pages(
            game=GAME, page_names=TEAMS, page_ts="team",
            user = "ggpyparser-testing(github.com/Lou-Zhou)"
        )

        # Build HTML-backed team objects from local fixtures
        cls.all_teams_html = {}
        for t_name in TEAMS:
            path = BASE_PATH / f"{t_name.replace('/', '_')}.txt"
            with path.open("r", encoding="utf-8") as f:
                raw_html = f.read()
            t_obj = team.Team.from_raw_str(
                name=t_name, game=GAME, action="html",
                response=raw_html, user = "ggpyparser-testing(github.com/Lou-Zhou)"
            )
            cls.all_teams_html[t_name] = t_obj
    def setup_test_teams(self, teams,
                               ground_truths, method_name, mode="wikicode", both = False,
                               key = None):
        """Sets up and runs tests for TEAMS."""
        team_dict = self.all_teams_wikicode if mode == "wikicode" else self.all_teams_html
        results_tournament = {name: t_obj for name, t_obj in
                            team_dict.items() if
                            name in teams}

        for to_name, to_obj in results_tournament.items():
            with self.subTest(name=to_name, mode=mode):
                method = getattr(to_obj, method_name)
                results = method()
                if key is not None:
                    results = len(results.get(key))
                elif isinstance(results, list):
                    results = len(results)
                elif isinstance(results, dict):
                    results = len(results)
                elif isinstance(results, pd.DataFrame):
                    results = results.shape if both else results.shape[0]
                expected_size = ground_truths[to_name]
                self.assertEqual(
                    results,
                    expected_size,
                    msg=f"{to_name}, {mode}",
                )
    def test_get_info_html(self):
        """Tests the get_info method for HTML"""
        self.setup_test_teams(TEAMS, INFOS_html, "get_info", mode="html")
    def test_get_info_wikicode(self):
        """Tests the get_info method for wikicode"""
        self.setup_test_teams(TEAMS, INFOS_wc, "get_info", mode="wikicode")
    #OUTDATED:
    #def test_get_news_html(self):
    #    """Tests the get_news method for HTML"""
        self.setup_test_teams(TEAMS, NEWS, "get_news", mode="html")
    def test_get_news_wikicode(self):
        """Tests the get_news method for wikicode"""
        self.setup_test_teams(TEAMS, NEWS, "get_news", mode="wikicode")
    def test_get_roster_html(self):
        """Tests the get_players method for HTML"""
        self.setup_test_teams(TEAMS, ROSTER, "get_players", mode="html")
    def test_get_roster_wikicode(self):
        """Tests the get_players method for wikicode"""
        self.setup_test_teams(TEAMS, ROSTER, "get_players", mode="wikicode")
    def test_get_organization_html(self):
        """Tests the get_organization method for HTML"""
        self.setup_test_teams(TEAMS, ORGANIZATION, "get_organization", mode="html")
    def test_get_organization_wikicode(self):
        """Tests the get_organization method for wikicode"""
        self.setup_test_teams(TEAMS, ORGANIZATION, "get_organization", mode="wikicode")
    def test_get_achievements_html(self):
        """Tests the get_results method for HTML"""
        self.setup_test_teams(TEAMS, ACHIEVEMENTS, "get_results", mode="html",
                              both = True, key = "Achievements")
    def test_get_recent_matches_html(self):
        """Tests the get_results method for HTML"""
        self.setup_test_teams(TEAMS, RECENT_MATCHES, "get_results", mode="html",
                              both = True, key = "Recent Matches")

if __name__ == "__main__":
    unittest.main()
