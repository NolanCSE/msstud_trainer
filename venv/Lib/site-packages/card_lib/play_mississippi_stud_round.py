
from card_lib.deck import Deck
from card_lib.simulation.mississippi_simulator import (
    simulate_round,
    HumanInputStrategy,
)

def main():
    print("🃏 Mississippi Stud - Training Mode")
    deck = Deck()
    deck.shuffle()

    strategy = HumanInputStrategy()
    ante = int(input("Enter your ante (e.g., 1, 5, 10): "))
    profit = simulate_round(deck, strategy, ante)
    print(f"Round complete. Net profit/loss: {profit} chips")

if __name__ == "__main__":
    main()
