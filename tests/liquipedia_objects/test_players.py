"""Testing the Player class"""
import unittest
from pathlib import Path
import pandas as pd
from ggpyscraper.liquipedia_objects import player
from ggpyscraper import parse_multiple_liquipedia_pages

GAME = "counterstrike"
PLAYERS = ['Autimatic', 'Stewie2K']
INFOS_wc = dict(zip(PLAYERS, [22, 24]))
INFOS_html = dict(zip(PLAYERS, [10, 11]))

GEAR_html = dict(zip(PLAYERS, [1,3]))

GEAR_wc = dict(zip(PLAYERS, [2,4]))
GEAR_CROSSHAIR_html = dict(zip(PLAYERS, [9,9]))

GEAR_CROSSHAIR_wc = dict(zip(PLAYERS, [3,3]))

TEAM_HISTORY = dict(zip(PLAYERS, [13, 12]))

ACHIEVEMENTS = dict(zip(PLAYERS, [10, 10]))

BASE_PATH = Path("tests/assets/player")
class TestPlayers(unittest.TestCase):
    """Test the Player class"""

    @classmethod
    def setUpClass(cls):
        # Build wikicode-backed Tournament objects (one network call batching page names)
        cls.all_players_wikicode = parse_multiple_liquipedia_pages.create_multiple_pages(
            game=GAME, page_names=PLAYERS, page_ts="player"
        )

        # Build HTML-backed player objects from local fixtures
        cls.all_players_html = {}
        for t_name in PLAYERS:
            path = BASE_PATH / f"{t_name.replace('/', '_')}.txt"
            with path.open("r", encoding="utf-8") as f:
                raw_html = f.read()
            t_obj = player.Player.from_raw_str(
                name=t_name, game=GAME, action="html", response=raw_html
            )
            cls.all_players_html[t_name] = t_obj
    def setup_test_players(self, players,
                               ground_truths, method_name, mode="wikicode", both = False,
                               key = None):
        """Sets up and runs tests for players."""
        player_dict = self.all_players_wikicode if mode == "wikicode" else self.all_players_html
        results_tournament = {name: t_obj for name, t_obj in
                            player_dict.items() if
                            name in players}

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
    def test_info_wc(self):
        """Validate info counts using WC parse."""
        self.setup_test_players(PLAYERS, INFOS_wc,
                                    "get_info", mode="wikicode")
    def test_info_html(self):
        """Validate info counts using HTML parse."""
        self.setup_test_players(PLAYERS, INFOS_html,
                                    "get_info", mode="html")
    def test_gear_html(self):
        """Validate gear counts using HTML parse."""
        self.setup_test_players(PLAYERS, GEAR_html, "get_gear", mode="html")
    def test_gear_wc(self):
        """Validate gear counts using WC parse."""
        self.setup_test_players(PLAYERS, GEAR_wc, "get_gear", mode="wikicode")
    def test_gear_crosshair_html(self):
        """Validate gear crosshair counts using HTML parse."""
        self.setup_test_players(PLAYERS, GEAR_CROSSHAIR_html, "get_gear",
                                mode="html", key = "Crosshair Settings")
    def test_gear_crosshair_wikicode(self):
        """Validate gear crosshair counts using wikicode parse."""
        self.setup_test_players(PLAYERS, GEAR_CROSSHAIR_wc, "get_gear",
                                 mode="wikicode", key = "Crosshair")
    def test_team_history_wc(self):
        """Validate team history counts using WC parse."""
        self.setup_test_players(PLAYERS, TEAM_HISTORY, "get_info",
                                mode="wikicode", key = "team_history")
    def test_team_history_html(self):
        """Validate team history counts using HTML parse."""
        self.setup_test_players(PLAYERS, TEAM_HISTORY, "get_info",
                                mode="html", key = "team_history")
    def test_achievements_html(self):
        """Validate achievements counts using HTML parse."""
        self.setup_test_players(PLAYERS, ACHIEVEMENTS, "get_achievements", mode="html")
if __name__ == "__main__":
    unittest.main()
