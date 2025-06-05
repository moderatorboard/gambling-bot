"""
Database Manager for SQLite operations
"""

import sqlite3
import aiosqlite
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "economy_bot.db"):
        self.db_path = db_path
        self.connection = None
    
    async def initialize(self):
        """Initialize database and create tables"""
        try:
            self.connection = await aiosqlite.connect(self.db_path)
            await self.create_tables()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def create_tables(self):
        """Create all necessary database tables"""
        tables = [
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                guild_id INTEGER NOT NULL,
                balance INTEGER DEFAULT 1000,
                crypto_balance INTEGER DEFAULT 0,
                total_winnings INTEGER DEFAULT 0,
                total_losses INTEGER DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                experience INTEGER DEFAULT 0,
                prestige INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_daily TIMESTAMP,
                last_weekly TIMESTAMP,
                last_monthly TIMESTAMP,
                last_yearly TIMESTAMP,
                last_work TIMESTAMP,
                last_overtime TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS guild_configs (
                guild_id INTEGER PRIMARY KEY,
                cash_name TEXT DEFAULT 'coins',
                cash_emoji TEXT DEFAULT '💰',
                crypto_name TEXT DEFAULT 'gems',
                crypto_emoji TEXT DEFAULT '💎',
                admin_ids TEXT DEFAULT '[]',
                disabled_channels TEXT DEFAULT '[]',
                update_messages_enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS user_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS cooldowns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                command_name TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                UNIQUE(user_id, guild_id, command_name)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS game_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                game_name TEXT NOT NULL,
                games_played INTEGER DEFAULT 0,
                games_won INTEGER DEFAULT 0,
                total_bet INTEGER DEFAULT 0,
                total_won INTEGER DEFAULT 0,
                best_streak INTEGER DEFAULT 0,
                current_streak INTEGER DEFAULT 0,
                UNIQUE(user_id, guild_id, game_name)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                amount INTEGER NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
        
        for table_sql in tables:
            await self.connection.execute(table_sql)
        
        await self.connection.commit()
    
    async def get_user(self, user_id: int, guild_id: int) -> Optional[Dict]:
        """Get user data or create new user"""
        try:
            async with self.connection.execute(
                "SELECT * FROM users WHERE user_id = ? AND guild_id = ?",
                (user_id, guild_id)
            ) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                else:
                    # Create new user
                    await self.connection.execute(
                        "INSERT INTO users (user_id, guild_id) VALUES (?, ?)",
                        (user_id, guild_id)
                    )
                    await self.connection.commit()
                    return await self.get_user(user_id, guild_id)
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    async def update_user_balance(self, user_id: int, guild_id: int, 
                                amount: int, currency_type: str = 'balance'):
        """Update user balance (positive or negative amount)"""
        try:
            await self.connection.execute(
                f"UPDATE users SET {currency_type} = {currency_type} + ? WHERE user_id = ? AND guild_id = ?",
                (amount, user_id, guild_id)
            )
            await self.connection.commit()
            
            # Record transaction
            await self.add_transaction(
                user_id, guild_id, 
                "credit" if amount > 0 else "debit",
                abs(amount),
                f"{currency_type} update"
            )
        except Exception as e:
            logger.error(f"Error updating balance for user {user_id}: {e}")
    
    async def add_transaction(self, user_id: int, guild_id: int, 
                            transaction_type: str, amount: int, description: str):
        """Add transaction record"""
        try:
            await self.connection.execute(
                "INSERT INTO transactions (user_id, guild_id, transaction_type, amount, description) VALUES (?, ?, ?, ?, ?)",
                (user_id, guild_id, transaction_type, amount, description)
            )
            await self.connection.commit()
        except Exception as e:
            logger.error(f"Error adding transaction: {e}")
    
    async def get_guild_config(self, guild_id: int) -> Dict:
        """Get guild configuration"""
        try:
            async with self.connection.execute(
                "SELECT * FROM guild_configs WHERE guild_id = ?",
                (guild_id,)
            ) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                else:
                    await self.create_guild_config(guild_id)
                    return await self.get_guild_config(guild_id)
        except Exception as e:
            logger.error(f"Error getting guild config {guild_id}: {e}")
            return {}
    
    async def create_guild_config(self, guild_id: int):
        """Create default guild configuration"""
        try:
            await self.connection.execute(
                "INSERT OR IGNORE INTO guild_configs (guild_id) VALUES (?)",
                (guild_id,)
            )
            await self.connection.commit()
        except Exception as e:
            logger.error(f"Error creating guild config: {e}")
    
    async def update_guild_config(self, guild_id: int, **kwargs):
        """Update guild configuration"""
        try:
            set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values()) + [guild_id]
            
            await self.connection.execute(
                f"UPDATE guild_configs SET {set_clause} WHERE guild_id = ?",
                values
            )
            await self.connection.commit()
        except Exception as e:
            logger.error(f"Error updating guild config: {e}")
    
    async def set_cooldown(self, user_id: int, guild_id: int, 
                         command_name: str, duration_seconds: int):
        """Set command cooldown"""
        try:
            expires_at = datetime.utcnow() + timedelta(seconds=duration_seconds)
            await self.connection.execute(
                "INSERT OR REPLACE INTO cooldowns (user_id, guild_id, command_name, expires_at) VALUES (?, ?, ?, ?)",
                (user_id, guild_id, command_name, expires_at)
            )
            await self.connection.commit()
        except Exception as e:
            logger.error(f"Error setting cooldown: {e}")
    
    async def check_cooldown(self, user_id: int, guild_id: int, command_name: str) -> Optional[int]:
        """Check if command is on cooldown, return remaining seconds"""
        try:
            async with self.connection.execute(
                "SELECT expires_at FROM cooldowns WHERE user_id = ? AND guild_id = ? AND command_name = ?",
                (user_id, guild_id, command_name)
            ) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    expires_at = datetime.fromisoformat(row[0])
                    now = datetime.utcnow()
                    
                    if expires_at > now:
                        return int((expires_at - now).total_seconds())
                    else:
                        # Cooldown expired, remove it
                        await self.connection.execute(
                            "DELETE FROM cooldowns WHERE user_id = ? AND guild_id = ? AND command_name = ?",
                            (user_id, guild_id, command_name)
                        )
                        await self.connection.commit()
                
                return None
        except Exception as e:
            logger.error(f"Error checking cooldown: {e}")
            return None
    
    async def get_leaderboard(self, guild_id: int, category: str = 'balance', limit: int = 10) -> List[Dict]:
        """Get leaderboard data"""
        try:
            valid_categories = ['balance', 'crypto_balance', 'total_winnings', 'games_played', 'level']
            if category not in valid_categories:
                category = 'balance'
            
            async with self.connection.execute(
                f"SELECT user_id, {category} FROM users WHERE guild_id = ? ORDER BY {category} DESC LIMIT ?",
                (guild_id, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [{'user_id': row[0], 'value': row[1]} for row in rows]
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return []
    
    async def update_game_stats(self, user_id: int, guild_id: int, game_name: str, 
                              won: bool, bet_amount: int, win_amount: int = 0):
        """Update game statistics"""
        try:
            # Get current stats
            async with self.connection.execute(
                "SELECT * FROM game_stats WHERE user_id = ? AND guild_id = ? AND game_name = ?",
                (user_id, guild_id, game_name)
            ) as cursor:
                row = await cursor.fetchone()
            
            if row:
                # Update existing stats
                current_streak = row[7] + 1 if won else 0
                best_streak = max(row[6], current_streak)
                
                await self.connection.execute(
                    """UPDATE game_stats SET 
                       games_played = games_played + 1,
                       games_won = games_won + ?,
                       total_bet = total_bet + ?,
                       total_won = total_won + ?,
                       best_streak = ?,
                       current_streak = ?
                       WHERE user_id = ? AND guild_id = ? AND game_name = ?""",
                    (1 if won else 0, bet_amount, win_amount, best_streak, current_streak,
                     user_id, guild_id, game_name)
                )
            else:
                # Create new stats
                await self.connection.execute(
                    """INSERT INTO game_stats 
                       (user_id, guild_id, game_name, games_played, games_won, total_bet, total_won, best_streak, current_streak)
                       VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?)""",
                    (user_id, guild_id, game_name, 1 if won else 0, bet_amount, win_amount,
                     1 if won else 0, 1 if won else 0)
                )
            
            await self.connection.commit()
        except Exception as e:
            logger.error(f"Error updating game stats: {e}")
    
    async def reset_daily_cooldowns(self):
        """Reset expired cooldowns (called by daily task)"""
        try:
            await self.connection.execute(
                "DELETE FROM cooldowns WHERE expires_at < ?",
                (datetime.utcnow(),)
            )
            await self.connection.commit()
        except Exception as e:
            logger.error(f"Error resetting cooldowns: {e}")
    
    async def close(self):
        """Close database connection"""
        if self.connection:
            await self.connection.close()
