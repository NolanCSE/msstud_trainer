
import random
from card_lib.deck import Deck
from core.strategies.basic import BasicStrategy
from card_lib.simulation.mississippi_simulator import MississippiStudStrategy

class HumanTrainer(MississippiStudStrategy):
    def __init__(self, strategy):
        self.strategy = strategy

    def get_bet(self, hole_cards, revealed_community_cards, stage, ante=1, current_total=0):
        print(f"\n===== {stage.upper()} STREET =====")
        print(f"Hole Cards: {hole_cards}")
        print(f"Revealed Community Cards: {revealed_community_cards}")
        print(f"Current Total Bet: {current_total}")
        print(f"Ante: {ante}")
        print("What would you do? (1/2/3 for bet × ante, f to fold): ", end="")
        user_input = input().strip().lower()
        if user_input == "f":
            user_bet = "fold"
        elif user_input in {"1", "2", "3"}:
            user_bet = int(user_input) * ante
        else:
            print("Invalid input, folding by default.")
            user_bet = "fold"

        # Get correct decision
        correct_bet = self.strategy.get_bet(hole_cards, revealed_community_cards, stage, ante, current_total)

        # Evaluate
        if user_bet == correct_bet:
            print("✅ Correct decision!")
        else:
            print(f"❌ Incorrect. Suggested bet was: {correct_bet}")

        return user_bet

def main():
    deck = Deck()
    deck.shuffle()

    strategy = BasicStrategy()
    trainer = HumanTrainer(strategy)

    from card_lib.simulation.mississippi_simulator import simulate_round

    while True:
        print("\n========== NEW HAND ==========")
        simulate_round(deck, trainer, ante=5)
        again = input("Play another? (y/n): ").strip().lower()
        if again != "y":
            break

if __name__ == "__main__":
    main()
