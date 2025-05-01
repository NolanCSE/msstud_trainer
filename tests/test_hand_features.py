
import unittest
from card_lib.card import Card
from core.hand_features import evaluate_partial_hand

class TestHandFeatures(unittest.TestCase):
    def test_high_card_count(self):
        cards = [Card("Hearts", "J"), Card("Spades", "Q")]
        features = evaluate_partial_hand(cards)
        self.assertEqual(features["num_high_cards"], 2)
        self.assertEqual(features["total_points"], 4)

    def test_mid_card_and_points(self):
        cards = [Card("Clubs", "6"), Card("Diamonds", "8"), Card("Spades", "9")]
        features = evaluate_partial_hand(cards)
        self.assertEqual(features["num_mid_cards"], 3)
        self.assertEqual(features["total_points"], 3)

    def test_pair_and_made_hand(self):
        cards = [Card("Hearts", "7"), Card("Spades", "7")]
        features = evaluate_partial_hand(cards)
        self.assertEqual(features["pair_rank"], "7")
        self.assertTrue(features["is_made_hand"])

    def test_low_pair_not_made_hand(self):
        cards = [Card("Hearts", "4"), Card("Clubs", "4")]
        features = evaluate_partial_hand(cards)
        self.assertEqual(features["pair_rank"], "4")
        self.assertFalse(features["is_made_hand"])

    def test_flush_draw(self):
        cards = [Card("Hearts", "2"), Card("Hearts", "4"), Card("Hearts", "6")]
        features = evaluate_partial_hand(cards)
        self.assertTrue(features["is_flush_draw"])

    def test_straight_draw_no_gaps(self):
        cards = [Card("Clubs", "5"), Card("Hearts", "6"), Card("Spades", "7")]
        features = evaluate_partial_hand(cards)
        self.assertTrue(features["is_straight_draw"])
        self.assertEqual(features["straight_gaps"], 0)

    def test_straight_draw_with_gap(self):
        cards = [Card("Clubs", "5"), Card("Hearts", "7"), Card("Spades", "8")]
        features = evaluate_partial_hand(cards)
        self.assertTrue(features["is_straight_draw"])
        self.assertEqual(features["straight_gaps"], 1)

    def test_straight_draw_three_gaps(self):
        cards = [Card("Clubs", "5"), Card("Hearts", "8"), Card("Spades", "10")]
        features = evaluate_partial_hand(cards)
        self.assertFalse(features["is_straight_draw"])

    def test_non_straight_draw(self):
        cards = [Card("Clubs", "2"), Card("Hearts", "4"), Card("Spades", "9")]
        features = evaluate_partial_hand(cards)
        self.assertFalse(features["is_straight_draw"])

    def test_straight_draw_one_gap_four_cards(self):
        cards = [Card("Clubs", "5"), Card("Hearts", "8"), Card("Spades", "9"), Card("Diamonds", "7")]
        features = evaluate_partial_hand(cards)
        self.assertTrue(features["is_straight_draw"])
        self.assertEqual(features["straight_gaps"], 1)

if __name__ == "__main__":
    unittest.main()
