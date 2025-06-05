"""
Player-focused commands (profile, balance, rewards, etc.)
"""

import discord
from discord.ext import commands
from discord import app_commands
from economy.economy import EconomyManager
from economy.rewards import RewardManager
from economy.shop import ShopManager
from utils.cooldowns import CooldownManager
from utils.helpers import *
import logging

logger = logging.getLogger(__name__)

class PlayerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.economy = EconomyManager(bot.db)
        self.rewards = RewardManager(bot.db)
        self.shop = ShopManager(bot.db)
        self.cooldowns = CooldownManager(bot.db)
    
    @app_commands.command(name="profile", description="View your player profile")
    @app_commands.describe(page="Page number for profile sections")
    async def profile(self, interaction: discord.Interaction, page: int = 1):
        """Display user profile with stats"""
        await interaction.response.defer()
        
        try:
            user_stats = await self.economy.get_user_stats(interaction.user.id, interaction.guild.id)
            
            if not user_stats:
                await interaction.followup.send(embed=create_error_embed("Profile not found!"))
                return
            
            user_data = user_stats['user_data']
            game_stats = user_stats['game_stats']
            net_profit = user_stats['net_profit']
            
            # Calculate level progress
            current_xp = user_data['experience']
            current_level = user_data['level']
            next_level_xp = calculate_level_xp(current_level + 1)
            xp_needed = next_level_xp - current_xp
            level_progress = current_xp / next_level_xp if next_level_xp > 0 else 1.0
            
            embed = discord.Embed(
                title=f"👤 {interaction.user.display_name}'s Profile",
                color=0x3498db
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            
            if page == 1:
                # Basic info page
                balance_str = format_currency(user_data['balance'], "coins")
                crypto_str = format_currency(user_data['crypto_balance'], "gems")
                
                embed.add_field(
                    name="💰 Wealth",
                    value=f"{balance_str}\n{crypto_str}",
                    inline=True
                )
                
                embed.add_field(
                    name="📊 Statistics",
                    value=f"Level: {current_level}\n"
                          f"Games Played: {user_data['games_played']:,}\n"
                          f"Net Profit: {format_currency(net_profit)}",
                    inline=True
                )
                
                progress_bar = generate_progress_bar(int(level_progress * 10), 10)
                embed.add_field(
                    name="⭐ Level Progress",
                    value=f"Level {current_level} {progress_bar} Level {current_level + 1}\n"
                          f"XP: {current_xp:,} / {next_level_xp:,} ({xp_needed:,} to go)",
                    inline=False
                )
                
                winnings_str = format_currency(user_data['total_winnings'])
                losses_str = format_currency(user_data['total_losses'])
                embed.add_field(
                    name="🎲 Gaming Record",
                    value=f"Total Winnings: {winnings_str}\n"
                          f"Total Losses: {losses_str}\n"
                          f"Prestige Level: {user_data['prestige']}",
                    inline=False
                )
                
            elif page == 2 and game_stats:
                # Game stats page
                embed.title += " - Game Statistics"
                
                for i, stat in enumerate(game_stats[:6]):  # Show up to 6 games
                    game_name = stat['game'].title()
                    played = stat['played']
                    won = stat['won']
                    win_rate = stat['win_rate']
                    streak = stat['best_streak']
                    
                    embed.add_field(
                        name=f"🎮 {game_name}",
                        value=f"Played: {played:,}\n"
                              f"Won: {won:,} ({win_rate}%)\n"
                              f"Best Streak: {streak}",
                        inline=True
                    )
            
            else:
                embed.description = "No additional profile data available."
            
            # Footer
            if len(game_stats) > 0 and page == 1:
                embed.set_footer(text="Use `/profile 2` to see game statistics")
            else:
                embed.set_footer(text=f"Member since {user_data['created_at'][:10]}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in profile command: {e}")
            await interaction.followup.send(embed=create_error_embed("Failed to load profile"))
    
    @app_commands.command(name="balance", description="Check your current balance")
    async def balance(self, interaction: discord.Interaction):
        """Display user balance"""
        try:
            balance_data = await self.economy.get_user_balance(interaction.user.id, interaction.guild.id)
            
            coins = format_currency(balance_data['balance'], "coins")
            gems = format_currency(balance_data['crypto_balance'], "gems")
            
            embed = discord.Embed(
                title="💰 Your Balance",
                color=0x2ecc71
            )
            embed.add_field(name="Coins", value=coins, inline=True)
            embed.add_field(name="Gems", value=gems, inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in balance command: {e}")
            await interaction.response.send_message(embed=create_error_embed("Failed to check balance"))
    
    @app_commands.command(name="daily", description="Claim your daily reward")
    async def daily(self, interaction: discord.Interaction):
        """Claim daily reward"""
        try:
            result = await self.rewards.claim_daily_reward(interaction.user.id, interaction.guild.id)
            
            if result["success"]:
                embed = create_success_embed(result["message"])
                await self.cooldowns.set_cooldown(interaction.user.id, interaction.guild.id, "daily")
            else:
                embed = create_error_embed(result["message"])
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in daily command: {e}")
            await interaction.response.send_message(embed=create_error_embed("Failed to claim daily reward"))
    
    @app_commands.command(name="weekly", description="Claim your weekly reward")
    async def weekly(self, interaction: discord.Interaction):
        """Claim weekly reward"""
        try:
            result = await self.rewards.claim_weekly_reward(interaction.user.id, interaction.guild.id)
            
            if result["success"]:
                embed = create_success_embed(result["message"])
                await self.cooldowns.set_cooldown(interaction.user.id, interaction.guild.id, "weekly")
            else:
                embed = create_error_embed(result["message"])
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in weekly command: {e}")
            await interaction.response.send_message(embed=create_error_embed("Failed to claim weekly reward"))
    
    @app_commands.command(name="monthly", description="Claim your monthly reward")
    async def monthly(self, interaction: discord.Interaction):
        """Claim monthly reward"""
        try:
            result = await self.rewards.claim_monthly_reward(interaction.user.id, interaction.guild.id)
            
            if result["success"]:
                embed = create_success_embed(result["message"])
                await self.cooldowns.set_cooldown(interaction.user.id, interaction.guild.id, "monthly")
            else:
                embed = create_error_embed(result["message"])
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in monthly command: {e}")
            await interaction.response.send_message(embed=create_error_embed("Failed to claim monthly reward"))
    
    @app_commands.command(name="work", description="Work to earn some money")
    async def work(self, interaction: discord.Interaction):
        """Work for money"""
        try:
            result = await self.rewards.claim_work_reward(interaction.user.id, interaction.guild.id)
            
            if result["success"]:
                embed = create_success_embed(result["message"])
                await self.cooldowns.set_cooldown(interaction.user.id, interaction.guild.id, "work")
            else:
                embed = create_error_embed(result["message"])
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in work command: {e}")
            await interaction.response.send_message(embed=create_error_embed("Failed to work"))
    
    @app_commands.command(name="cooldowns", description="Check your command cooldowns")
    @app_commands.describe(detailed="Show detailed cooldown information")
    async def cooldowns(self, interaction: discord.Interaction, detailed: bool = False):
        """Show user cooldowns"""
        try:
            cooldown_text = await self.cooldowns.format_user_cooldowns(
                interaction.user.id, interaction.guild.id, detailed
            )
            
            embed = create_info_embed("Cooldowns", cooldown_text)
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in cooldowns command: {e}")
            await interaction.response.send_message(embed=create_error_embed("Failed to check cooldowns"))
    
    @app_commands.command(name="shop", description="Browse the shop")
    @app_commands.describe(
        shop_type="Category of items to view",
        page="Page number"
    )
    async def shop(self, interaction: discord.Interaction, shop_type: str = None, page: int = 1):
        """Display shop"""
        try:
            shop_display = self.shop.format_shop_display(shop_type, page)
            
            embed = create_info_embed("Shop", shop_display)
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in shop command: {e}")
            await interaction.response.send_message(embed=create_error_embed("Failed to load shop"))
    
    @app_commands.command(name="buy", description="Buy an item from the shop")
    @app_commands.describe(
        item_id="ID of the item to buy",
        amount="Quantity to purchase"
    )
    async def buy(self, interaction: discord.Interaction, item_id: str, amount: int = 1):
        """Buy item from shop"""
        try:
            if amount <= 0:
                await interaction.response.send_message(embed=create_error_embed("Amount must be positive!"))
                return
            
            result = await self.shop.purchase_item(interaction.user.id, interaction.guild.id, item_id, amount)
            
            if result["success"]:
                embed = create_success_embed(result["message"])
            else:
                embed = create_error_embed(result["message"])
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in buy command: {e}")
            await interaction.response.send_message(embed=create_error_embed("Failed to purchase item"))
    
    @app_commands.command(name="inventory", description="View your inventory")
    @app_commands.describe(page="Page number")
    async def inventory(self, interaction: discord.Interaction, page: int = 1):
        """Display user inventory"""
        try:
            user_items = await self.shop.get_user_items(interaction.user.id, interaction.guild.id)
            inventory_display = self.shop.format_inventory_display(user_items, page)
            
            embed = create_info_embed("Inventory", inventory_display)
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in inventory command: {e}")
            await interaction.response.send_message(embed=create_error_embed("Failed to load inventory"))
    
    @app_commands.command(name="sell", description="Sell an item from your inventory")
    @app_commands.describe(
        item_id="ID of the item to sell",
        amount="Quantity to sell"
    )
    async def sell(self, interaction: discord.Interaction, item_id: str, amount: int = 1):
        """Sell item from inventory"""
        try:
            if amount <= 0:
                await interaction.response.send_message(embed=create_error_embed("Amount must be positive!"))
                return
            
            result = await self.shop.sell_item(interaction.user.id, interaction.guild.id, item_id, amount)
            
            if result["success"]:
                embed = create_success_embed(result["message"])
            else:
                embed = create_error_embed(result["message"])
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in sell command: {e}")
            await interaction.response.send_message(embed=create_error_embed("Failed to sell item"))
    
    @app_commands.command(name="send", description="Send money to another user")
    @app_commands.describe(
        recipient="User to send money to",
        amount="Amount to send"
    )
    async def send(self, interaction: discord.Interaction, recipient: discord.Member, amount: int):
        """Send money to another user"""
        try:
            if amount <= 0:
                await interaction.response.send_message(embed=create_error_embed("Amount must be positive!"))
                return
            
            if recipient.id == interaction.user.id:
                await interaction.response.send_message(embed=create_error_embed("You can't send money to yourself!"))
                return
            
            if recipient.bot:
                await interaction.response.send_message(embed=create_error_embed("You can't send money to bots!"))
                return
            
            success = await self.economy.transfer_money(
                interaction.user.id, recipient.id, interaction.guild.id, amount
            )
            
            if success:
                embed = create_success_embed(
                    f"Successfully sent {format_currency(amount)} to {recipient.display_name}!"
                )
            else:
                embed = create_error_embed("Insufficient balance!")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in send command: {e}")
            await interaction.response.send_message(embed=create_error_embed("Failed to send money"))
    
    @app_commands.command(name="leaderboard", description="View server leaderboards")
    @app_commands.describe(
        category="Leaderboard category",
        global_view="Show global leaderboard instead of server"
    )
    async def leaderboard(self, interaction: discord.Interaction, 
                         category: str = "balance", global_view: bool = False):
        """Display leaderboard"""
        try:
            await interaction.response.defer()
            
            if global_view:
                # For global leaderboard, we'd need cross-guild data
                # For now, just show server leaderboard
                await interaction.followup.send(embed=create_error_embed("Global leaderboards not yet implemented"))
                return
            
            # Get leaderboard data
            leaderboard_data = await self.bot.db.get_leaderboard(interaction.guild.id, category, 10)
            
            if not leaderboard_data:
                await interaction.followup.send(embed=create_error_embed("No leaderboard data available"))
                return
            
            # Create leaderboard embed
            embed = create_leaderboard_embed(
                f"{category.title()} Leaderboard",
                leaderboard_data,
                interaction.guild,
                category
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in leaderboard command: {e}")
            await interaction.followup.send(embed=create_error_embed("Failed to load leaderboard"))