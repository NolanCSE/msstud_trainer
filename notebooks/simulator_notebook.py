# Mississippi Stud Simulation Jupyter Notebook

# Imports
import matplotlib.pyplot as plt
import numpy as np
from card_lib.simulation.mississippi_simulator import simulate_round, MississippiStudStrategy
from card_lib.deck import Deck
from msstud_trainer.core.strategies.basic import BasicStrategy
from msstud_trainer.core.strategies.ap3 import AdvantagePlay3rdStrategy

# Simulation Parameters
ROUNDS = 10000
ANTE = 5
STRATEGY = "ap3"  # options: "basic", "ap3"

# Strategy Selection
if STRATEGY == "basic":
    strategy = BasicStrategy()
elif STRATEGY == "ap3":
    strategy = AdvantagePlay3rdStrategy()
else:
    raise ValueError("Unknown strategy")

class NotebookStrategyWrapper(MississippiStudStrategy):
    def __init__(self, strategy):
        self.strategy = strategy

    def get_bet(self, hole_cards, revealed_community_cards, stage, ante=1, current_total=0, peeked_cards=None):
        return self.strategy.get_bet(hole_cards, revealed_community_cards, stage, ante, current_total, peeked_cards)

# Run Simulation
profits = []
deck = Deck()
for _ in range(ROUNDS):
    deck.shuffle()
    sim_strategy = NotebookStrategyWrapper(strategy)
    profit = simulate_round(deck, sim_strategy, ante=ANTE)
    profits.append(profit)

# Results
profits = np.array(profits)
ev_per_hand = profits.mean()
std_dev = profits.std()
total_profit = profits.sum()

print(f"Rounds: {ROUNDS}")
print(f"EV per hand: ${ev_per_hand:.2f}")
print(f"Total Profit: ${total_profit:.2f}")
print(f"Standard Deviation: ${std_dev:.2f}")

# Plot Histogram
plt.hist(profits, bins=range(int(min(profits)), int(max(profits)) + 2), edgecolor='black')
plt.title("Distribution of Profits per Hand")
plt.xlabel("Profit per Hand")
plt.ylabel("Frequency")
plt.grid(True)
plt.show()
