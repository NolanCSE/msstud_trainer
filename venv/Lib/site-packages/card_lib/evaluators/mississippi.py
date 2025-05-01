
from collections import Counter
from card_lib.card import Card
from card_lib.evaluators import evaluate_hand

RANK_ORDER = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6,
    '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 11, 'Q': 12, 'K': 13, 'A': 14
}

def evaluate_mississippi_stud_hand(hand: list[Card], joker_mode="wild"):
    poker_result = evaluate_hand(hand, joker_mode)

    ms_winning_hands = [
        "Royal Flush", "Straight Flush", "Four of a Kind",
        "Full House", "Flush", "Straight", "Three of a Kind", "Two Pair"
    ]

    if poker_result in ms_winning_hands:
        return f"Win: {poker_result}"

    elif poker_result == "One Pair":
        # Count non-joker cards
        non_joker_ranks = [
            card.rank for card in hand if card.suit != "Joker"
        ]
        rank_counts = Counter(non_joker_ranks)
        pairs = [rank for rank, count in rank_counts.items() if count == 2]

        if not pairs:
            return "Loss"

        highest_pair = max(pairs, key=lambda r: RANK_ORDER[r])

        if RANK_ORDER[highest_pair] >= 11:
            return f"Win: Pair of {highest_pair}s (Jacks or Better)"
        elif RANK_ORDER[highest_pair] >= 6:
            return f"Win: Pair of {highest_pair}s (6s through 10s)"
        else:
            return "Loss"
    else:
        return "Loss"
