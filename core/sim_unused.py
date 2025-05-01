
import argparse
import statistics
import multiprocessing
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

def simulate_hand(args):
    strategy_class, ante, verbose = args
    strategy = strategy_class()
    wrapper = SimulatedStrategy(strategy)
    deck = Deck()
    deck.shuffle()
    return simulate_round(deck, wrapper, ante=ante)

def run_simulation(strategy_name, rounds, ante, bankroll, rounds_per_hour, verbose):
    strategy_class = STRATEGIES.get(strategy_name)
    if not strategy_class:
        raise ValueError(f"Unknown strategy: {strategy_name}")

    args_list = [(strategy_class, ante, verbose) for _ in range(rounds)]

    with multiprocessing.Pool() as pool:
        profits = []
        for i, profit in enumerate(pool.imap_unordered(simulate_hand, args_list, chunksize=100)):
            profits.append(profit)
            if verbose and (i + 1) % 1000 == 0:
                print(f"Simulated {i + 1} / {rounds} hands...")

    ev = sum(profits) / rounds
    stdev = statistics.stdev(profits) if len(profits) > 1 else 0
    win_rate = sum(1 for p in profits if p > 0) / rounds
    loss_rate = sum(1 for p in profits if p < 0) / rounds
    push_rate = 1.0 - win_rate - loss_rate
    ror = risk_of_ruin(ev, stdev, bankroll)
    ev_per_hour = ev * rounds_per_hour

    print(f"\nStrategy: {strategy_name}")
    print(f"Rounds: {rounds}")
    print(f"Ante: {ante}")
    print(f"EV per hand: ${ev:.2f}")
    print(f"Standard Deviation: ${stdev:.2f}")
    print(f"Win Rate: {win_rate:.1%}")
    print(f"Loss Rate: {loss_rate:.1%}")
    print(f"Push Rate: {push_rate:.1%}")
    print(f"EV/hr: ${ev_per_hour:.2f}")
    print(f"Risk of Ruin (bankroll = ${bankroll}): {ror:.2%}")

    if ev > 0:
        n0 = (stdev / ev) ** 2
        n0_hours = n0 / rounds_per_hour
        print(f"N₀ (rounds): {n0:.0f}")
        print(f"N₀ (hours @ {rounds_per_hour} rph): {n0_hours:.2f}")
    else:
        print("N₀: ∞ (non-positive EV)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mississippi Stud Strategy Simulation")
    parser.add_argument("--strategy", type=str, default="basic", help="Strategy name (default: basic)")
    parser.add_argument("--rounds", type=int, default=10000, help="Number of rounds to simulate")
    parser.add_argument("--ante", type=int, default=5, help="Ante bet per hand")
    parser.add_argument("--bankroll", type=float, default=500, help="Initial bankroll for risk of ruin calculation")
    parser.add_argument("--rounds_per_hour", type=float, default=30, help="Estimated rounds per hour for N₀ calc")
    parser.add_argument("--verbose", action="store_true", help="Show simulation progress")
    args = parser.parse_args()

    run_simulation(args.strategy, args.rounds, args.ante, args.bankroll, args.rounds_per_hour, args.verbose)
