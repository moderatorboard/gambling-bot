"""
Utility helper functions
"""

import random
import string
from typing import List, Dict, Any, Optional
import discord
from discord.ext import commands

def format_currency(amount: int, currency_type: str = "coins") -> str:
    """Format currency with appropriate emoji and commas"""
    emoji = "💰" if currency_type in ["coins", "balance"] else "💎"
    return f"{emoji} {amount:,}"

def format_percentage(value: float) -> str:
    """Format percentage with 1 decimal place"""
    return f"{value:.1f}%"

def generate_progress_bar(current: int, maximum: int, length: int = 10) -> str:
    """Generate a progress bar using unicode characters"""
    if maximum <= 0:
        return "█" * length
    
    progress = min(current / maximum, 1.0)
    filled = int(progress * length)
    empty = length - filled
    
    return "█" * filled + "░" * empty

def create_embed(title: str, description: str = None, color: int = 0x3498db, **kwargs) -> discord.Embed:
    """Create a Discord embed with consistent styling"""
    embed = discord.Embed(title=title, description=description, color=color)
    
    # Add common fields if provided
    if 'fields' in kwargs:
        for field in kwargs['fields']:
            embed.add_field(
                name=field.get('name', ''),
                value=field.get('value', ''),
                inline=field.get('inline', False)
            )
    
    if 'footer' in kwargs:
        embed.set_footer(text=kwargs['footer'])
    
    if 'thumbnail' in kwargs:
        embed.set_thumbnail(url=kwargs['thumbnail'])
    
    if 'author' in kwargs:
        author = kwargs['author']
        embed.set_author(
            name=author.get('name', ''),
            icon_url=author.get('icon_url', ''),
            url=author.get('url', '')
        )
    
    return embed

def create_error_embed(message: str) -> discord.Embed:
    """Create an error embed"""
    return create_embed(
        title="❌ Error",
        description=message,
        color=0xe74c3c
    )

def create_success_embed(message: str) -> discord.Embed:
    """Create a success embed"""
    return create_embed(
        title="✅ Success",
        description=message,
        color=0x2ecc71
    )

def create_info_embed(title: str, message: str) -> discord.Embed:
    """Create an info embed"""
    return create_embed(
        title=f"ℹ️ {title}",
        description=message,
        color=0x3498db
    )

def calculate_level_xp(level: int) -> int:
    """Calculate XP required for a specific level"""
    return level * level * 100

def calculate_xp_for_next_level(current_xp: int, current_level: int) -> int:
    """Calculate XP needed for next level"""
    next_level_xp = calculate_level_xp(current_level + 1)
    return next_level_xp - current_xp

def parse_bet_amount(bet_input: str, user_balance: int) -> int:
    """Parse bet amount from user input"""
    bet_input = bet_input.lower().strip()
    
    # Handle special cases
    if bet_input in ['all', 'max']:
        return user_balance
    elif bet_input in ['half', '50%']:
        return user_balance // 2
    elif bet_input in ['quarter', '25%']:
        return user_balance // 4
    elif bet_input.endswith('%'):
        try:
            percentage = float(bet_input[:-1])
            if 0 <= percentage <= 100:
                return int(user_balance * (percentage / 100))
        except ValueError:
            pass
    elif bet_input.endswith('k'):
        try:
            return int(float(bet_input[:-1]) * 1000)
        except ValueError:
            pass
    elif bet_input.endswith('m'):
        try:
            return int(float(bet_input[:-1]) * 1000000)
        except ValueError:
            pass
    
    # Try to parse as regular integer
    try:
        return int(bet_input)
    except ValueError:
        raise ValueError("Invalid bet amount format")

def validate_bet_amount(amount: int, min_bet: int = 1, max_bet: int = None) -> bool:
    """Validate bet amount"""
    if amount < min_bet:
        return False
    if max_bet and amount > max_bet:
        return False
    return True

def get_random_flavor_text(category: str) -> str:
    """Get random flavor text for various situations"""
    texts = {
        'win': [
            "🎉 Congratulations!",
            "🌟 Amazing!",
            "🔥 You're on fire!",
            "💫 Incredible!",
            "⚡ Lightning fast!",
            "🚀 To the moon!",
            "🎊 Fantastic!",
            "💎 Diamond hands!",
            "🏆 Champion!",
            "⭐ Stellar!"
        ],
        'lose': [
            "😢 Better luck next time!",
            "🍀 The luck will turn around!",
            "💪 Don't give up!",
            "🎯 So close!",
            "🔄 Try again!",
            "⚡ Lightning might strike twice!",
            "🎲 The dice will favor you!",
            "🌟 Your moment will come!",
            "💫 Keep trying!",
            "🎪 The show must go on!"
        ],
        'jackpot': [
            "🎰 JACKPOT! 🎰",
            "💥 MEGA WIN! 💥",
            "🌟 SUPERSTAR! 🌟",
            "🔥 BLAZING! 🔥",
            "⚡ ELECTRIC! ⚡",
            "💎 DIAMOND! 💎",
            "🚀 ROCKET! 🚀",
            "🎊 PARTY TIME! 🎊"
        ]
    }
    
    return random.choice(texts.get(category, ['Nice!']))

def create_leaderboard_embed(title: str, entries: List[Dict], guild: discord.Guild, 
                           category: str = "balance") -> discord.Embed:
    """Create a leaderboard embed"""
    embed = discord.Embed(
        title=f"🏆 {title}",
        color=0xf1c40f
    )
    
    if not entries:
        embed.description = "No data available yet!"
        return embed
    
    description = ""
    medals = ["🥇", "🥈", "🥉"]
    
    for i, entry in enumerate(entries[:10]):  # Top 10
        try:
            user = guild.get_member(entry['user_id'])
            username = user.display_name if user else f"User {entry['user_id']}"
        except:
            username = f"User {entry['user_id']}"
        
        medal = medals[i] if i < 3 else f"**{i+1}.**"
        value = entry['value']
        
        if category in ['balance', 'crypto_balance']:
            value_str = format_currency(value, "coins" if category == "balance" else "gems")
        else:
            value_str = f"{value:,}"
        
        description += f"{medal} {username} - {value_str}\n"
    
    embed.description = description
    return embed

def is_admin(member: discord.Member, guild_config: Dict) -> bool:
    """Check if member is admin based on permissions or guild config"""
    # Check Discord permissions
    if member.guild_permissions.administrator:
        return True
    
    # Check guild config admin list
    admin_ids = guild_config.get('admin_ids', [])
    if isinstance(admin_ids, str):
        try:
            import json
            admin_ids = json.loads(admin_ids)
        except:
            admin_ids = []
    
    return member.id in admin_ids

def format_time_delta(seconds: int) -> str:
    """Format time delta into human readable string"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h" if hours > 0 else f"{days}d"

def clamp(value: int, min_val: int, max_val: int) -> int:
    """Clamp value between min and max"""
    return max(min_val, min(value, max_val))

def weighted_random_choice(choices: Dict[str, float]) -> str:
    """Make a weighted random choice from a dictionary"""
    total_weight = sum(choices.values())
    random_value = random.uniform(0, total_weight)
    
    current_weight = 0
    for choice, weight in choices.items():
        current_weight += weight
        if random_value <= current_weight:
            return choice
    
    # Fallback to first choice
    return list(choices.keys())[0]
