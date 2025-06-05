"""
Administrative commands for guild management
"""

import discord
from discord.ext import commands
from discord import app_commands
from utils.helpers import *
import json
import logging

logger = logging.getLogger(__name__)

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def _check_admin_permissions(self, interaction: discord.Interaction) -> bool:
        """Check if user has admin permissions"""
        # Check Discord permissions
        if interaction.user.guild_permissions.administrator:
            return True
        
        # Check bot's admin list
        guild_config = await self.bot.db.get_guild_config(interaction.guild.id)
        admin_ids = guild_config.get('admin_ids', '[]')
        
        try:
            if isinstance(admin_ids, str):
                admin_ids = json.loads(admin_ids)
            return interaction.user.id in admin_ids
        except:
            return False
    
    @app_commands.command(name="config", description="View or modify server configuration")
    @app_commands.describe(
        action="Action to perform: show, set",
        setting="Setting to modify",
        value="New value for the setting"
    )
    async def config(self, interaction: discord.Interaction, 
                    action: str = "show", setting: str = None, value: str = None):
        """Configure server settings"""
        try:
            if not await self._check_admin_permissions(interaction):
                await interaction.response.send_message(
                    embed=create_error_embed("❌ You need administrator permissions to use this command!")
                )
                return
            
            guild_config = await self.bot.db.get_guild_config(interaction.guild.id)
            
            if action.lower() == "show":
                # Display current configuration
                admin_ids = guild_config.get('admin_ids', '[]')
                try:
                    if isinstance(admin_ids, str):
                        admin_ids = json.loads(admin_ids)
                except:
                    admin_ids = []
                
                # Get admin usernames
                admin_names = []
                for admin_id in admin_ids:
                    member = interaction.guild.get_member(admin_id)
                    admin_names.append(member.display_name if member else f"User {admin_id}")
                
                embed = discord.Embed(
                    title="⚙️ Server Configuration",
                    color=0x3498db
                )
                
                embed.add_field(
                    name="💰 Economy Settings",
                    value=f"Cash Name: {guild_config.get('cash_name', 'coins')}\n"
                          f"Cash Emoji: {guild_config.get('cash_emoji', '💰')}\n"
                          f"Crypto Name: {guild_config.get('crypto_name', 'gems')}\n"
                          f"Crypto Emoji: {guild_config.get('crypto_emoji', '💎')}",
                    inline=False
                )
                
                embed.add_field(
                    name="👑 Administrators",
                    value=", ".join(admin_names) if admin_names else "None (using Discord permissions)",
                    inline=False
                )
                
                embed.add_field(
                    name="🔔 Notifications",
                    value="Enabled" if guild_config.get('update_messages_enabled', 1) else "Disabled",
                    inline=True
                )
                
                embed.set_footer(text="Use `/config set <setting> <value>` to modify settings")
                
            elif action.lower() == "set":
                if not setting or not value:
                    await interaction.response.send_message(
                        embed=create_error_embed("Please specify both setting and value!")
                    )
                    return
                
                setting = setting.lower()
                valid_settings = [
                    'cash_name', 'cash_emoji', 'crypto_name', 'crypto_emoji', 
                    'update_messages_enabled'
                ]
                
                if setting not in valid_settings:
                    await interaction.response.send_message(
                        embed=create_error_embed(f"Invalid setting! Valid options: {', '.join(valid_settings)}")
                    )
                    return
                
                # Handle boolean settings
                if setting == 'update_messages_enabled':
                    value = 1 if value.lower() in ['true', 'yes', '1', 'on', 'enabled'] else 0
                
                # Update the setting
                await self.bot.db.update_guild_config(interaction.guild.id, **{setting: value})
                
                embed = create_success_embed(f"✅ Updated {setting} to: {value}")
            
            else:
                embed = create_error_embed("Invalid action! Use 'show' or 'set'")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in config command: {e}")
            await interaction.response.send_message(embed=create_error_embed("Failed to access configuration"))
    
    @app_commands.command(name="admin_add", description="Add a user to the bot's admin list")
    @app_commands.describe(user="User to add as admin")
    async def admin_add(self, interaction: discord.Interaction, user: discord.Member):
        """Add user to admin list"""
        try:
            if not await self._check_admin_permissions(interaction):
                await interaction.response.send_message(
                    embed=create_error_embed("❌ You need administrator permissions to use this command!")
                )
                return
            
            guild_config = await self.bot.db.get_guild_config(interaction.guild.id)
            admin_ids = guild_config.get('admin_ids', '[]')
            
            try:
                if isinstance(admin_ids, str):
                    admin_ids = json.loads(admin_ids)
            except:
                admin_ids = []
            
            if user.id in admin_ids:
                await interaction.response.send_message(
                    embed=create_error_embed(f"{user.display_name} is already an admin!")
                )
                return
            
            admin_ids.append(user.id)
            await self.bot.db.update_guild_config(
                interaction.guild.id, 
                admin_ids=json.dumps(admin_ids)
            )
            
            embed = create_success_embed(f"✅ Added {user.display_name} as a bot administrator!")
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in admin_add command: {e}")
            await interaction.response.send_message(embed=create_error_embed("Failed to add admin"))
    
    @app_commands.command(name="admin_remove", description="Remove a user from the bot's admin list")
    @app_commands.describe(user="User to remove from admin list")
    async def admin_remove(self, interaction: discord.Interaction, user: discord.Member):
        """Remove user from admin list"""
        try:
            if not await self._check_admin_permissions(interaction):
                await interaction.response.send_message(
                    embed=create_error_embed("❌ You need administrator permissions to use this command!")
                )
                return
            
            guild_config = await self.bot.db.get_guild_config(interaction.guild.id)
            admin_ids = guild_config.get('admin_ids', '[]')
            
            try:
                if isinstance(admin_ids, str):
                    admin_ids = json.loads(admin_ids)
            except:
                admin_ids = []
            
            if user.id not in admin_ids:
                await interaction.response.send_message(
                    embed=create_error_embed(f"{user.display_name} is not in the admin list!")
                )
                return
            
            admin_ids.remove(user.id)
            await self.bot.db.update_guild_config(
                interaction.guild.id, 
                admin_ids=json.dumps(admin_ids)
            )
            
            embed = create_success_embed(f"✅ Removed {user.display_name} from bot administrators!")
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in admin_remove command: {e}")
            await interaction.response.send_message(embed=create_error_embed("Failed to remove admin"))
    
    @app_commands.command(name="give_money", description="Give money to a user (Admin only)")
    @app_commands.describe(
        user="User to give money to",
        amount="Amount to give",
        currency="Type of currency: coins or gems"
    )
    async def give_money(self, interaction: discord.Interaction, 
                        user: discord.Member, amount: int, currency: str = "coins"):
        """Give money to a user"""
        try:
            if not await self._check_admin_permissions(interaction):
                await interaction.response.send_message(
                    embed=create_error_embed("❌ You need administrator permissions to use this command!")
                )
                return
            
            if amount <= 0:
                await interaction.response.send_message(
                    embed=create_error_embed("Amount must be positive!")
                )
                return
            
            if user.bot:
                await interaction.response.send_message(
                    embed=create_error_embed("Cannot give money to bots!")
                )
                return
            
            # Determine currency type
            currency_type = "crypto_balance" if currency.lower() in ["gems", "crypto"] else "balance"
            currency_name = "gems" if currency_type == "crypto_balance" else "coins"
            
            # Give the money
            await self.bot.db.update_user_balance(user.id, interaction.guild.id, amount, currency_type)
            
            # Record admin action
            await self.bot.db.add_transaction(
                user.id, interaction.guild.id, "admin_gift", amount,
                f"Admin gift from {interaction.user.display_name}"
            )
            
            embed = create_success_embed(
                f"✅ Gave {format_currency(amount, currency_name)} to {user.display_name}!"
            )
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in give_money command: {e}")
            await interaction.response.send_message(embed=create_error_embed("Failed to give money"))
    
    @app_commands.command(name="take_money", description="Take money from a user (Admin only)")
    @app_commands.describe(
        user="User to take money from",
        amount="Amount to take",
        currency="Type of currency: coins or gems"
    )
    async def take_money(self, interaction: discord.Interaction, 
                        user: discord.Member, amount: int, currency: str = "coins"):
        """Take money from a user"""
        try:
            if not await self._check_admin_permissions(interaction):
                await interaction.response.send_message(
                    embed=create_error_embed("❌ You need administrator permissions to use this command!")
                )
                return
            
            if amount <= 0:
                await interaction.response.send_message(
                    embed=create_error_embed("Amount must be positive!")
                )
                return
            
            if user.bot:
                await interaction.response.send_message(
                    embed=create_error_embed("Cannot take money from bots!")
                )
                return
            
            # Determine currency type
            currency_type = "crypto_balance" if currency.lower() in ["gems", "crypto"] else "balance"
            currency_name = "gems" if currency_type == "crypto_balance" else "coins"
            
            # Check if user has enough
            user_data = await self.bot.db.get_user(user.id, interaction.guild.id)
            if not user_data or user_data[currency_type] < amount:
                current_amount = user_data[currency_type] if user_data else 0
                await interaction.response.send_message(
                    embed=create_error_embed(
                        f"{user.display_name} only has {format_currency(current_amount, currency_name)}!"
                    )
                )
                return
            
            # Take the money
            await self.bot.db.update_user_balance(user.id, interaction.guild.id, -amount, currency_type)
            
            # Record admin action
            await self.bot.db.add_transaction(
                user.id, interaction.guild.id, "admin_deduct", amount,
                f"Admin deduction by {interaction.user.display_name}"
            )
            
            embed = create_success_embed(
                f"✅ Took {format_currency(amount, currency_name)} from {user.display_name}!"
            )
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in take_money command: {e}")
            await interaction.response.send_message(embed=create_error_embed("Failed to take money"))
    
    @app_commands.command(name="reset_user", description="Reset a user's data (Admin only)")
    @app_commands.describe(user="User to reset")
    async def reset_user(self, interaction: discord.Interaction, user: discord.Member):
        """Reset a user's data"""
        try:
            if not await self._check_admin_permissions(interaction):
                await interaction.response.send_message(
                    embed=create_error_embed("❌ You need administrator permissions to use this command!")
                )
                return
            
            if user.bot:
                await interaction.response.send_message(
                    embed=create_error_embed("Cannot reset bot data!")
                )
                return
            
            # Reset user data
            await self.bot.db.connection.execute(
                "DELETE FROM users WHERE user_id = ? AND guild_id = ?",
                (user.id, interaction.guild.id)
            )
            await self.bot.db.connection.execute(
                "DELETE FROM user_items WHERE user_id = ? AND guild_id = ?",
                (user.id, interaction.guild.id)
            )
            await self.bot.db.connection.execute(
                "DELETE FROM cooldowns WHERE user_id = ? AND guild_id = ?",
                (user.id, interaction.guild.id)
            )
            await self.bot.db.connection.execute(
                "DELETE FROM game_stats WHERE user_id = ? AND guild_id = ?",
                (user.id, interaction.guild.id)
            )
            await self.bot.db.connection.execute(
                "DELETE FROM transactions WHERE user_id = ? AND guild_id = ?",
                (user.id, interaction.guild.id)
            )
            await self.bot.db.connection.commit()
            
            embed = create_success_embed(f"✅ Reset all data for {user.display_name}!")
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in reset_user command: {e}")
            await interaction.response.send_message(embed=create_error_embed("Failed to reset user"))
    
    @app_commands.command(name="server_stats", description="Display server statistics (Admin only)")
    async def server_stats(self, interaction: discord.Interaction):
        """Display server statistics"""
        try:
            if not await self._check_admin_permissions(interaction):
                await interaction.response.send_message(
                    embed=create_error_embed("❌ You need administrator permissions to use this command!")
                )
                return
            
            await interaction.response.defer()
            
            # Get server statistics
            async with self.bot.db.connection.execute(
                "SELECT COUNT(*) FROM users WHERE guild_id = ?",
                (interaction.guild.id,)
            ) as cursor:
                total_users = (await cursor.fetchone())[0]
            
            async with self.bot.db.connection.execute(
                "SELECT SUM(balance), SUM(crypto_balance), SUM(games_played) FROM users WHERE guild_id = ?",
                (interaction.guild.id,)
            ) as cursor:
                row = await cursor.fetchone()
                total_coins = row[0] or 0
                total_gems = row[1] or 0
                total_games = row[2] or 0
            
            async with self.bot.db.connection.execute(
                "SELECT COUNT(*) FROM transactions WHERE guild_id = ?",
                (interaction.guild.id,)
            ) as cursor:
                total_transactions = (await cursor.fetchone())[0]
            
            embed = discord.Embed(
                title="📊 Server Statistics",
                color=0x3498db
            )
            
            embed.add_field(
                name="👥 Users",
                value=f"Total Users: {total_users:,}",
                inline=True
            )
            
            embed.add_field(
                name="💰 Economy",
                value=f"Total Coins: {total_coins:,}\n"
                      f"Total Gems: {total_gems:,}\n"
                      f"Transactions: {total_transactions:,}",
                inline=True
            )
            
            embed.add_field(
                name="🎮 Gaming",
                value=f"Games Played: {total_games:,}",
                inline=True
            )
            
            embed.set_footer(text=f"Server: {interaction.guild.name}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in server_stats command: {e}")
            await interaction.followup.send(embed=create_error_embed("Failed to get server statistics"))
    
    @app_commands.command(name="updates", description="Send a server update message (Admin only)")
    @app_commands.describe(message="Update message to send")
    async def updates(self, interaction: discord.Interaction, message: str):
        """Send server updates"""
        try:
            if not await self._check_admin_permissions(interaction):
                await interaction.response.send_message(
                    embed=create_error_embed("❌ You need administrator permissions to use this command!")
                )
                return
            
            # Check if updates are enabled
            guild_config = await self.bot.db.get_guild_config(interaction.guild.id)
            if not guild_config.get('update_messages_enabled', 1):
                await interaction.response.send_message(
                    embed=create_error_embed("Update messages are disabled for this server!")
                )
                return
            
            embed = discord.Embed(
                title="📢 Server Update",
                description=message,
                color=0xf39c12
            )
            embed.set_footer(text=f"Update by {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in updates command: {e}")
            await interaction.response.send_message(embed=create_error_embed("Failed to send update"))