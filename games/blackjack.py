"""
Blackjack game implementation
"""

import random
from typing import List, Tuple
from database.models import GameResult

class Card:
    def __init__(self, suit: str, rank: str):
        self.suit = suit
        self.rank = rank
        self.value = self._calculate_value()
    
    def _calculate_value(self) -> int:
        if self.rank in ['J', 'Q', 'K']:
            return 10
        elif self.rank == 'A':
            return 11  # Ace value will be adjusted in hand calculation
        else:
            return int(self.rank)
    
    def __str__(self):
        return f"{self.rank}{self.suit}"

class BlackjackHand:
    def __init__(self):
        self.cards: List[Card] = []
    
    def add_card(self, card: Card):
        self.cards.append(card)
    
    def calculate_value(self) -> int:
        value = sum(card.value for card in self.cards)
        aces = sum(1 for card in self.cards if card.rank == 'A')
        
        # Adjust for aces
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        
        return value
    
    def is_blackjack(self) -> bool:
        return len(self.cards) == 2 and self.calculate_value() == 21
    
    def is_bust(self) -> bool:
        return self.calculate_value() > 21
    
    def __str__(self):
        return " ".join(str(card) for card in self.cards)

class BlackjackGame:
    def __init__(self):
        self.deck = self._create_deck()
        self.player_hand = BlackjackHand()
        self.dealer_hand = BlackjackHand()
        self.game_over = False
    
    def _create_deck(self) -> List[Card]:
        suits = ['♠', '♥', '♦', '♣']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = [Card(suit, rank) for suit in suits for rank in ranks]
        random.shuffle(deck)
        return deck
    
    def deal_initial_cards(self):
        """Deal initial 2 cards to player and dealer"""
        for _ in range(2):
            self.player_hand.add_card(self.deck.pop())
            self.dealer_hand.add_card(self.deck.pop())
    
    def hit(self, hand: BlackjackHand):
        """Add a card to the specified hand"""
        if self.deck:
            hand.add_card(self.deck.pop())
    
    def dealer_play(self):
        """Dealer plays according to standard rules"""
        while self.dealer_hand.calculate_value() < 17:
            self.hit(self.dealer_hand)
    
    def determine_winner(self, bet_amount: int) -> GameResult:
        """Determine the winner and calculate payout"""
        player_value = self.player_hand.calculate_value()
        dealer_value = self.dealer_hand.calculate_value()
        
        # Player bust
        if self.player_hand.is_bust():
            return GameResult(
                won=False,
                amount_won=0,
                message=f"**BUST!** Your hand: {self.player_hand} ({player_value})\nYou lose {bet_amount} coins! 💸",
                details={"player_hand": str(self.player_hand), "dealer_hand": str(self.dealer_hand)}
            )
        
        # Player blackjack
        if self.player_hand.is_blackjack() and not self.dealer_hand.is_blackjack():
            winnings = int(bet_amount * 2.5)
            return GameResult(
                won=True,
                amount_won=winnings,
                message=f"**BLACKJACK!** 🎉\nYour hand: {self.player_hand} ({player_value})\nYou win {winnings} coins!",
                multiplier=2.5,
                details={"player_hand": str(self.player_hand), "dealer_hand": str(self.dealer_hand)}
            )
        
        # Dealer bust
        if self.dealer_hand.is_bust():
            winnings = bet_amount * 2
            return GameResult(
                won=True,
                amount_won=winnings,
                message=f"**DEALER BUST!** 🎉\nDealer: {self.dealer_hand} ({dealer_value})\nYour hand: {self.player_hand} ({player_value})\nYou win {winnings} coins!",
                multiplier=2.0,
                details={"player_hand": str(self.player_hand), "dealer_hand": str(self.dealer_hand)}
            )
        
        # Both blackjack - push
        if self.player_hand.is_blackjack() and self.dealer_hand.is_blackjack():
            return GameResult(
                won=False,
                amount_won=bet_amount,  # Return bet
                message=f"**PUSH!** Both have blackjack!\nYour bet is returned.",
                multiplier=1.0,
                details={"player_hand": str(self.player_hand), "dealer_hand": str(self.dealer_hand)}
            )
        
        # Compare values
        if player_value > dealer_value:
            winnings = bet_amount * 2
            return GameResult(
                won=True,
                amount_won=winnings,
                message=f"**YOU WIN!** 🎉\nYour hand: {self.player_hand} ({player_value})\nDealer: {self.dealer_hand} ({dealer_value})\nYou win {winnings} coins!",
                multiplier=2.0,
                details={"player_hand": str(self.player_hand), "dealer_hand": str(self.dealer_hand)}
            )
        elif player_value < dealer_value:
            return GameResult(
                won=False,
                amount_won=0,
                message=f"**YOU LOSE!** 😢\nYour hand: {self.player_hand} ({player_value})\nDealer: {self.dealer_hand} ({dealer_value})\nYou lose {bet_amount} coins!",
                details={"player_hand": str(self.player_hand), "dealer_hand": str(self.dealer_hand)}
            )
        else:
            return GameResult(
                won=False,
                amount_won=bet_amount,  # Return bet
                message=f"**PUSH!** Same value ({player_value})\nYour bet is returned.",
                multiplier=1.0,
                details={"player_hand": str(self.player_hand), "dealer_hand": str(self.dealer_hand)}
            )

async def play_blackjack(bet_amount: int) -> GameResult:
    """Play a complete blackjack game"""
    game = BlackjackGame()
    game.deal_initial_cards()
    
    # For now, we'll auto-play the optimal strategy
    # In a full implementation, you'd want interactive play
    
    # Simple strategy: hit if under 17, stand if 17+
    while game.player_hand.calculate_value() < 17 and not game.player_hand.is_bust():
        game.hit(game.player_hand)
    
    # Dealer plays
    if not game.player_hand.is_bust():
        game.dealer_play()
    
    return game.determine_winner(bet_amount)
