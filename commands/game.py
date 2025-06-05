"""
Game-focused commands (blackjack, coinflip, slots, dice, etc.)
"""

import discord
from discord.ext import commands
from discord import app_commands
from economy.economy import EconomyManager
from utils.cooldowns import CooldownManager
from utils.helpers import *
from games.blackjack import play_blackjack
from games.coinflip import play_coinflip, get_coinflip_help
from games.slots import play_slots, get_slots_help
from games.dice import play_dice_roll, play_single_dice, get_dice_help
import logging
import random

logger = logging.getLogger(__name__)

class GameCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.economy = EconomyManager(bot.db)
        self.cooldowns = CooldownManager(bot.db)
        
        # Minimum bet amounts
        self.min_bets = {
            'blackjack': 10,
            'coinflip': 1,
            'slots': 5,
            'dice': 1,
            'gamble': 1
        }
    
    async def _validate_bet(self, interaction: discord.Interaction, bet_input: str, game: str) -> tuple:
        """Validate bet amount and user balance"""
        try:
            # Get user balance
            balance_data = await self.economy.get_user_balance(interaction.user.id, interaction.guild.id)
            user_balance = balance_data['balance']
            
            # Parse bet amount
            bet_amount = parse_bet_amount(bet_input, user_balance)
            
            # Validate bet amount
            min_bet = self.min_bets.get(game, 1)
            if bet_amount < min_bet:
                return False, f"Minimum bet is {format_currency(min_bet)}", 0
            
            if bet_amount > user_balance:
                return False, f"You only have {format_currency(user_balance)}", 0
            
            # Check cooldown
            cooldown_remaining = await self.cooldowns.check_cooldown(
                interaction.user.id, interaction.guild.id, game
            )
            if cooldown_remaining:
                time_str = self.cooldowns.format_cooldown_time(cooldown_remaining)
                return False, f"⏰ {game.title()} is on cooldown for {time_str}", 0
            
            return True, "", bet_amount
            
        except ValueError as e:
            return False, f"Invalid bet amount: {str(e)}", 0
        except Exception as e:
            logger.error(f"Error validating bet: {e}")
            return False, "Failed to validate bet", 0
    
    async def _process_game_result(self, interaction: discord.Interaction, game_name: str, 
                                 bet_amount: int, result, set_cooldown: bool = True):
        """Process game result and update user balance"""
        try:
            # Process the game economically
            await self.economy.process_game_result(
                interaction.user.id, interaction.guild.id, game_name,
                bet_amount, result.won, result.amount_won
            )
            
            # Set cooldown if requested
            if set_cooldown:
                await self.cooldowns.set_cooldown(interaction.user.id, interaction.guild.id, game_name)
            
            # Add XP for playing
            xp_gained = 5 + (bet_amount // 100)  # Base XP + bonus based on bet
            if result.won:
                xp_gained *= 2  # Double XP for winning
            
            level_result = await self.economy.calculate_level_and_xp(
                interaction.user.id, interaction.guild.id, xp_gained
            )
            
            # Create result message
            message = result.message
            if level_result and level_result['level_up']:
                message += f"\n\n🆙 **LEVEL UP!** You are now level {level_result['new_level']}!"
            
            # Create embed
            if result.won:
                embed = create_success_embed(message)
                embed.color = 0x2ecc71
            else:
                embed = discord.Embed(title="🎮 Game Result", description=message, color=0xe74c3c)
            
            return embed
            
        except ValueError as e:
            return create_error_embed(str(e))
        except Exception as e:
            logger.error(f"Error processing game result: {e}")
            return create_error_embed("Failed to process game result")
    
    @app_commands.command(name="blackjack", description="Play blackjack against the dealer")
    @app_commands.describe(bet="Amount to bet (supports 'all', 'half', percentages, 'k', 'm')")
    async def blackjack(self, interaction: discord.Interaction, bet: str):
        """Play blackjack game"""
        await interaction.response.defer()
        
        try:
            # Validate bet
            valid, error_msg, bet_amount = await self._validate_bet(interaction, bet, 'blackjack')
            if not valid:
                await interaction.followup.send(embed=create_error_embed(error_msg))
                return
            
            # Play the game
            result = await play_blackjack(bet_amount)
            
            # Process result
            embed = await self._process_game_result(interaction, 'blackjack', bet_amount, result)
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in blackjack command: {e}")
            await interaction.followup.send(embed=create_error_embed("Failed to play blackjack"))
    
    @app_commands.command(name="coinflip", description="Flip a coin and bet on the outcome")
    @app_commands.describe(
        prediction="Your prediction: heads, tails, h, or t",
        bet="Amount to bet"
    )
    async def coinflip(self, interaction: discord.Interaction, prediction: str, bet: str):
        """Play coinflip game"""
        await interaction.response.defer()
        
        try:
            # Validate bet
            valid, error_msg, bet_amount = await self._validate_bet(interaction, bet, 'coinflip')
            if not valid:
                await interaction.followup.send(embed=create_error_embed(error_msg))
                return
            
            # Play the game
            result = await play_coinflip(prediction, bet_amount)
            
            # Process result
            embed = await self._process_game_result(interaction, 'coinflip', bet_amount, result)
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in coinflip command: {e}")
            await interaction.followup.send(embed=create_error_embed("Failed to play coinflip"))
    
    @app_commands.command(name="slots", description="Spin the slot machine")
    @app_commands.describe(bet="Amount to bet")
    async def slots(self, interaction: discord.Interaction, bet: str):
        """Play slot machine"""
        await interaction.response.defer()
        
        try:
            # Validate bet
            valid, error_msg, bet_amount = await self._validate_bet(interaction, bet, 'slots')
            if not valid:
                await interaction.followup.send(embed=create_error_embed(error_msg))
                return
            
            # Play the game
            result = await play_slots(bet_amount)
            
            # Process result
            embed = await self._process_game_result(interaction, 'slots', bet_amount, result)
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in slots command: {e}")
            await interaction.followup.send(embed=create_error_embed("Failed to play slots"))
    
    @app_commands.command(name="roll", description="Roll dice and bet on the outcome")
    @app_commands.describe(
        prediction="Your prediction: high, low, lucky7, or exact number (2-12)",
        bet="Amount to bet",
        dice_type="Type of dice game: 'single' for 1 die, 'double' for 2 dice"
    )
    async def roll(self, interaction: discord.Interaction, prediction: str, bet: str, dice_type: str = "double"):
        """Play dice rolling game"""
        await interaction.response.defer()
        
        try:
            # Validate bet
            valid, error_msg, bet_amount = await self._validate_bet(interaction, bet, 'dice')
            if not valid:
                await interaction.followup.send(embed=create_error_embed(error_msg))
                return
            
            # Play the appropriate dice game
            if dice_type.lower() == "single":
                result = await play_single_dice(prediction, bet_amount)
            else:
                result = await play_dice_roll(prediction, bet_amount)
            
            # Process result
            embed = await self._process_game_result(interaction, 'dice', bet_amount, result)
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in roll command: {e}")
            await interaction.followup.send(embed=create_error_embed("Failed to play dice"))
    
    @app_commands.command(name="gamble", description="Simple high-risk gambling game")
    @app_commands.describe(bet="Amount to bet")
    async def gamble(self, interaction: discord.Interaction, bet: str):
        """Simple gambling game with varying odds"""
        await interaction.response.defer()
        
        try:
            # Validate bet
            valid, error_msg, bet_amount = await self._validate_bet(interaction, bet, 'gamble')
            if not valid:
                await interaction.followup.send(embed=create_error_embed(error_msg))
                return
            
            # Gambling outcomes with probabilities
            outcomes = [
                {"chance": 0.45, "multiplier": 2.0, "message": "🎉 You won!"},
                {"chance": 0.20, "multiplier": 1.5, "message": "😊 Small win!"},
                {"chance": 0.10, "multiplier": 3.0, "message": "🔥 Big win!"},
                {"chance": 0.05, "multiplier": 5.0, "message": "⚡ Huge win!"},
                {"chance": 0.02, "multiplier": 10.0, "message": "💎 JACKPOT!"},
                {"chance": 0.18, "multiplier": 0.0, "message": "😢 You lost!"}
            ]
            
            # Determine outcome
            rand = random.random()
            cumulative = 0
            selected_outcome = outcomes[-1]  # Default to loss
            
            for outcome in outcomes:
                cumulative += outcome["chance"]
                if rand <= cumulative:
                    selected_outcome = outcome
                    break
            
            # Calculate result
            won = selected_outcome["multiplier"] > 0
            winnings = int(bet_amount * selected_outcome["multiplier"]) if won else 0
            
            # Create result
            from database.models import GameResult
            result = GameResult(
                won=won,
                amount_won=winnings,
                message=f"🎰 **GAMBLE** 🎰\n\n{selected_outcome['message']}\n" +
                       (f"You win **{winnings}** coins! (x{selected_outcome['multiplier']})" if won 
                        else f"You lose **{bet_amount}** coins!"),
                multiplier=selected_outcome["multiplier"]
            )
            
            # Process result
            embed = await self._process_game_result(interaction, 'gamble', bet_amount, result)
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in gamble command: {e}")
            await interaction.followup.send(embed=create_error_embed("Failed to gamble"))
    
    @app_commands.command(name="rockpaperscissors", description="Play rock paper scissors")
    @app_commands.describe(
        selection="Your choice: rock, paper, or scissors",
        bet="Amount to bet"
    )
    async def rockpaperscissors(self, interaction: discord.Interaction, selection: str, bet: str):
        """Play rock paper scissors"""
        await interaction.response.defer()
        
        try:
            # Validate bet
            valid, error_msg, bet_amount = await self._validate_bet(interaction, bet, 'rockpaperscissors')
            if not valid:
                await interaction.followup.send(embed=create_error_embed(error_msg))
                return
            
            # Validate selection
            selection = selection.lower()
            valid_choices = ['rock', 'paper', 'scissors', 'r', 'p', 's']
            if selection not in valid_choices:
                await interaction.followup.send(embed=create_error_embed(
                    "Invalid selection! Use 'rock', 'paper', 'scissors', 'r', 'p', or 's'"
                ))
                return
            
            # Normalize selection
            choice_map = {'r': 'rock', 'p': 'paper', 's': 'scissors'}
            player_choice = choice_map.get(selection, selection)
            
            # Bot choice
            bot_choice = random.choice(['rock', 'paper', 'scissors'])
            
            # Determine winner
            if player_choice == bot_choice:
                # Tie - return bet
                won = False
                winnings = bet_amount
                outcome = "It's a tie!"
                emoji = "🤝"
            elif (player_choice == 'rock' and bot_choice == 'scissors') or \
                 (player_choice == 'paper' and bot_choice == 'rock') or \
                 (player_choice == 'scissors' and bot_choice == 'paper'):
                # Player wins
                won = True
                winnings = bet_amount * 2
                outcome = "You win!"
                emoji = "🎉"
            else:
                # Player loses
                won = False
                winnings = 0
                outcome = "You lose!"
                emoji = "😢"
            
            # Choice emojis
            choice_emojis = {'rock': '🪨', 'paper': '📄', 'scissors': '✂️'}
            
            message = f"✂️ **ROCK PAPER SCISSORS** ✂️\n\n"
            message += f"You: {choice_emojis[player_choice]} {player_choice.title()}\n"
            message += f"Bot: {choice_emojis[bot_choice]} {bot_choice.title()}\n\n"
            message += f"{emoji} **{outcome}**\n"
            
            if won:
                message += f"You win **{winnings}** coins!"
            elif winnings > 0:  # Tie
                message += f"Your bet of **{bet_amount}** coins is returned."
            else:
                message += f"You lose **{bet_amount}** coins!"
            
            # Create result
            from database.models import GameResult
            result = GameResult(
                won=won,
                amount_won=winnings,
                message=message,
                multiplier=2.0 if won else (1.0 if winnings > 0 else 0.0),
                details={"player": player_choice, "bot": bot_choice, "outcome": outcome}
            )
            
            # Process result
            embed = await self._process_game_result(interaction, 'rockpaperscissors', bet_amount, result)
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in rockpaperscissors command: {e}")
            await interaction.followup.send(embed=create_error_embed("Failed to play rock paper scissors"))
    
    @app_commands.command(name="crash", description="Bet on when the multiplier will crash")
    @app_commands.describe(
        bet="Amount to bet",
        cashout="Multiplier to cash out at (e.g., 1.5, 2.0, 5.0)"
    )
    async def crash(self, interaction: discord.Interaction, bet: str, cashout: float = 2.0):
        """Play crash game"""
        await interaction.response.defer()
        
        try:
            # Validate bet
            valid, error_msg, bet_amount = await self._validate_bet(interaction, bet, 'crash')
            if not valid:
                await interaction.followup.send(embed=create_error_embed(error_msg))
                return
            
            # Validate cashout multiplier
            if cashout < 1.1 or cashout > 50.0:
                await interaction.followup.send(embed=create_error_embed(
                    "Cashout multiplier must be between 1.1 and 50.0"
                ))
                return
            
            # Generate crash point (exponential distribution favoring lower values)
            import math
            rand = random.random()
            # Use exponential distribution to make lower crash points more likely
            crash_point = 1.0 + (-math.log(1 - rand) * 0.8)  # Adjusted for reasonable range
            crash_point = min(crash_point, 100.0)  # Cap at 100x
            
            # Determine if player wins
            won = cashout <= crash_point
            winnings = int(bet_amount * cashout) if won else 0
            
            message = f"🚀 **CRASH GAME** 🚀\n\n"
            message += f"Your cashout: {cashout:.2f}x\n"
            message += f"Crash point: {crash_point:.2f}x\n\n"
            
            if won:
                message += f"🎉 **SAFE CASHOUT!**\n"
                message += f"You win **{winnings}** coins! (x{cashout})"
                emoji = "🎉"
            else:
                message += f"💥 **CRASHED!**\n"
                message += f"You lose **{bet_amount}** coins!"
                emoji = "💥"
            
            # Create result
            from database.models import GameResult
            result = GameResult(
                won=won,
                amount_won=winnings,
                message=message,
                multiplier=cashout if won else 0.0,
                details={"cashout": cashout, "crash_point": crash_point}
            )
            
            # Process result
            embed = await self._process_game_result(interaction, 'crash', bet_amount, result)
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in crash command: {e}")
            await interaction.followup.send(embed=create_error_embed("Failed to play crash"))
    
    @app_commands.command(name="game_help", description="Get help for specific games")
    @app_commands.describe(
        game="Game to get help for: blackjack, coinflip, slots, dice, or all"
    )
    async def game_help(self, interaction: discord.Interaction, 
                       game: str = None):
        """Get help for games"""
        try:
            if not game or game.lower() == "all":
                # Show general game help
                embed = discord.Embed(
                    title="🎮 Game Help",
                    description="Available casino games and their commands:",
                    color=0x3498db
                )
                
                embed.add_field(
                    name="🃏 Blackjack",
                    value="`/blackjack <bet>` - Play against the dealer\nGoal: Get 21 or closest without going over",
                    inline=False
                )
                
                embed.add_field(
                    name="🪙 Coinflip",
                    value="`/coinflip <heads/tails> <bet>` - Flip a coin\nPayout: 2x your bet",
                    inline=False
                )
                
                embed.add_field(
                    name="🎰 Slots",
                    value="`/slots <bet>` - Spin the slot machine\nMatch symbols for big payouts!",
                    inline=False
                )
                
                embed.add_field(
                    name="🎲 Dice",
                    value="`/roll <prediction> <bet>` - Roll dice games\nPredict: high, low, lucky7, or exact numbers",
                    inline=False
                )
                
                embed.add_field(
                    name="🎰 Other Games",
                    value="`/gamble <bet>` - High-risk gambling\n`/rockpaperscissors <choice> <bet>` - Classic RPS\n`/crash <bet> <cashout>` - Crash betting",
                    inline=False
                )
                
                embed.set_footer(text="Use `/game_help <game_name>` for detailed help on specific games")
                
            elif game.lower() == "coinflip":
                embed = create_info_embed("Coinflip Help", get_coinflip_help())
            elif game.lower() == "slots":
                embed = create_info_embed("Slots Help", get_slots_help())
            elif game.lower() in ["dice", "roll"]:
                embed = create_info_embed("Dice Help", get_dice_help())
            elif game.lower() == "blackjack":
                help_text = """
                **🃏 Blackjack Game**
                
                **How to play:**
                `/blackjack <bet>` - Play against the dealer
                
                **Rules:**
                • Goal: Get 21 or closest without going over
                • Face cards (J, Q, K) = 10 points
                • Aces = 11 or 1 (automatically adjusted)
                • Dealer hits on 16, stands on 17
                
                **Payouts:**
                • Blackjack (21 with 2 cards): x2.5
                • Regular win: x2
                • Push (tie): bet returned
                
                **Strategy:**
                • Hit if your total is under 17
                • Stand if 17 or higher
                • Watch the dealer's visible card
                """
                embed = create_info_embed("Blackjack Help", help_text)
            else:
                embed = create_error_embed(f"Unknown game: {game}")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in game_help command: {e}")
            await interaction.response.send_message(embed=create_error_embed("Failed to show game help"))