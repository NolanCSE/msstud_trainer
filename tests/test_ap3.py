
import unittest
from core.strategies.ap3 import AdvantagePlay3rdStrategy
from card_lib.card import Card

class TestAdvantagePlay3rdStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = AdvantagePlay3rdStrategy()

    def test_made_hand_triggers_3x(self):
        # Example: Three of a kind
        hole = [Card("♠", "9"), Card("♦", "9")]
        hole_card = [Card("♣", "9")]
        bet = self.strategy.get_bet(hole, [], "3rd", ante=5, ap_revealed_community_cards={'3rd': hole_card, '4th': None, '5th': None})
        self.assertEqual(bet, 15)

    def test_flush_with_high_card_triggers_1x(self):
        hole = [Card("♠", "A"), Card("♠", "9")]
        flop = [Card("♠", "3")]
        bet = self.strategy.get_bet(hole, [], "3rd", ante=5, ap_revealed_community_cards={'3rd': flop, '4th': None, '5th': None})
        self.assertEqual(bet, 5)

    def test_weak_hand_folds(self):
        hole = [Card("♠", "3"), Card("♦", "7")]
        flop = [Card("♣", "9")]
        bet = self.strategy.get_bet(hole, [], "3rd", ante=5, ap_revealed_community_cards={'3rd': flop, '4th': None, '5th': None})
        self.assertEqual(bet, "fold")

    def test_low_pair_triggers_1x(self):
        hole = [Card("♠", "4"), Card("♦", "4")]
        flop = [Card("♣", "9")]
        bet = self.strategy.get_bet(hole, [], "3rd", ante=5, ap_revealed_community_cards={'3rd': flop, '4th': None, '5th': None})
        self.assertEqual(bet, 5)

    def test_straight_flush_draw_high_triggers_3x(self):
        hole = [Card("♠", "6"), Card("♠", "7")]
        flop = [Card("♠", "8")]
        bet = self.strategy.get_bet(hole, [], "3rd", ante=5, ap_revealed_community_cards={'3rd': flop, '4th': None, '5th': None})
        self.assertEqual(bet, 15)

if __name__ == "__main__":
    unittest.main()
