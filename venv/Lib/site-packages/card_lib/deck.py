import random
from .card import Card

class Deck:
    def __init__(self, include_jokers=False):
        self.cards = self._generate_deck(include_jokers)
        self.shuffle()

    def _generate_deck(self, include_jokers):
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = [Card(suit, rank) for suit in suits for rank in ranks]
        if include_jokers:
            deck.append(Card('Joker', 'Red'))
            deck.append(Card('Joker', 'Black'))
        return deck

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, num=1):
        if num > len(self.cards):
            raise ValueError("Not enough cards left to deal")
        return [self.cards.pop() for _ in range(num)]

    def draw(self):
        return self.deal(1)[0]

    def __len__(self):
        return len(self.cards)

    def __repr__(self):
        return f"Deck({len(self.cards)} cards remaining)"
