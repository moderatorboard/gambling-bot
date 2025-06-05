"""
Dice rolling game implementation
"""

import random
from typing import List
from database.models import GameResult

async def play_dice_roll(prediction: str, bet_amount: int, dice_count: int = 2) -> GameResult:
    """
    Play dice rolling game
    Args:
        prediction: 'high' (8-12), 'low' (2-6), 'lucky7' (exactly 7), or specific number
        bet_amount: Amount to bet
        dice_count: Number of dice to roll (default 2)
    """
    # Roll the dice
    dice_results = [random.randint(1, 6) for _ in range(dice_count)]
    total = sum(dice_results)
    
    # Format dice display
    dice_emojis = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅']
    dice_display = ' '.join([dice_emojis[roll - 1] for roll in dice_results])
    
    prediction = prediction.lower()
    won = False
    multiplier = 0
    win_description = ""
    
    # Determine win conditions
    if prediction == 'high' and total >= 8:
        won = True
        multiplier = 2.0
        win_description = f"HIGH ({total})"
    elif prediction == 'low' and total <= 6:
        won = True
        multiplier = 2.0
        win_description = f"LOW ({total})"
    elif prediction == 'lucky7' and total == 7:
        won = True
        multiplier = 5.0
        win_description = "LUCKY 7! 🍀"
    elif prediction.isdigit():
        target = int(prediction)
        if 2 <= target <= 12 and total == target:
            won = True
            # Higher multiplier for exact number prediction
            if target in [2, 12]:
                multiplier = 35.0  # Snake eyes or boxcars
            elif target in [3, 11]:
                multiplier = 17.0
            elif target in [4, 10]:
                multiplier = 11.0
            elif target in [5, 9]:
                multiplier = 8.0
            elif target in [6, 8]:
                multiplier = 6.0
            elif target == 7:
                multiplier = 5.0
            win_description = f"EXACT MATCH: {target}!"
    
    # Calculate winnings
    if won:
        winnings = int(bet_amount * multiplier)
        message = f"🎲 **DICE ROLL** 🎲\n\n{dice_display}\n**Total: {total}**\n\n"
        message += f"🎉 **{win_description}**\nYou win **{winnings}** coins! (x{multiplier})"
        
        return GameResult(
            won=True,
            amount_won=winnings,
            message=message,
            multiplier=multiplier,
            details={"dice": dice_results, "total": total, "prediction": prediction}
        )
    else:
        message = f"🎲 **DICE ROLL** 🎲\n\n{dice_display}\n**Total: {total}**\n\n"
        message += f"😢 Your prediction '{prediction}' didn't match. You lose **{bet_amount}** coins!"
        
        return GameResult(
            won=False,
            amount_won=0,
            message=message,
            details={"dice": dice_results, "total": total, "prediction": prediction}
        )

async def play_single_dice(prediction: str, bet_amount: int) -> GameResult:
    """Play single dice game (1-6)"""
    roll = random.randint(1, 6)
    dice_emojis = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅']
    dice_display = dice_emojis[roll - 1]
    
    won = False
    multiplier = 0
    
    if prediction.lower() in ['high', 'hi'] and roll >= 4:
        won = True
        multiplier = 2.0
    elif prediction.lower() in ['low', 'lo'] and roll <= 3:
        won = True
        multiplier = 2.0
    elif prediction.isdigit() and int(prediction) == roll:
        won = True
        multiplier = 6.0  # Exact number on single die
    
    if won:
        winnings = int(bet_amount * multiplier)
        win_type = "HIGH" if prediction.lower() in ['high', 'hi'] else "LOW" if prediction.lower() in ['low', 'lo'] else f"EXACT ({roll})"
        message = f"🎲 **SINGLE DICE** 🎲\n\n{dice_display}\n**Roll: {roll}**\n\n"
        message += f"🎉 **{win_type}!**\nYou win **{winnings}** coins! (x{multiplier})"
        
        return GameResult(
            won=True,
            amount_won=winnings,
            message=message,
            multiplier=multiplier,
            details={"roll": roll, "prediction": prediction}
        )
    else:
        message = f"🎲 **SINGLE DICE** 🎲\n\n{dice_display}\n**Roll: {roll}**\n\n"
        message += f"😢 Your prediction '{prediction}' didn't match. You lose **{bet_amount}** coins!"
        
        return GameResult(
            won=False,
            amount_won=0,
            message=message,
            details={"roll": roll, "prediction": prediction}
        )

def get_dice_help() -> str:
    """Get help text for dice games"""
    return """
    **🎲 Dice Games**
    
    **Two Dice Game:**
    `/roll <prediction> <bet>`
    
    **Predictions:**
    • `high` - Total 8-12 (x2 payout)
    • `low` - Total 2-6 (x2 payout)
    • `lucky7` - Exactly 7 (x5 payout)
    • `2-12` - Exact number (x5-35 payout)
    
    **Single Dice Game:**
    `/roll <prediction> <bet> single`
    
    **Predictions:**
    • `high` - Roll 4-6 (x2 payout)
    • `low` - Roll 1-3 (x2 payout)
    • `1-6` - Exact number (x6 payout)
    
    **Payout Guide:**
    • Snake eyes (2) or Boxcars (12): x35
    • 3 or 11: x17
    • 4 or 10: x11
    • 5 or 9: x8
    • 6 or 8: x6
    • Lucky 7: x5
    """
