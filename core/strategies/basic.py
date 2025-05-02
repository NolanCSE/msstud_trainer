from card_lib.card import Card
from core.hand_features import evaluate_partial_hand
from card_lib.utils.mississippi_constants import RANK_ORDER

class BasicStrategy:
    def __init__(self):
        self.previous_3x = False

    def get_bet(self, hole_cards, revealed_community_cards, stage, ante=1, current_total=0, ap_revealed_community_cards={'3rd': None, '4th': None, '5th': None}):
        all_cards = hole_cards + revealed_community_cards
        features = evaluate_partial_hand(all_cards)
        num_cards = len(all_cards)

        if stage == "3rd":
            return self.handle_3rd_street(features, hole_cards, ante)

        if stage == "4th":
            return self.handle_4th_street(features, all_cards, ante)

        if stage == "5th":
            return self.handle_5th_street(features, ante)

        return "fold"

    def handle_3rd_street(self, features, hole_cards, ante):
        ranks = [c.rank for c in hole_cards]
        suits = [c.suit for c in hole_cards]

        # Rule 1: Raise 3x with any pair
        if features["pair_rank"]:
            self.previous_3x = True
            return 3 * ante

        # Rule 2: Raise 1x with at least two points
        if features["total_points"] >= 2:
            return 1 * ante

        # Rule 3: Raise 1x with 6/5 suited
        if set(ranks) == {"5", "6"} and len(set(suits)) == 1:
            return 1 * ante

        return "fold"

    def handle_4th_street(self, features, all_cards, ante):
        # Rule 1: 3x with made hand (mid pair or better)
        if features["is_made_hand"]:
            self.previous_3x = True
            return 3 * ante

        # Rule 2: 3x with royal flush draw
        if features["is_flush_draw"] and {"10", "J", "Q", "K", "A"}.issuperset(set(card.rank for card in all_cards)):
            self.previous_3x = True
            return 3 * ante

        # Rule 3: 3x with straight flush draw, no gaps, 567 or higher
        if features["is_straight_draw"] and features["is_flush_draw"] and features["straight_gaps"] == 0 and self._min_straight_rank(all_cards) >= 5:
            self.previous_3x = True
            return 3 * ante

        # Rule 4: 3x with 1-gap SF draw and at least one high card
        if features["is_straight_draw"] and features["is_flush_draw"] and features["straight_gaps"] == 1 and features["num_high_cards"] >= 1:
            self.previous_3x = True
            return 3 * ante

        # Rule 5: 3x with 2-gap SF draw and 2 high cards
        if features["is_straight_draw"] and features["is_flush_draw"] and features["straight_gaps"] == 2 and features["num_high_cards"] >= 2:
            self.previous_3x = True
            return 3 * ante

        # Rule 6: 1x with other suited 3
        if features["is_flush_draw"]:
            return 1 * ante

        # Rule 7: 1x with low pair
        if features["pair_rank"] and not features["is_made_hand"]:
            return 1 * ante

        # Rule 8: 1x with at least 3 points
        if features["total_points"] >= 3:
            return 1 * ante

        # Rule 9: 1x with straight draw, no gaps, 456 or higher
        if features["is_straight_draw"] and features["straight_gaps"] == 0 and self._min_straight_rank(all_cards) >= 4:
            return 1 * ante

        # Rule 10: 1x with straight draw, 1 gap, two mid cards
        if features["is_straight_draw"] and features["straight_gaps"] == 1 and features["num_mid_cards"] >= 2:
            return 1 * ante

        return "fold"

    def handle_5th_street(self, features, ante):
        # Rule 1: 3x with made hand
        if features["is_made_hand"]:
            self.previous_3x = True
            return 3 * ante

        # Rule 2: 3x with 4 to flush
        if features["is_flush_draw"]:
            self.previous_3x = True
            return 3 * ante

        # Rule 3: 3x with outside straight 8+
        if features["is_straight_draw"] and features["straight_gaps"] == 0 and features["num_mid_cards"] >= 3:
            self.previous_3x = True
            return 3 * ante

        # Rule 4: 1x with other straight draw
        if features["is_straight_draw"]:
            return 1 * ante

        # Rule 5: 1x with low pair
        if features["pair_rank"] and not features["is_made_hand"]:
            return 1 * ante

        # Rule 6: 1x with at least 4 points
        if features["total_points"] >= 4:
            return 1 * ante

        # Rule 7: 1x with 3 mid cards and prev 3x
        if features["num_mid_cards"] >= 3 and self.previous_3x:
            return 1 * ante

        return "fold"

    def _min_straight_rank(self, cards):
        try:
            return min(RANK_ORDER[card.rank] for card in cards if card.rank in RANK_ORDER)
        except:
            return 2
