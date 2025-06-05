"""
Main Discord Bot Class
"""

import discord
from discord.ext import commands, tasks
import logging
import asyncio
from database.database import DatabaseManager
from commands.player import PlayerCommands
from commands.game import GameCommands
from commands.admin import AdminCommands
from config.config import Config

logger = logging.getLogger(__name__)

class EconomyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        self.db = None
        self.config = Config()
        
    async def setup(self):
        """Initialize bot components"""
        try:
            # Initialize database
            self.db = DatabaseManager()
            await self.db.initialize()
            
            # Add cogs
            await self.add_cog(PlayerCommands(self))
            await self.add_cog(GameCommands(self))
            await self.add_cog(AdminCommands(self))
            
            logger.info("Bot setup completed successfully")
            
        except Exception as e:
            logger.error(f"Error during bot setup: {e}")
            raise
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f'Synced {len(synced)} command(s)')
        except Exception as e:
            logger.error(f'Failed to sync commands: {e}')
        
        # Start background tasks
        self.daily_reset.start()
    
    async def on_guild_join(self, guild):
        """Called when bot joins a new guild"""
        logger.info(f'Joined new guild: {guild.name} (ID: {guild.id})')
        await self.db.create_guild_config(guild.id)
    
    async def on_command_error(self, ctx, error):
        """Global error handler"""
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ Command on cooldown. Try again in {error.retry_after:.1f} seconds.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: {error.param}")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Invalid argument provided.")
        else:
            logger.error(f"Unhandled error in {ctx.command}: {error}")
            await ctx.send("❌ An unexpected error occurred.")
    
    @tasks.loop(hours=24)
    async def daily_reset(self):
        """Reset daily cooldowns and process rewards"""
        try:
            await self.db.reset_daily_cooldowns()
            logger.info("Daily cooldowns reset")
        except Exception as e:
            logger.error(f"Error in daily reset: {e}")
    
    async def close(self):
        """Cleanup when bot shuts down"""
        if self.db:
            await self.db.close()
        await super().close()
