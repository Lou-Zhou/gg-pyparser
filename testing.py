import unittest
from Tournaments import Tournament
class TestMatchData(unittest.TestCase):

    def test_swiss(self):
        #ensure that size is as expected
        tourn = Tournament(name = "counterstrike","BLAST/Major/2025/Austin/Stage_3")
        matches = tourn.get_matches()
        self.assertEqual(matches.shape[0],59)
    
    def test_group_playoff(self):
        tourn = Tournament("FISSURE/Playground/1")
        matches = tourn.get_matches()
        self.assertEqual(matches.shape[0],83)

    def test_playoff(self):
        tourn = Tournament("BLAST/Major/2025/Austin/Playoffs")
        matches = tourn.get_matches()
        self.assertEqual(matches.shape[0],21)
    
    def test_dbl_playoff(self):
        tourn = Tournament("Intel_Extreme_Masters/2025/Dallas")
        matches = tourn.get_matches()
        self.assertEqual(matches.shape[0],89)

    def test_blast_bounty(self):
        tourn = Tournament("BLAST/Bounty/2025/Spring/Qualifier")
        matches = tourn.get_matches()
        self.assertEqual(matches.shape[0], 72)

    def test_lower_tier(self):
        tourn = Tournament(name="counterstrike", tournament_id="CCT/Season_3/Oceania/Series_1")
        matches = tourn.get_matches()
        self.assertEqual(matches.shape[0], 68)
    def test_lower_tier_2(self):
        tourn = Tournament("AGES/GO_GAME_Festival/2025").get_matches().shape[0]
        self.assertEqual(tourn, 9)

    def test_stf(self):
        tourn = Tournament("Hero_Esports/Asian_Champions_League/2025").get_matches().shape[0]
        self.assertEqual(tourn, 43)
if __name__ == '__main__':
    unittest.main()