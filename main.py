#!/usr/bin/env python3
"""
Discord Economy and Casino Bot - Main Entry Point
"""

import asyncio
import logging
import os
import sys
from bot import EconomyBot
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main function to start the bot"""
    try:
        # Get Discord bot token from environment
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            logger.error("DISCORD_TOKEN environment variable not set!")
            return
        
        # Initialize and start the bot
        bot = EconomyBot()
        await bot.setup()
        await bot.start(token)
        
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error starting bot: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
