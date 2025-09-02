
from collections import Counter
from card_lib.card import Card
from card_lib.utils.mississippi_constants import RANK_ORDER
from card_lib.evaluators.mississippi import evaluate_mississippi_stud_hand

def card_points(card: Card) -> int:
    if card.rank in {"J", "Q", "K", "A"}:
        return 2
    elif card.rank in {"6", "7", "8", "9", "10"}:
        return 1
    else:
        return 0

def evaluate_partial_hand(cards: list[Card]) -> dict:
    ranks = [card.rank for card in cards if card.suit != "Joker"]
    suits = [card.suit for card in cards if card.suit != "Joker"]
    rank_vals = sorted([RANK_ORDER[rank] for rank in ranks])
    rank_counts = Counter(ranks)

    num_high = sum(1 for r in ranks if RANK_ORDER[r] >= 11)
    num_mid = sum(1 for r in ranks if 6 <= RANK_ORDER[r] <= 10)
    num_low = sum(1 for r in ranks if RANK_ORDER[r] <= 5)

    pair_rank = None
    for rank, count in rank_counts.items():
        if count == 2:
            pair_rank = rank

    # is_made_hand = pair_rank and RANK_ORDER[pair_rank] >= 6
    padded = cards[:]
    while len(padded) < 5:
        padded.append(Card("Joker", "Red"))

    result = evaluate_mississippi_stud_hand(padded, joker_mode="dead")
    print(f'Evaluating hand: {cards} -> Result: {result}')
    is_made_hand = result not in ["Loss", "High Card"]

    flush_draw = any(suits.count(suit) >= len(cards) for suit in suits)

    # Straight draw & gap analysis
    gaps = None
    if len(rank_vals) >= 3:
        unique_vals = sorted(set(rank_vals))
        diffs = [b - a for a, b in zip(unique_vals, unique_vals[1:])]
        total_gaps = sum(d - 1 for d in diffs if d > 1)
        gaps = total_gaps if total_gaps <= 2 else None

        # check for wheel (A2345)
        if set(rank_vals) == {2, 3, 4, 5, 14}:
            gaps = 0

    return {
        "pair_rank": pair_rank,
        "is_made_hand": is_made_hand,
        "is_flush_draw": flush_draw,
        "is_straight_draw": gaps is not None,
        "straight_gaps": gaps,
        "num_high_cards": num_high,
        "num_mid_cards": num_mid,
        "num_low_cards": num_low,
        "total_points": sum(card_points(card) for card in cards),
        "min_straight_rank": min(RANK_ORDER[rank] for rank in ranks) if ranks else 0,
        "contains_8_or_higher": any(RANK_ORDER[rank] >= 8 for rank in ranks)
    }
