
import argparse
import statistics
from card_lib.deck import Deck
from core.strategies.basic import BasicStrategy
from card_lib.simulation.mississippi_simulator import MississippiStudStrategy, simulate_round
from analysis.bankroll_math import risk_of_ruin

STRATEGIES = {
    "basic": BasicStrategy,
    # "ap3": AP3Strategy,
    # "ap5": AP5Strategy
}

class SimulatedStrategy(MississippiStudStrategy):
    def __init__(self, strategy):
        self.strategy = strategy

    def get_bet(self, hole_cards, revealed_community_cards, stage, ante=1, current_total=0):
        return self.strategy.get_bet(hole_cards, revealed_community_cards, stage, ante, current_total)

def run_simulation(strategy_name, rounds, ante, bankroll):
    strategy_class = STRATEGIES.get(strategy_name)
    if not strategy_class:
        raise ValueError(f"Unknown strategy: {strategy_name}")

    strategy = strategy_class()
    wrapper = SimulatedStrategy(strategy)
    deck = Deck()

    profits = []
    for _ in range(rounds):
        deck = Deck()
        deck.shuffle()
        profit = simulate_round(deck, wrapper, ante=ante)
        profits.append(profit)

    ev = sum(profits) / rounds
    stdev = statistics.stdev(profits) if len(profits) > 1 else 0
    win_rate = sum(1 for p in profits if p > 0) / rounds
    loss_rate = sum(1 for p in profits if p < 0) / rounds
    push_rate = 1.0 - win_rate - loss_rate
    ror = risk_of_ruin(ev, stdev, bankroll)

    print(f"Strategy: {strategy_name}")
    print(f"Rounds: {rounds}")
    print(f"Ante: {ante}")
    print(f"EV per hand: {ev:.2f}")
    print(f"Standard Deviation: {stdev:.2f}")
    print(f"Win Rate: {win_rate:.1%}")
    print(f"Loss Rate: {loss_rate:.1%}")
    print(f"Push Rate: {push_rate:.1%}")
    print(f"Risk of Ruin (bankroll = ${bankroll:.0f}): {ror:.2%}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mississippi Stud Strategy Simulation")
    parser.add_argument("--strategy", type=str, default="basic", help="Strategy name (default: basic)")
    parser.add_argument("--rounds", type=int, default=10000, help="Number of rounds to simulate")
    parser.add_argument("--ante", type=int, default=5, help="Ante bet per hand")
    parser.add_argument("--bankroll", type=float, default=500, help="Initial bankroll for risk of ruin calculation")
    args = parser.parse_args()

    run_simulation(args.strategy, args.rounds, args.ante, args.bankroll)
