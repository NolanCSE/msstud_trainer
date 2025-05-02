
from card_lib.card import Card
from core.hand_features import evaluate_partial_hand

class AdvantagePlay5thStrategy:
    def __init__(self):
        self.last_bet = None  # for repeating bet on 4th street

    def get_bet(self, hole_cards, revealed_community_cards, stage, ante=1, current_total=0, ap_revealed_community_cards={'3rd': None, '4th': None, '5th': None}):
        cards = hole_cards + revealed_community_cards

        # Makes the hand evaluation and thus decision making depend upon the revealed flop card the AP got a peek at
        if stage == "3rd" or stage == "4th" or stage == "5th":
            cards.append(ap_revealed_community_cards['5th'])

        features = evaluate_partial_hand(cards)

        if stage == "3rd":
            return self.handle_ap5_flop_stage(features, ante)

        if stage == "4th":
            return self.handle_ap5_turn_stage(features, ante)  # repeat the 3rd street bet, per strategy

        if stage == "5th":
            return self.handle_ap5_river_stage(features, ante)

        return "fold"

    def handle_ap5_flop_stage(self, features, ante):
        # Raise (3x, 3x)
        is_sf = features["is_straight_draw"] and features["is_flush_draw"]

        if features["is_made_hand"]:
            self.last_bet = 3 * ante
            return self.last_bet
        if is_sf and features["straight_gaps"] == 0 and features["min_straight_rank"] >= 5:
            self.last_bet = 3 * ante
            return self.last_bet
        if is_sf and features["straight_gaps"] == 1 and features["num_high_cards"] >= 1:
            self.last_bet = 3 * ante
            return self.last_bet
        if is_sf and features["straight_gaps"] == 2 and features["num_high_cards"] >= 2:
            self.last_bet = 3 * ante
            return self.last_bet

        # Raise (1x, 1x)
        if features["pair_rank"] and not features["is_made_hand"]:
            self.last_bet = 1 * ante
            return self.last_bet
        if is_sf and features["straight_gaps"] == 0 and features["min_straight_rank"] <= 4:
            self.last_bet = 1 * ante
            return self.last_bet
        if is_sf and features["straight_gaps"] == 1 and features["num_high_cards"] == 0:
            self.last_bet = 1 * ante
            return self.last_bet
        if is_sf and features["straight_gaps"] == 2 and features["num_high_cards"] <= 1:
            self.last_bet = 1 * ante
            return self.last_bet
        if features["is_straight_draw"] and features["straight_gaps"] == 0 and features["min_straight_rank"] >= 3:
            self.last_bet = 1 * ante
            return self.last_bet
        if features["is_straight_draw"] and features["straight_gaps"] == 1 and features["min_straight_rank"] >= 3:
            self.last_bet = 1 * ante
            return self.last_bet
        if features["is_straight_draw"] and features["straight_gaps"] == 2 and features["contains_8_or_higher"] >= 1:
            self.last_bet = 1 * ante
            return self.last_bet
        if features["num_high_cards"] >= 2:
            self.last_bet = 1 * ante
            return self.last_bet
        if features["num_high_cards"] >= 1 and features["num_mid_cards"] >= 1:
            self.last_bet = 1 * ante
            return self.last_bet
        if features["is_flush_draw"] and features["num_high_cards"] >= 1:
            self.last_bet = 1 * ante
            return self.last_bet

        self.last_bet = "fold"
        return "fold"
    
    def handle_ap5_turn_stage(self, features, ante):
        if features["is_made_hand"]:
            self.last_bet = 3 * ante
            return self.last_bet
        if features["is_flush_draw"]:
            self.last_bet = 3 * ante
            return self.last_bet
        if features["is_straight_draw"] and features["straight_gaps"] == 0 and features["min_straight_rank"] >= 5:
            self.last_bet = 3 * ante
            return self.last_bet
        if features["is_straight_draw"] and features["straight_gaps"] == 0 and features["min_straight_rank"] < 5:
            self.last_bet = 1 * ante
            return self.last_bet
        if features["is_straight_draw"] and features["straight_gaps"] == 1:
            self.last_bet = 1 * ante
            return self.last_bet
        if features["num_high_cards"] >= 2:
            self.last_bet = 1 * ante
            return self.last_bet
        if features["num_high_cards"] >= 1 and features["num_mid_cards"] >= 3:
            self.last_bet = 1 * ante
            return self.last_bet
        if features["pair_rank"] and not features["is_made_hand"]:
            self.last_bet = 1 * ante
            return self.last_bet
        
        self.last_bet = "fold"
        return "fold"
        
            
    def handle_ap5_river_stage(self, features, ante):
        if features["is_made_hand"]:
            return 3 * ante

        return "fold"
