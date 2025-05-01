
import math

def risk_of_ruin(ev, sd, bankroll):
    """
    Calculates the risk of ruin based on expected value, standard deviation, and bankroll.
    Formula:
    ROR = exp(-2 * EV * Bankroll / SD^2)
    Assumes EV > 0. If EV <= 0, risk of ruin is 1.
    """
    if ev <= 0 or sd == 0:
        return 1.0
    return math.exp(-2 * ev * bankroll / (sd ** 2))
