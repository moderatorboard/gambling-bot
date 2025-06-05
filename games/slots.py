"""
Slot machine game implementation
"""

import random
from typing import List, Dict
from database.models import GameResult

class SlotMachine:
    def __init__(self):
        # Slot symbols with their weights (lower weight = rarer)
        self.symbols = {
            '🍒': {'weight': 25, 'payout': 2},    # Cherry - common
            '🍋': {'weight': 20, 'payout': 3},    # Lemon - common
            '🍊': {'weight': 15, 'payout': 4},    # Orange - uncommon
            '🍇': {'weight': 12, 'payout': 5},    # Grape - uncommon
            '🔔': {'weight': 8, 'payout': 8},     # Bell - rare
            '⭐': {'weight': 5, 'payout': 12},    # Star - rare
            '💎': {'weight': 3, 'payout': 20},    # Diamond - very rare
            '🎰': {'weight': 1, 'payout': 50}     # Slot machine - jackpot
        }
        
        # Create weighted list for random selection
        self.weighted_symbols = []
        for symbol, data in self.symbols.items():
            self.weighted_symbols.extend([symbol] * data['weight'])
    
    def spin(self) -> List[str]:
        """Spin the slot machine and return 3 symbols"""
        return [random.choice(self.weighted_symbols) for _ in range(3)]
    
    def calculate_payout(self, symbols: List[str], bet_amount: int) -> Dict:
        """Calculate payout based on symbols"""
        # Count occurrences of each symbol
        symbol_counts = {}
        for symbol in symbols:
            symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        
        # Check for winning combinations
        payout_multiplier = 0
        win_type = ""
        
        # Three of a kind (jackpot)
        if len(symbol_counts) == 1:
            symbol = symbols[0]
            payout_multiplier = self.symbols[symbol]['payout']
            win_type = f"THREE {symbol}s!"
            
            # Bonus for rare symbols
            if symbol == '🎰':
                win_type = "🎉 MEGA JACKPOT! 🎉"
            elif symbol == '💎':
                win_type = "💎 DIAMOND JACKPOT! 💎"
            elif symbol == '⭐':
                win_type = "⭐ STAR JACKPOT! ⭐"
        
        # Two of a kind
        elif len(symbol_counts) == 2:
            # Find the symbol that appears twice
            for symbol, count in symbol_counts.items():
                if count == 2:
                    payout_multiplier = self.symbols[symbol]['payout'] * 0.3  # 30% of full payout
                    win_type = f"TWO {symbol}s"
                    break
        
        # Special combinations
        elif set(symbols) == {'🍒', '🍋', '🍊'}:
            payout_multiplier = 5
            win_type = "FRUIT COMBO!"
        elif set(symbols) == {'🔔', '⭐', '💎'}:
            payout_multiplier = 15
            win_type = "PREMIUM COMBO!"
        
        total_payout = int(bet_amount * payout_multiplier) if payout_multiplier > 0 else 0
        
        return {
            'payout': total_payout,
            'multiplier': payout_multiplier,
            'win_type': win_type,
            'symbols': symbols
        }

async def play_slots(bet_amount: int) -> GameResult:
    """Play slot machine game"""
    machine = SlotMachine()
    symbols = machine.spin()
    result = machine.calculate_payout(symbols, bet_amount)
    
    # Format the slot display
    slot_display = f"┌─────────────┐\n│ {' '.join(symbols)} │\n└─────────────┘"
    
    won = result['payout'] > 0
    
    if won:
        message = f"🎰 **SLOT MACHINE** 🎰\n\n{slot_display}\n\n"
        if result['win_type']:
            message += f"🎉 **{result['win_type']}** 🎉\n"
        message += f"💰 You win **{result['payout']}** coins! (x{result['multiplier']:.1f})"
        
        return GameResult(
            won=True,
            amount_won=result['payout'],
            message=message,
            multiplier=result['multiplier'],
            details=result
        )
    else:
        message = f"🎰 **SLOT MACHINE** 🎰\n\n{slot_display}\n\n"
        message += f"😢 No winning combination. You lose **{bet_amount}** coins!"
        
        return GameResult(
            won=False,
            amount_won=0,
            message=message,
            details=result
        )

def get_slots_help() -> str:
    """Get help text for slots game"""
    return """
    **🎰 Slot Machine**
    
    **How to play:**
    `/slots <bet>` - Spin the reels!
    
    **Symbols & Payouts (3 of a kind):**
    🍒 Cherry - x2
    🍋 Lemon - x3
    🍊 Orange - x4
    🍇 Grape - x5
    🔔 Bell - x8
    ⭐ Star - x12
    💎 Diamond - x20
    🎰 Mega Jackpot - x50!
    
    **Special Combos:**
    • Two of a kind: 30% payout
    • 🍒🍋🍊 Fruit Combo: x5
    • 🔔⭐💎 Premium Combo: x15
    
    **Tips:**
    • Higher bets = higher rewards
    • Rare symbols have better payouts
    • Try your luck at the jackpot!
    """
