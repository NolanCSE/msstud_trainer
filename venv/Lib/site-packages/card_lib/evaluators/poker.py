# card_lib/poker.py

from collections import Counter
from card_lib.card import Card
from itertools import combinations, product

RANK_ORDER = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
    '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
}

REVERSE_RANK = {v: k for k, v in RANK_ORDER.items()}
SUITS = ['Hearts', 'Diamonds', 'Clubs', 'Spades']

# Evaluation ranking order
HAND_RANKS = [
    "Invalid Hand","High Card", "One Pair", "Two Pair", "Three of a Kind",
    "Straight", "Flush", "Full House", "Four of a Kind",
    "Straight Flush", "Royal Flush"
]

def generate_minimal_filler(existing_hand):
    # Generate "lowest possible" dummy cards that don't affect the hand
    # e.g., 2 of different suits/ranks that won't create a pair, flush, or straight
    existing_ranks = {card.rank for card in existing_hand}
    existing_suits = {card.suit for card in existing_hand}
    fillers = []
    for suit in SUITS:
        for rank in RANK_ORDER:
            if rank not in existing_ranks and suit not in existing_suits:
                fillers.append(Card(suit, rank))
            if len(fillers) + len(existing_hand) >= 5:
                return fillers
    return fillers


def evaluate_hand(hand, joker_mode="wild"):
    jokers = [card for card in hand if card.suit == "Joker"]
    non_jokers = [card for card in hand if card.suit != "Joker"]

    if joker_mode == "dead":
        non_jokers = [card for card in hand if card.suit != "Joker"]
        if len(non_jokers) < 5:
            return evaluate_standard(non_jokers + generate_minimal_filler(non_jokers))
        return evaluate_standard(non_jokers)

    elif joker_mode == "wild":
        if not jokers:
            return evaluate_standard(hand)

        num_jokers = len(jokers)
        best_rank_index = 0  # Start from "High Card"

        # Generate all possible joker replacements
        all_ranks = list(RANK_ORDER.keys())
        replacements = list(product(SUITS, all_ranks))
        for joker_cards in combinations(replacements, num_jokers):
            candidate_hand = non_jokers + [Card(suit, rank) for suit, rank in joker_cards]
            result = evaluate_standard(candidate_hand)
            rank_index = HAND_RANKS.index(result)
            best_rank_index = max(best_rank_index, rank_index)

        return HAND_RANKS[best_rank_index]

def evaluate_standard(hand):
    ranks = [RANK_ORDER[card.rank] for card in hand]
    suits = [card.suit for card in hand]
    rank_counts = Counter(ranks).values()
    is_flush = len(set(suits)) == 1
    sorted_ranks = sorted(set(ranks))
    is_straight = sorted_ranks == list(range(min(sorted_ranks), max(sorted_ranks) + 1)) and len(sorted_ranks) == 5

    if 5 in rank_counts:
        return "Invalid Hand"

    # Ace-low straight
    if set(ranks) == {14, 2, 3, 4, 5}:
        is_straight = True
        sorted_ranks = [5]

    if is_straight and is_flush and set(ranks) == {10, 11, 12, 13, 14}:
        return "Royal Flush"
    elif is_straight and is_flush:
        return "Straight Flush"
    elif 4 in rank_counts:
        return "Four of a Kind"
    elif 3 in rank_counts and 2 in rank_counts:
        return "Full House"
    elif is_flush:
        return "Flush"
    elif is_straight:
        return "Straight"
    elif 3 in rank_counts:
        return "Three of a Kind"
    elif list(rank_counts).count(2) == 2:
        return "Two Pair"
    elif 2 in rank_counts:
        return "One Pair"
    else:
        return "High Card"
