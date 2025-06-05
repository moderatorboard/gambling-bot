"""
Daily, weekly, monthly, and yearly reward system
"""

import random
from datetime import datetime, timedelta
from typing import Dict, Optional
from database.database import DatabaseManager

class RewardManager:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def claim_daily_reward(self, user_id: int, guild_id: int) -> Dict:
        """Claim daily reward"""
        user = await self.db.get_user(user_id, guild_id)
        if not user:
            return {"success": False, "message": "User not found"}
        
        # Check if daily reward already claimed
        if user['last_daily']:
            last_daily = datetime.fromisoformat(user['last_daily'])
            if datetime.utcnow() - last_daily < timedelta(hours=20):  # 20 hour cooldown
                remaining = timedelta(hours=24) - (datetime.utcnow() - last_daily)
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                return {
                    "success": False, 
                    "message": f"Daily reward already claimed! Next reward in {hours}h {minutes}m"
                }
        
        # Calculate reward based on streak and level
        base_reward = 100
        level_bonus = user['level'] * 10
        
        # Check for streak bonus
        streak = 1
        if user['last_daily']:
            last_daily = datetime.fromisoformat(user['last_daily'])
            if datetime.utcnow() - last_daily <= timedelta(hours=25):  # Allow 1 hour grace period
                # Streak continues - we'd need to track this in database
                streak = 1  # Simplified for now
        
        streak_bonus = min(streak * 25, 500)  # Max 500 bonus
        random_bonus = random.randint(0, 50)
        
        total_reward = base_reward + level_bonus + streak_bonus + random_bonus
        
        # Add crypto chance (5% chance for 1-5 gems)
        crypto_reward = 0
        if random.random() < 0.05:
            crypto_reward = random.randint(1, 5)
        
        # Update user
        await self.db.update_user_balance(user_id, guild_id, total_reward, "balance")
        if crypto_reward > 0:
            await self.db.update_user_balance(user_id, guild_id, crypto_reward, "crypto_balance")
        
        await self.db.connection.execute(
            "UPDATE users SET last_daily = ? WHERE user_id = ? AND guild_id = ?",
            (datetime.utcnow().isoformat(), user_id, guild_id)
        )
        await self.db.connection.commit()
        
        message = f"🎁 **Daily Reward Claimed!**\n\n"
        message += f"💰 Base reward: {base_reward}\n"
        message += f"📈 Level bonus: {level_bonus}\n"
        message += f"🔥 Streak bonus: {streak_bonus}\n"
        message += f"🎲 Random bonus: {random_bonus}\n"
        message += f"**Total: {total_reward} coins**"
        
        if crypto_reward > 0:
            message += f"\n💎 Bonus: {crypto_reward} gems!"
        
        return {
            "success": True,
            "message": message,
            "reward": total_reward,
            "crypto_reward": crypto_reward,
            "streak": streak
        }
    
    async def claim_weekly_reward(self, user_id: int, guild_id: int) -> Dict:
        """Claim weekly reward"""
        user = await self.db.get_user(user_id, guild_id)
        if not user:
            return {"success": False, "message": "User not found"}
        
        # Check cooldown
        if user['last_weekly']:
            last_weekly = datetime.fromisoformat(user['last_weekly'])
            if datetime.utcnow() - last_weekly < timedelta(days=7):
                remaining = timedelta(days=7) - (datetime.utcnow() - last_weekly)
                days = remaining.days
                hours = int(remaining.seconds // 3600)
                return {
                    "success": False,
                    "message": f"Weekly reward already claimed! Next reward in {days}d {hours}h"
                }
        
        # Calculate weekly reward
        base_reward = 1000
        level_bonus = user['level'] * 50
        games_bonus = min(user['games_played'] * 5, 2000)
        
        total_reward = base_reward + level_bonus + games_bonus
        crypto_reward = random.randint(5, 15)
        
        # Update user
        await self.db.update_user_balance(user_id, guild_id, total_reward, "balance")
        await self.db.update_user_balance(user_id, guild_id, crypto_reward, "crypto_balance")
        
        await self.db.connection.execute(
            "UPDATE users SET last_weekly = ? WHERE user_id = ? AND guild_id = ?",
            (datetime.utcnow().isoformat(), user_id, guild_id)
        )
        await self.db.connection.commit()
        
        message = f"🎁 **Weekly Reward Claimed!**\n\n"
        message += f"💰 Base reward: {base_reward}\n"
        message += f"📈 Level bonus: {level_bonus}\n"
        message += f"🎮 Games bonus: {games_bonus}\n"
        message += f"**Total: {total_reward} coins**\n"
        message += f"💎 **{crypto_reward} gems**"
        
        return {
            "success": True,
            "message": message,
            "reward": total_reward,
            "crypto_reward": crypto_reward
        }
    
    async def claim_monthly_reward(self, user_id: int, guild_id: int) -> Dict:
        """Claim monthly reward"""
        user = await self.db.get_user(user_id, guild_id)
        if not user:
            return {"success": False, "message": "User not found"}
        
        # Check cooldown
        if user['last_monthly']:
            last_monthly = datetime.fromisoformat(user['last_monthly'])
            if datetime.utcnow() - last_monthly < timedelta(days=30):
                remaining = timedelta(days=30) - (datetime.utcnow() - last_monthly)
                days = remaining.days
                return {
                    "success": False,
                    "message": f"Monthly reward already claimed! Next reward in {days} days"
                }
        
        # Calculate monthly reward
        base_reward = 5000
        level_bonus = user['level'] * 200
        prestige_bonus = user['prestige'] * 1000
        
        total_reward = base_reward + level_bonus + prestige_bonus
        crypto_reward = random.randint(25, 50)
        
        # Special item chance
        special_item = None
        if random.random() < 0.3:  # 30% chance
            special_item = random.choice(["luck_boost", "double_xp", "protection"])
        
        # Update user
        await self.db.update_user_balance(user_id, guild_id, total_reward, "balance")
        await self.db.update_user_balance(user_id, guild_id, crypto_reward, "crypto_balance")
        
        if special_item:
            # Add special item (would need shop manager)
            pass
        
        await self.db.connection.execute(
            "UPDATE users SET last_monthly = ? WHERE user_id = ? AND guild_id = ?",
            (datetime.utcnow().isoformat(), user_id, guild_id)
        )
        await self.db.connection.commit()
        
        message = f"🎁 **Monthly Reward Claimed!**\n\n"
        message += f"💰 Base reward: {base_reward}\n"
        message += f"📈 Level bonus: {level_bonus}\n"
        message += f"⭐ Prestige bonus: {prestige_bonus}\n"
        message += f"**Total: {total_reward} coins**\n"
        message += f"💎 **{crypto_reward} gems**"
        
        if special_item:
            message += f"\n🎉 Bonus item: {special_item}!"
        
        return {
            "success": True,
            "message": message,
            "reward": total_reward,
            "crypto_reward": crypto_reward,
            "special_item": special_item
        }
    
    async def claim_work_reward(self, user_id: int, guild_id: int) -> Dict:
        """Claim work reward (4 hour cooldown)"""
        user = await self.db.get_user(user_id, guild_id)
        if not user:
            return {"success": False, "message": "User not found"}
        
        # Check cooldown
        if user['last_work']:
            last_work = datetime.fromisoformat(user['last_work'])
            if datetime.utcnow() - last_work < timedelta(hours=4):
                remaining = timedelta(hours=4) - (datetime.utcnow() - last_work)
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                return {
                    "success": False,
                    "message": f"You're tired from working! Rest for {hours}h {minutes}m"
                }
        
        # Work rewards
        work_types = [
            {"name": "Office Job", "min": 50, "max": 150, "flavor": "You filed some paperwork"},
            {"name": "Delivery", "min": 75, "max": 200, "flavor": "You delivered packages around town"},
            {"name": "Construction", "min": 100, "max": 250, "flavor": "You helped build something"},
            {"name": "Restaurant", "min": 60, "max": 180, "flavor": "You served customers"},
            {"name": "Freelance", "min": 25, "max": 300, "flavor": "You completed a project"}
        ]
        
        job = random.choice(work_types)
        base_reward = random.randint(job["min"], job["max"])
        level_bonus = user['level'] * 5
        total_reward = base_reward + level_bonus
        
        # Small chance for extra reward
        bonus_message = ""
        if random.random() < 0.1:  # 10% chance
            bonus = random.randint(50, 200)
            total_reward += bonus
            bonus_message = f"\n💡 You worked extra hard! +{bonus} bonus"
        
        # Update user
        await self.db.update_user_balance(user_id, guild_id, total_reward, "balance")
        await self.db.connection.execute(
            "UPDATE users SET last_work = ? WHERE user_id = ? AND guild_id = ?",
            (datetime.utcnow().isoformat(), user_id, guild_id)
        )
        await self.db.connection.commit()
        
        message = f"💼 **{job['name']}**\n\n"
        message += f"{job['flavor']}\n"
        message += f"💰 Earned: {total_reward} coins"
        message += bonus_message
        
        return {
            "success": True,
            "message": message,
            "reward": total_reward,
            "job": job["name"]
        }
