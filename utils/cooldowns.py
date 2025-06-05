"""
Cooldown management utilities
"""

from datetime import datetime, timedelta
from typing import Optional, Dict
from database.database import DatabaseManager

class CooldownManager:
    def __init__(self, db: DatabaseManager):
        self.db = db
        
        # Define cooldown durations in seconds
        self.cooldowns = {
            'daily': 86400,    # 24 hours
            'weekly': 604800,  # 7 days
            'monthly': 2592000, # 30 days
            'work': 14400,     # 4 hours
            'overtime': 28800, # 8 hours
            'gamble': 60,      # 1 minute
            'slots': 30,       # 30 seconds
            'blackjack': 45,   # 45 seconds
            'coinflip': 15,    # 15 seconds
            'dice': 20,        # 20 seconds
            'spin': 300,       # 5 minutes
            'vote': 43200,     # 12 hours
        }
    
    async def check_cooldown(self, user_id: int, guild_id: int, command: str) -> Optional[int]:
        """
        Check if a command is on cooldown
        Returns: remaining seconds if on cooldown, None if available
        """
        return await self.db.check_cooldown(user_id, guild_id, command)
    
    async def set_cooldown(self, user_id: int, guild_id: int, command: str) -> bool:
        """
        Set a cooldown for a command
        Returns: True if cooldown was set, False if command not found
        """
        if command not in self.cooldowns:
            return False
        
        duration = self.cooldowns[command]
        await self.db.set_cooldown(user_id, guild_id, command, duration)
        return True
    
    async def get_all_cooldowns(self, user_id: int, guild_id: int) -> Dict[str, Optional[int]]:
        """Get all active cooldowns for a user"""
        cooldowns = {}
        
        for command in self.cooldowns:
            remaining = await self.check_cooldown(user_id, guild_id, command)
            if remaining and remaining > 0:
                cooldowns[command] = remaining
        
        return cooldowns
    
    def format_cooldown_time(self, seconds: int) -> str:
        """Format cooldown time into human readable format"""
        if seconds <= 0:
            return "Ready!"
        
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 and not parts:  # Only show seconds if no larger units
            parts.append(f"{seconds}s")
        
        return " ".join(parts) if parts else "Ready!"
    
    async def format_user_cooldowns(self, user_id: int, guild_id: int, detailed: bool = False) -> str:
        """Format all user cooldowns for display"""
        cooldowns = await self.get_all_cooldowns(user_id, guild_id)
        
        if not cooldowns:
            return "⏰ **All commands are ready to use!**"
        
        message = "⏰ **Your Cooldowns:**\n\n"
        
        # Group cooldowns by category
        game_cooldowns = {}
        reward_cooldowns = {}
        other_cooldowns = {}
        
        for command, remaining in cooldowns.items():
            if command in ['daily', 'weekly', 'monthly', 'work', 'overtime']:
                reward_cooldowns[command] = remaining
            elif command in ['gamble', 'slots', 'blackjack', 'coinflip', 'dice']:
                game_cooldowns[command] = remaining
            else:
                other_cooldowns[command] = remaining
        
        if reward_cooldowns:
            message += "💰 **Rewards & Work:**\n"
            for command, remaining in reward_cooldowns.items():
                time_str = self.format_cooldown_time(remaining)
                message += f"• {command.title()}: {time_str}\n"
            message += "\n"
        
        if game_cooldowns:
            message += "🎮 **Games:**\n"
            for command, remaining in game_cooldowns.items():
                time_str = self.format_cooldown_time(remaining)
                message += f"• {command.title()}: {time_str}\n"
            message += "\n"
        
        if other_cooldowns:
            message += "🔧 **Other:**\n"
            for command, remaining in other_cooldowns.items():
                time_str = self.format_cooldown_time(remaining)
                message += f"• {command.title()}: {time_str}\n"
        
        if detailed:
            message += "\n*Use commands when cooldowns expire*"
        
        return message
    
    async def is_command_available(self, user_id: int, guild_id: int, command: str) -> bool:
        """Check if a command is available (not on cooldown)"""
        remaining = await self.check_cooldown(user_id, guild_id, command)
        return remaining is None or remaining <= 0
    
    async def get_cooldown_embed_data(self, user_id: int, guild_id: int) -> Dict:
        """Get cooldown data formatted for Discord embeds"""
        cooldowns = await self.get_all_cooldowns(user_id, guild_id)
        
        embed_data = {
            "title": "⏰ Command Cooldowns",
            "fields": [],
            "color": 0x3498db
        }
        
        if not cooldowns:
            embed_data["description"] = "All commands are ready to use! 🎉"
            embed_data["color"] = 0x2ecc71
            return embed_data
        
        # Sort cooldowns by remaining time
        sorted_cooldowns = sorted(cooldowns.items(), key=lambda x: x[1], reverse=True)
        
        for command, remaining in sorted_cooldowns:
            time_str = self.format_cooldown_time(remaining)
            embed_data["fields"].append({
                "name": f"/{command}",
                "value": time_str,
                "inline": True
            })
        
        return embed_data
