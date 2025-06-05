"""
Configuration management for the Discord bot
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class Config:
    """Bot configuration manager"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.default_config = {
            "bot": {
                "name": "Economy Casino Bot",
                "version": "1.0.0",
                "description": "A comprehensive Discord economy and casino bot",
                "prefix": "!",
                "case_insensitive": True,
                "sync_commands_on_startup": True
            },
            "database": {
                "path": "economy_bot.db",
                "backup_enabled": True,
                "backup_interval_hours": 24
            },
            "economy": {
                "starting_balance": 1000,
                "starting_crypto": 0,
                "max_bet_percentage": 50,  # Max bet as percentage of balance
                "daily_reward_base": 100,
                "weekly_reward_base": 1000,
                "monthly_reward_base": 5000,
                "work_reward_min": 50,
                "work_reward_max": 300,
                "level_xp_multiplier": 100
            },
            "games": {
                "blackjack": {
                    "min_bet": 10,
                    "max_bet": 50000,
                    "blackjack_multiplier": 2.5,
                    "win_multiplier": 2.0,
                    "cooldown_seconds": 45
                },
                "coinflip": {
                    "min_bet": 1,
                    "max_bet": 100000,
                    "win_multiplier": 2.0,
                    "cooldown_seconds": 15
                },
                "slots": {
                    "min_bet": 5,
                    "max_bet": 75000,
                    "cooldown_seconds": 30
                },
                "dice": {
                    "min_bet": 1,
                    "max_bet": 50000,
                    "cooldown_seconds": 20
                },
                "crash": {
                    "min_bet": 10,
                    "max_bet": 100000,
                    "max_multiplier": 50.0,
                    "cooldown_seconds": 60
                }
            },
            "cooldowns": {
                "daily": 86400,    # 24 hours
                "weekly": 604800,  # 7 days
                "monthly": 2592000, # 30 days
                "work": 14400,     # 4 hours
                "overtime": 28800, # 8 hours
                "vote": 43200      # 12 hours
            },
            "features": {
                "gambling_enabled": True,
                "trading_enabled": True,
                "leaderboards_enabled": True,
                "prestige_enabled": True,
                "shop_enabled": True,
                "lottery_enabled": True,
                "mining_enabled": False  # Future feature
            },
            "limits": {
                "max_transfer_amount": 1000000,
                "max_daily_games": 1000,
                "max_inventory_items": 100,
                "max_leaderboard_entries": 100
            },
            "messages": {
                "welcome_message": "Welcome to the casino! Type `/help` to get started.",
                "level_up_message": "🆙 Congratulations! You reached level {level}!",
                "jackpot_message": "🎰 JACKPOT! You won {amount} coins!",
                "bankruptcy_message": "💸 You're broke! Use `/daily` to get some starting coins."
            },
            "webhooks": {
                "error_webhook": None,
                "transactions_webhook": None,
                "jackpots_webhook": None
            },
            "logging": {
                "level": "INFO",
                "log_to_file": True,
                "log_file": "bot.log",
                "max_log_size_mb": 50,
                "backup_count": 5
            }
        }
        
        self._config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return self._merge_configs(self.default_config, config)
            else:
                logger.info(f"Config file {self.config_file} not found. Creating default config.")
                self.save_config(self.default_config)
                return self.default_config.copy()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            logger.info("Using default configuration")
            return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any] = None) -> bool:
        """Save configuration to file"""
        try:
            config_to_save = config or self._config
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=4, ensure_ascii=False)
            logger.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """Recursively merge user config with default config"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def get(self, key_path: str, default=None) -> Any:
        """
        Get config value using dot notation
        Example: get('games.blackjack.min_bet')
        """
        try:
            keys = key_path.split('.')
            value = self._config
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any, save: bool = True) -> bool:
        """
        Set config value using dot notation
        Example: set('games.blackjack.min_bet', 20)
        """
        try:
            keys = key_path.split('.')
            config = self._config
            
            # Navigate to the parent of the target key
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
            
            # Set the value
            config[keys[-1]] = value
            
            if save:
                return self.save_config()
            return True
        except Exception as e:
            logger.error(f"Error setting config value {key_path}: {e}")
            return False
    
    def reload(self) -> bool:
        """Reload configuration from file"""
        try:
            self._config = self.load_config()
            logger.info("Configuration reloaded")
            return True
        except Exception as e:
            logger.error(f"Error reloading config: {e}")
            return False
    
    def get_game_config(self, game_name: str) -> Dict[str, Any]:
        """Get configuration for a specific game"""
        return self.get(f'games.{game_name}', {})
    
    def get_economy_config(self) -> Dict[str, Any]:
        """Get economy configuration"""
        return self.get('economy', {})
    
    def get_cooldown(self, command: str) -> int:
        """Get cooldown for a command in seconds"""
        return self.get(f'cooldowns.{command}', 0)
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled"""
        return self.get(f'features.{feature}', False)
    
    def get_limit(self, limit_name: str) -> int:
        """Get a configured limit value"""
        return self.get(f'limits.{limit_name}', 0)
    
    def get_message(self, message_name: str, **kwargs) -> str:
        """Get a configured message with optional formatting"""
        message = self.get(f'messages.{message_name}', '')
        if kwargs:
            try:
                return message.format(**kwargs)
            except KeyError:
                logger.warning(f"Missing formatting keys for message {message_name}")
                return message
        return message
    
    def validate_config(self) -> bool:
        """Validate configuration values"""
        try:
            # Check required sections
            required_sections = ['bot', 'database', 'economy', 'games', 'cooldowns']
            for section in required_sections:
                if section not in self._config:
                    logger.error(f"Missing required config section: {section}")
                    return False
            
            # Validate economy settings
            economy = self.get_economy_config()
            if economy.get('starting_balance', 0) <= 0:
                logger.error("Invalid starting_balance in economy config")
                return False
            
            # Validate game settings
            for game_name in ['blackjack', 'coinflip', 'slots', 'dice']:
                game_config = self.get_game_config(game_name)
                if game_config.get('min_bet', 0) <= 0:
                    logger.error(f"Invalid min_bet for {game_name}")
                    return False
                if game_config.get('max_bet', 0) <= game_config.get('min_bet', 0):
                    logger.error(f"Invalid max_bet for {game_name}")
                    return False
            
            logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Error validating config: {e}")
            return False
    
    def create_backup(self) -> bool:
        """Create a backup of the current configuration"""
        try:
            import shutil
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{self.config_file}.backup_{timestamp}"
            
            shutil.copy2(self.config_file, backup_file)
            logger.info(f"Configuration backup created: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating config backup: {e}")
            return False
    
    def reset_to_default(self, section: str = None) -> bool:
        """Reset configuration to default values"""
        try:
            if section:
                if section in self.default_config:
                    self._config[section] = self.default_config[section].copy()
                    logger.info(f"Reset {section} to default values")
                else:
                    logger.error(f"Unknown config section: {section}")
                    return False
            else:
                self._config = self.default_config.copy()
                logger.info("Reset entire configuration to default values")
            
            return self.save_config()
            
        except Exception as e:
            logger.error(f"Error resetting config: {e}")
            return False
    
    def export_config(self, file_path: str) -> bool:
        """Export configuration to a different file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
            logger.info(f"Configuration exported to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting config: {e}")
            return False
    
    def import_config(self, file_path: str) -> bool:
        """Import configuration from a file"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"Config file not found: {file_path}")
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # Merge with current config
            self._config = self._merge_configs(self._config, imported_config)
            
            # Validate and save
            if self.validate_config():
                return self.save_config()
            else:
                logger.error("Imported configuration failed validation")
                return False
                
        except Exception as e:
            logger.error(f"Error importing config: {e}")
            return False
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get debug information about the configuration"""
        return {
            "config_file": self.config_file,
            "config_exists": os.path.exists(self.config_file),
            "config_size": len(json.dumps(self._config)),
            "sections": list(self._config.keys()),
            "features_enabled": {k: v for k, v in self.get('features', {}).items() if v},
            "validation_status": self.validate_config()
        }
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get the entire configuration dictionary"""
        return self._config.copy()
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access"""
        return self._config[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Allow dictionary-style setting"""
        self._config[key] = value
    
    def __contains__(self, key: str) -> bool:
        """Allow 'in' operator"""
        return key in self._config
