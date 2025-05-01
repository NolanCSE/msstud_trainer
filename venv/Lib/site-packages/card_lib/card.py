class Card:
    SUIT_SYMBOLS = {
        "Spades": "♠",
        "Hearts": "♥",
        "Diamonds": "♦",
        "Clubs": "♣",
        "Joker": "🃏"
    }

    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __repr__(self):
        suit_symbol = self.SUIT_SYMBOLS.get(self.suit, "?")
        return f"{self.rank}{suit_symbol}"

    def __eq__(self, other):
        return self.rank == other.rank and self.suit == other.suit

    def __lt__(self, other):
        RANK_ORDER = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        return RANK_ORDER.index(self.rank) < RANK_ORDER.index(other.rank)