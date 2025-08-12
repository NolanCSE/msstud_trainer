
import argparse
import statistics
import multiprocessing
from card_lib.deck import Deck
from core.strategies.basic import BasicStrategy
from core.strategies.ap3 import AdvantagePlay3rdStrategy
from core.strategies.ap5 import AdvantagePlay5thStrategy
from card_lib.simulation.mississippi_simulator import MississippiStudStrategy, simulate_round
from analysis.bankroll_math import risk_of_ruin

STRATEGIES = {
    "basic": BasicStrategy,
    "ap3": AdvantagePlay3rdStrategy,
    "ap5": AdvantagePlay5thStrategy
}

class SimulatedStrategy(MississippiStudStrategy):
    def __init__(self, strategy):
        self.strategy = strategy

    def get_bet(self, hole_cards, revealed_community_cards, stage, ante=1, current_total=0, ap_revealed_community_cards={'3rd': None, '4th': None, '5th': None}):
        return self.strategy.get_bet(hole_cards, revealed_community_cards, stage, ante, current_total, ap_revealed_community_cards)

def simulate_hand(args):
    strategy_class, ante, verbose = args
    strategy = strategy_class()
    wrapper = SimulatedStrategy(strategy)
    deck = Deck()
    deck.shuffle()
    return simulate_round(deck, wrapper, ante=ante, ap_revealed_community_cards={'3rd': True if strategy_class == AdvantagePlay3rdStrategy else False, '4th': False, '5th': True if strategy_class == AdvantagePlay5thStrategy else False})

def run_simulation(strategy_name, rounds, ante, bankroll, verbose, rounds_per_hour):
    strategy_class = STRATEGIES.get(strategy_name)
    if not strategy_class:
        raise ValueError(f"Unknown strategy: {strategy_name}")

    args_list = [(strategy_class, ante, verbose) for _ in range(rounds)]

    with multiprocessing.Pool() as pool:
        profits, totals = [], []
        for i, (profit, total) in enumerate(pool.imap_unordered(simulate_hand, args_list, chunksize=100)):
            profits.append(profit)
            totals.append(total)
            if verbose and (i + 1) % 1000 == 0:
                print(f"Simulated {i + 1} / {rounds} hands...")

    ev_per_hand = sum(profits) / rounds
    Tbar = sum(totals) / rounds
    mu_risk = ev_per_hand / Tbar
    sigma_risk = statistics.pstdev([p / Tbar for p in profits])  # SD in risk units
    B_over_Tbar = bankroll / Tbar

    ror = risk_of_ruin(mu_risk, sigma_risk, B_over_Tbar)

    print(f"\nStrategy: {strategy_name}")
    print(f"Rounds: {rounds}")
    print(f"Ante: ${ante}")
    print(f"EV per hand: ${ev_per_hand:.2f}")
    print(f"Standard Deviation: ${statistics.stdev(profits):.2f}" if len(profits) > 1 else "Standard Deviation: $0.00")
    print(f"Win Rate: {sum(1 for p in profits if p > 0)/rounds:.1%}")
    print(f"Loss Rate: {sum(1 for p in profits if p < 0)/rounds:.1%}")
    print(f"Push Rate: {1 - sum(1 for p in profits if p != 0)/rounds:.1%}")
    print(f"Avg total bet T̄: ${Tbar:.2f}")
    print(f"μ (risk units): {mu_risk:.4f}   σ (risk units): {sigma_risk:.4f}")
    print(f"Risk of Ruin (bankroll = ${bankroll:.2f}, ~{B_over_Tbar:.1f} risk units): {ror:.2%}")
    print(f"EV/hr: ${ev_per_hand * rounds_per_hour:.2f}")

    # if ev > 0:
    #     n0 = (stdev / ev) ** 2
    #     n0_hours = n0 / rounds_per_hour
    #     print(f"N₀ (rounds): {n0:.0f}")
    #     print(f"N₀ (hours @ {rounds_per_hour} rph): {n0_hours:.2f}")
    # else:
    #     print("N₀: ∞ (non-positive EV)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mississippi Stud Strategy Simulation")
    parser.add_argument("--strategy", type=str, default="basic", help="Strategy name (default: basic)")
    parser.add_argument("--rounds", type=int, default=10000, help="Number of rounds to simulate")
    parser.add_argument("--ante", type=int, default=5, help="Ante bet per hand")
    parser.add_argument("--bankroll", type=float, default=500, help="Initial bankroll for risk of ruin calculation")
    parser.add_argument("--rounds_per_hour", type=int, default=30, help="Rounds per hour")
    parser.add_argument("--verbose", action="store_true", help="Show simulation progress")
    args = parser.parse_args()

    run_simulation(args.strategy, args.rounds, args.ante, args.bankroll, args.verbose, args.rounds_per_hour)
