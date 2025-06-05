"""
Data models and structures
"""

from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime

@dataclass
class User:
    user_id: int
    guild_id: int
    balance: int = 1000
    crypto_balance: int = 0
    total_winnings: int = 0
    total_losses: int = 0
    games_played: int = 0
    level: int = 1
    experience: int = 0
    prestige: int = 0
    created_at: Optional[datetime] = None
    last_daily: Optional[datetime] = None
    last_weekly: Optional[datetime] = None
    last_monthly: Optional[datetime] = None
    last_yearly: Optional[datetime] = None
    last_work: Optional[datetime] = None
    last_overtime: Optional[datetime] = None

@dataclass
class GuildConfig:
    guild_id: int
    cash_name: str = "coins"
    cash_emoji: str = "💰"
    crypto_name: str = "gems"
    crypto_emoji: str = "💎"
    admin_ids: List[int] = None
    disabled_channels: List[int] = None
    update_messages_enabled: bool = True
    created_at: Optional[datetime] = None

@dataclass
class GameResult:
    won: bool
    amount_won: int
    message: str
    multiplier: float = 1.0
    details: Dict = None

@dataclass
class ShopItem:
    item_id: str
    name: str
    description: str
    price: int
    currency_type: str = "balance"
    max_quantity: int = -1
    category: str = "misc"

# Predefined shop items
SHOP_ITEMS = {
    "luck_boost": ShopItem(
        "luck_boost", "Luck Boost", 
        "Increases your luck for the next 10 games", 
        500, "balance", 5, "boosts"
    ),
    "double_xp": ShopItem(
        "double_xp", "Double XP", 
        "Doubles experience gain for 1 hour", 
        1000, "balance", 3, "boosts"
    ),
    "daily_multiplier": ShopItem(
        "daily_multiplier", "Daily Multiplier", 
        "Increases daily reward by 50% for 7 days", 
        2000, "balance", 1, "boosts"
    ),
    "lotto_ticket": ShopItem(
        "lotto_ticket", "Lottery Ticket", 
        "Enter the weekly lottery draw", 
        100, "balance", 50, "tickets"
    ),
    "protection": ShopItem(
        "protection", "Loss Protection", 
        "Protects against the next loss", 
        1500, "balance", 1, "protection"
    )
}
