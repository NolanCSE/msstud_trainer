
import random
from card_lib.deck import Deck
from core.strategies.ap5 import AdvantagePlay5thStrategy
from card_lib.simulation.mississippi_simulator import MississippiStudStrategy, simulate_round
from card_lib.evaluators.mississippi import evaluate_mississippi_stud_hand

class HumanTrainer(MississippiStudStrategy):
    def __init__(self, strategy):
        self.strategy = strategy
        self.final_hand = []
        self.result = None
        self.payout = 0

    def get_bet(self, hole_cards, revealed_community_cards, stage, ante=1, current_total=0, ap_revealed_community_cards={'3rd': None, '4th': None, '5th': None}):
        print(f"\n===== {stage.upper()} STREET =====")
        print(f"Hole Cards: {hole_cards}")
        print(f"Revealed Community Cards: {revealed_community_cards}")
        print(f"AP Revealed Community Cards: {ap_revealed_community_cards}")
        print(f"Current Total Bet: {current_total}")
        print(f"Ante: {ante}")
        print("What would you do? (1/3 for bet × ante, f to fold): ", end="")
        user_input = input().strip().lower()
        if user_input == "f":
            user_bet = "fold"
        elif user_input in {"1", "3"}:
            user_bet = int(user_input) * ante
        else:
            print("Invalid input, folding by default.")
            user_bet = "fold"

        # Get correct decision
        correct_bet = self.strategy.get_bet(hole_cards, revealed_community_cards, stage, ante, current_total, ap_revealed_community_cards)

        # Evaluate
        if user_bet == correct_bet:
            print("✅ Correct decision!")
        else:
            print(f"❌ Incorrect. Suggested bet was: {correct_bet}")

        return user_bet

def main():
    deck = Deck()
    strategy = AdvantagePlay5thStrategy()
    trainer = HumanTrainer(strategy)

    while True:
        print("\n========== NEW HAND ==========")
        deck.shuffle()

        profit = simulate_round(deck, trainer, ante=5, ap_revealed_community_cards={'3rd': None, '4th': None, '5th': True})

        print(f"💰 Net payout: {profit}")

        again = input("\nPlay another? (y/n): ").strip().lower()
        if again != "y":
            break

if __name__ == "__main__":
    main()
