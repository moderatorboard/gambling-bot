"""
Economy system for managing user balances and transactions
"""

import logging
from typing import Optional, Dict, List
from database.database import DatabaseManager
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class EconomyManager:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def get_user_balance(self, user_id: int, guild_id: int) -> Dict[str, int]:
        """Get user's balance information"""
        user = await self.db.get_user(user_id, guild_id)
        if user:
            return {
                'balance': user['balance'],
                'crypto_balance': user['crypto_balance'],
                'total_winnings': user['total_winnings'],
                'total_losses': user['total_losses']
            }
        return {'balance': 0, 'crypto_balance': 0, 'total_winnings': 0, 'total_losses': 0}
    
    async def can_afford(self, user_id: int, guild_id: int, amount: int, currency_type: str = 'balance') -> bool:
        """Check if user can afford the specified amount"""
        user = await self.db.get_user(user_id, guild_id)
        if not user:
            return False
        
        return user[currency_type] >= amount
    
    async def deduct_balance(self, user_id: int, guild_id: int, amount: int, currency_type: str = 'balance') -> bool:
        """Deduct amount from user balance"""
        if await self.can_afford(user_id, guild_id, amount, currency_type):
            await self.db.update_user_balance(user_id, guild_id, -amount, currency_type)
            return True
        return False
    
    async def add_balance(self, user_id: int, guild_id: int, amount: int, currency_type: str = 'balance'):
        """Add amount to user balance"""
        await self.db.update_user_balance(user_id, guild_id, amount, currency_type)
    
    async def transfer_money(self, from_user: int, to_user: int, guild_id: int, amount: int) -> bool:
        """Transfer money between users"""
        if await self.can_afford(from_user, guild_id, amount):
            await self.deduct_balance(from_user, guild_id, amount)
            await self.add_balance(to_user, guild_id, amount)
            
            # Record transactions
            await self.db.add_transaction(from_user, guild_id, "transfer_out", amount, f"Transfer to user {to_user}")
            await self.db.add_transaction(to_user, guild_id, "transfer_in", amount, f"Transfer from user {from_user}")
            
            return True
        return False
    
    async def process_game_result(self, user_id: int, guild_id: int, game_name: str, 
                                bet_amount: int, won: bool, win_amount: int = 0):
        """Process the result of a game"""
        # First deduct the bet
        if not await self.deduct_balance(user_id, guild_id, bet_amount):
            raise ValueError("Insufficient balance for bet")
        
        # Add winnings if won
        total_return = 0
        if won and win_amount > 0:
            await self.add_balance(user_id, guild_id, win_amount)
            total_return = win_amount
        
        # Update game statistics
        await self.db.update_game_stats(user_id, guild_id, game_name, won, bet_amount, win_amount)
        
        # Update user totals
        if won:
            await self.db.connection.execute(
                "UPDATE users SET total_winnings = total_winnings + ?, games_played = games_played + 1 WHERE user_id = ? AND guild_id = ?",
                (win_amount, user_id, guild_id)
            )
        else:
            await self.db.connection.execute(
                "UPDATE users SET total_losses = total_losses + ?, games_played = games_played + 1 WHERE user_id = ? AND guild_id = ?",
                (bet_amount, user_id, guild_id)
            )
        
        await self.db.connection.commit()
        return total_return
    
    async def get_user_stats(self, user_id: int, guild_id: int) -> Dict:
        """Get comprehensive user statistics"""
        user = await self.db.get_user(user_id, guild_id)
        if not user:
            return {}
        
        # Calculate net profit
        net_profit = user['total_winnings'] - user['total_losses']
        
        # Get game-specific stats
        game_stats = []
        async with self.db.connection.execute(
            "SELECT game_name, games_played, games_won, total_bet, total_won, best_streak FROM game_stats WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id)
        ) as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                win_rate = (row[2] / row[1] * 100) if row[1] > 0 else 0
                game_stats.append({
                    'game': row[0],
                    'played': row[1],
                    'won': row[2],
                    'total_bet': row[3],
                    'total_won': row[4],
                    'best_streak': row[5],
                    'win_rate': round(win_rate, 1)
                })
        
        return {
            'user_data': user,
            'net_profit': net_profit,
            'game_stats': game_stats
        }
    
    async def calculate_level_and_xp(self, user_id: int, guild_id: int, xp_gained: int = 0):
        """Calculate and update user level based on experience"""
        user = await self.db.get_user(user_id, guild_id)
        if not user:
            return
        
        new_xp = user['experience'] + xp_gained
        
        # Simple level calculation: level = sqrt(xp / 100)
        import math
        new_level = int(math.sqrt(new_xp / 100)) + 1
        
        level_up = new_level > user['level']
        
        # Update user
        await self.db.connection.execute(
            "UPDATE users SET experience = ?, level = ? WHERE user_id = ? AND guild_id = ?",
            (new_xp, new_level, user_id, guild_id)
        )
        await self.db.connection.commit()
        
        return {
            'level_up': level_up,
            'old_level': user['level'],
            'new_level': new_level,
            'xp': new_xp
        }
    
    async def get_transaction_history(self, user_id: int, guild_id: int, limit: int = 10) -> List[Dict]:
        """Get user's recent transaction history"""
        async with self.db.connection.execute(
            "SELECT transaction_type, amount, description, created_at FROM transactions WHERE user_id = ? AND guild_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, guild_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    'type': row[0],
                    'amount': row[1],
                    'description': row[2],
                    'timestamp': row[3]
                }
                for row in rows
            ]
