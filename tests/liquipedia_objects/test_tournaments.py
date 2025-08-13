"""Testing the Tournament class"""
import unittest
from pathlib import Path
import pandas as pd
from ggpyscraper.liquipedia_objects import tournament
from ggpyscraper import parse_multiple_liquipedia_pages

GAME = "counterstrike"
TOURNAMENTS = [
    "BLAST/Major/2025/Austin/Stage_3",
    "FISSURE/Playground/1",
    "BLAST/Major/2025/Austin/Playoffs",
    "Intel_Extreme_Masters/2025/Dallas",
    "BLAST/Bounty/2025/Spring/Qualifier",
    "CCT/Season_3/Oceania/Series_1",
    "Hero_Esports/Asian_Champions_League/2025",
    "Intel_Extreme_Masters/2025/Dallas/North_America"
]
TOURNAMENT_TYPES = [
    "swiss", "group_playoff", "playoff", "dbl_playoff",
    "blast_bounty", "lower_tier",  "straight_to_final",
]

PRIZE_TYPES = ["cash", "cash_qual", "non-usd", "weird_blast", "qual"]
PRIZE_TOURNAMENTS = ["FISSURE/Playground/1", "AGES/GO_GAME_Festival/2025",
                     "Hero_Esports/Asian_Champions_League/2025", 
                     "BLAST/Bounty/2025/Spring", 
                     "Intel_Extreme_Masters/2025/Dallas/North_America"]
INFO_TOURNAMENTS = [TOURNAMENTS[1]]

PARTICIPANTS_TOURNAMENTS = ["Hero_Esports/Asian_Champions_League/2025", "FISSURE/Playground/1"]
TALENT_TOURNAMENTS = ["FISSURE/Playground/1", "AGES/GO_GAME_Festival/2025"]

def convert_to_dict(tournaments, values):
    """Convers two lists into a dictionary"""
    return dict(zip(tournaments, values))

PRIZE_SIZES_wc = convert_to_dict(PRIZE_TOURNAMENTS, [(6, 3), (4, 3), (8,19), (4,3), (1,4)])
PRIZE_SIZES_html = convert_to_dict(PRIZE_TOURNAMENTS, [(6, 3), (4, 4), (6,4), (4,4), (4,3)])
MATCH_SIZES = convert_to_dict(TOURNAMENTS, [59, 83, 21, 89, 72, 74, 43, 18])
#wikicode parser will get all map forfeits while html will only get one map
INFO_SIZES_wc = convert_to_dict(INFO_TOURNAMENTS, [37])
INFO_SIZES_html = convert_to_dict(INFO_TOURNAMENTS, [12])
PARTICIPANTS_SIZES = convert_to_dict(PARTICIPANTS_TOURNAMENTS, [12, 16])
TALENT_SIZES = convert_to_dict(TALENT_TOURNAMENTS, [29, 1])
BASE_PATH = Path("tests/assets/tournaments")


class TestTournaments(unittest.TestCase):
    """Test the Tournament class"""

    @classmethod
    def setUpClass(cls):
        # Build wikicode-backed Tournament objects (one network call batching page names)
        cls.all_tournaments_wikicode = parse_multiple_liquipedia_pages.create_multiple_pages(
            game=GAME, page_names=TOURNAMENTS, page_ts="tournament"
        )

        # Build HTML-backed Tournament objects from local fixtures
        cls.all_tournaments_html = {}
        for t_name in TOURNAMENTS:
            path = BASE_PATH / f"{t_name.replace('/', '_')}.txt"
            with path.open("r", encoding="utf-8") as f:
                raw_html = f.read()
            t_obj = tournament.Tournament.from_raw_str(
                name=t_name, game=GAME, action="html", response=raw_html
            )
            cls.all_tournaments_html[t_name] = t_obj
    def setup_test_tournaments(self, tournaments,
                               ground_truths, method_name, mode="wikicode", both = False):
        """Sets up and runs tests for tournaments."""
        tourn_dict = (self.all_tournaments_wikicode if
                       mode == "wikicode" else self.all_tournaments_html)
        results_tournament = {name: t_obj for name, t_obj in
                            tourn_dict.items() if
                            name in tournaments}
        for to_name, to_obj in results_tournament.items():
            with self.subTest(name=to_name, mode=mode):
                method = getattr(to_obj, method_name)
                results = method()
                if isinstance(results, list):
                    results = results[0]
                if isinstance(results, dict):
                    results = len(results)
                if isinstance(results, pd.DataFrame):
                    results = results.shape if both else results.shape[0]
                expected_size = ground_truths[to_name]
                self.assertEqual(
                    results,
                    expected_size,
                    msg=f"{to_name}, {mode}",
                )
    def test_results_wc(self):
        """Validate match counts using WC parse."""
        self.setup_test_tournaments(TOURNAMENTS, MATCH_SIZES,
                                    "get_results", mode="wikicode")

    def test_results_html(self):
        """Validate match counts using HTML parse."""
        self.setup_test_tournaments(TOURNAMENTS,  MATCH_SIZES,
                                     "get_results", mode="html")
    def test_prizes_html(self):
        """Validate prize counts using HTML parse."""
        self.setup_test_tournaments(PRIZE_TOURNAMENTS, PRIZE_SIZES_html,
                                    "get_prizes",  mode="html", both = True)
    def test_prizes_wc(self):
        """Validate prize counts using WC parse."""
        self.setup_test_tournaments(PRIZE_TOURNAMENTS, PRIZE_SIZES_wc,
                                    "get_prizes",  mode="wikicode",both = True)

    def test_info_wc(self):
        """Validate info counts using WC parse."""
        self.setup_test_tournaments(INFO_TOURNAMENTS, INFO_SIZES_wc,
                                    "get_info",  mode="wikicode")
    def test_info_html(self):
        """Validate info counts using HTML parse."""
        self.setup_test_tournaments(INFO_TOURNAMENTS, INFO_SIZES_html,
                                    "get_info",  mode="html")

    def test_participants_wc(self):
        """Validate participant counts using WC parse."""
        self.setup_test_tournaments(PARTICIPANTS_TOURNAMENTS, PARTICIPANTS_SIZES,
                                    "get_participants",  mode="wikicode")
    def test_participants_html(self):
        """Validate participant counts using HTML parse."""
        self.setup_test_tournaments(PARTICIPANTS_TOURNAMENTS, PARTICIPANTS_SIZES,
                                    "get_participants",  mode="html")

    def test_talent_wc(self):
        """Validate participant counts using WC parse."""
        self.setup_test_tournaments(TALENT_TOURNAMENTS, TALENT_SIZES,
                                    "get_talent",  mode="wikicode")
    def test_talent_html(self):
        """Validate participant counts using HTML parse."""
        self.setup_test_tournaments(TALENT_TOURNAMENTS, TALENT_SIZES,
                                    "get_talent",  mode="html")


if __name__ == "__main__":
    unittest.main()
