
import math

# def risk_of_ruin(ev, sd, bankroll):
#     """
#     Calculates the risk of ruin based on expected value, standard deviation, and bankroll.
#     Formula:
#     ROR = exp(-2 * EV * Bankroll / SD^2)
#     Assumes EV > 0. If EV <= 0, risk of ruin is 1.
#     """
#     if ev <= 0 or sd == 0:
#         return 1.0
#     return math.exp(-2 * ev * bankroll / (sd ** 2))

def _clip01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x

def risk_of_ruin(mu_risk: float, sigma_risk: float, bankroll_over_Tbar: float) -> float:
    """
    Infinite-horizon risk of ruin under the drifted-Brownian approximation.
    
    Parameters:
    ----------
    mu_risk : float
        Mean profit per hand in *risk units* (EV / Tbar). Positive for +EV.
    
    sigma_risk : float
        Standard deviation of profit per hand in *risk units* (SD of profit / Tbar).

    bankroll_over_Tbar : float
        Bankroll measured in *risk units*, i.e. bankroll_dollars / Tbar_dollars.

    Returns:
    -------
    float
        Probability of eventual ruin (between 0 and 1).
    """

    # Guardrails
    if bankroll_over_Tbar <= 0 or sigma_risk <= 0:
        return 1.0
    if mu_risk <= 0:
        # Non-positive edge -> eventual ruin probability is 1 in this model
        return 1.0
    
    exponent = -2 * mu_risk * bankroll_over_Tbar / (sigma_risk ** 2)

    # numerical safety for very negative exponents
    if exponent < -700:  # exp(-700) is about 5e-305, close to underflow limit
        return 0.0
    
    return _clip01(math.exp(exponent))
