"""
Coinflip game implementation
"""

import random
from database.models import GameResult

async def play_coinflip(prediction: str, bet_amount: int) -> GameResult:
    """
    Play coinflip game
    Args:
        prediction: 'heads' or 'tails'
        bet_amount: Amount to bet
    """
    # Normalize prediction
    prediction = prediction.lower()
    if prediction not in ['heads', 'tails', 'h', 't']:
        return GameResult(
            won=False,
            amount_won=0,
            message="❌ Invalid prediction! Use 'heads', 'tails', 'h', or 't'"
        )
    
    # Standardize prediction
    if prediction in ['h', 'heads']:
        prediction = 'heads'
    else:
        prediction = 'tails'
    
    # Flip the coin
    result = random.choice(['heads', 'tails'])
    
    # Determine outcome
    if prediction == result:
        winnings = bet_amount * 2
        emoji = "🪙" if result == "heads" else "🪙"
        return GameResult(
            won=True,
            amount_won=winnings,
            message=f"**{result.upper()}!** {emoji}\n🎉 You predicted correctly! You win **{winnings}** coins!",
            multiplier=2.0,
            details={"prediction": prediction, "result": result}
        )
    else:
        emoji = "🪙" if result == "heads" else "🪙"
        return GameResult(
            won=False,
            amount_won=0,
            message=f"**{result.upper()}!** {emoji}\n😢 You predicted **{prediction}** but got **{result}**. You lose **{bet_amount}** coins!",
            details={"prediction": prediction, "result": result}
        )

def get_coinflip_help() -> str:
    """Get help text for coinflip game"""
    return """
    **🪙 Coinflip Game**
    
    **How to play:**
    `/coinflip <prediction> <bet>`
    
    **Predictions:**
    • `heads` or `h` - Bet on heads
    • `tails` or `t` - Bet on tails
    
    **Payout:** 2x your bet if you win
    
    **Example:**
    `/coinflip heads 100` - Bet 100 coins on heads
    """
