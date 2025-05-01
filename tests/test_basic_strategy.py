
import unittest
from card_lib.card import Card
from core.strategies.basic import BasicStrategy

class TestBasicStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = BasicStrategy()

    def test_3rd_street_pair(self):
        hole = [Card("Hearts", "7"), Card("Spades", "7")]
        bet = self.strategy.get_bet(hole, [], "3rd", ante=5)
        self.assertEqual(bet, 15)  # 3x ante

    def test_3rd_street_points(self):
        hole = [Card("Hearts", "Q"), Card("Spades", "9")]  # 2 + 1 = 3 points
        bet = self.strategy.get_bet(hole, [], "3rd", ante=5)
        self.assertEqual(bet, 5)  # 1x ante

    def test_3rd_street_suited_6_5(self):
        hole = [Card("Hearts", "6"), Card("Hearts", "5")]
        bet = self.strategy.get_bet(hole, [], "3rd", ante=5)
        self.assertEqual(bet, 5)

    def test_3rd_street_fold(self):
        hole = [Card("Diamonds", "2"), Card("Clubs", "4")]
        bet = self.strategy.get_bet(hole, [], "3rd", ante=5)
        self.assertEqual(bet, "fold")

    def test_4th_street_low_pair(self):
        hole = [Card("Clubs", "4"), Card("Spades", "4")]
        board = [Card("Hearts", "7")]
        bet = self.strategy.get_bet(hole, board, "4th", ante=5)
        self.assertEqual(bet, 5)

    def test_4th_street_flush_draw(self):
        hole = [Card("Hearts", "2"), Card("Hearts", "9")]
        board = [Card("Hearts", "6")]
        bet = self.strategy.get_bet(hole, board, "4th", ante=5)
        self.assertEqual(bet, 5)

    def test_5th_street_mid_pair(self):
        hole = [Card("Diamonds", "8"), Card("Clubs", "8")]
        board = [Card("Spades", "6"), Card("Hearts", "10")]
        bet = self.strategy.get_bet(hole, board, "5th", ante=5)
        self.assertEqual(bet, 15)

    def test_5th_street_fold(self):
        hole = [Card("Diamonds", "3"), Card("Clubs", "4")]
        board = [Card("Spades", "9"), Card("Hearts", "7")]
        bet = self.strategy.get_bet(hole, board, "5th", ante=5)
        self.assertEqual(bet, "fold")

if __name__ == "__main__":
    unittest.main()
