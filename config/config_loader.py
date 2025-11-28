"""
Config Loader Utility
Manages loading and saving of a single unified config file.

Config file: config.json
Contains all bot settings in a single file for easier management.
"""

import json
import os

CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')

# Default configuration
DEFAULT_CONFIG = {
    "bot_token": "YOUR_DISCORD_BOT_TOKEN_HERE",
    "admin_users": [],
    "guild_id": "",
    "branding": {
        "bot_name": "Template Bot",
        "bot_description": "A customizable Discord bot template for server management and community engagement!",
        "welcome_title": "Welcome to Template Bot!",
        "welcome_description": "I'm **Template Bot**, your customizable Discord bot featuring:\n\n**Server Management** - Moderation, roles, channels & more\n**Ticket System** - Professional support ticket management\n**Polls & Utilities** - Engage your community\n\nType `/help` to see all available commands!",
        "help_title": "Template Bot - Command List",
        "footer_text": "Template Bot - Made with love",
        "ticket_footer": "Template Bot Ticket System",
        "features_list": "Server Management\nTicket System\nPolls & Utilities\nCustomizable"
    },
    "settings": {
        "welcome_enabled": False,
        "welcome_channel_id": None,
        "welcome_message": "Welcome {user} to {server}!\nYou are member #{members}",
        "log_channel_id": None,
        "auto_role_id": None,
        "status_type": "playing",
        "status_text": "/help for commands"
    },
    "ticket_settings": {
        "ticket_category_id": None,
        "support_role_id": None,
        "transcript_channel_id": None,
        "transcript_enabled": True
    },
    "server_stats": {},
    "ranked": {}
}


def load_all_configs() -> dict:
    """Load the unified config file"""
    if not os.path.exists(CONFIG_FILE):
        # Create with default values
        save_all_configs(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # Merge with defaults to ensure all keys exist
            merged = DEFAULT_CONFIG.copy()
            merged.update(config)
            # Ensure nested dicts are also merged
            for key in ['branding', 'settings', 'ticket_settings']:
                if key in DEFAULT_CONFIG:
                    merged[key] = DEFAULT_CONFIG[key].copy()
                    if key in config:
                        merged[key].update(config[key])
            # Keep server_stats and ranked as-is from config
            if 'server_stats' in config:
                merged['server_stats'] = config['server_stats']
            if 'ranked' in config:
                merged['ranked'] = config['ranked']
            return merged
    except (json.JSONDecodeError, IOError):
        return DEFAULT_CONFIG.copy()


def save_all_configs(config: dict):
    """Save the unified config file"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)


# Convenience functions for specific configs (for backward compatibility)
def load_bot_config() -> dict:
    config = load_all_configs()
    return {
        'bot_token': config.get('bot_token'),
        'admin_users': config.get('admin_users', []),
        'guild_id': config.get('guild_id', '')
    }


def save_bot_config(data: dict):
    config = load_all_configs()
    config['bot_token'] = data.get('bot_token', config['bot_token'])
    config['admin_users'] = data.get('admin_users', config['admin_users'])
    config['guild_id'] = data.get('guild_id', config['guild_id'])
    save_all_configs(config)


def load_branding_config() -> dict:
    config = load_all_configs()
    return config.get('branding', DEFAULT_CONFIG['branding'])


def save_branding_config(data: dict):
    config = load_all_configs()
    config['branding'] = data
    save_all_configs(config)


def load_settings_config() -> dict:
    config = load_all_configs()
    return config.get('settings', DEFAULT_CONFIG['settings'])


def save_settings_config(data: dict):
    config = load_all_configs()
    config['settings'] = data
    save_all_configs(config)


def load_tickets_config() -> dict:
    config = load_all_configs()
    return config.get('ticket_settings', DEFAULT_CONFIG['ticket_settings'])


def save_tickets_config(data: dict):
    config = load_all_configs()
    config['ticket_settings'] = data
    save_all_configs(config)


def load_server_stats_config() -> dict:
    config = load_all_configs()
    return config.get('server_stats', {})


def save_server_stats_config(data: dict):
    config = load_all_configs()
    config['server_stats'] = data
    save_all_configs(config)


def load_ranked_config() -> dict:
    config = load_all_configs()
    return config.get('ranked', {})


def save_ranked_config(data: dict):
    config = load_all_configs()
    config['ranked'] = data
    save_all_configs(config)


# Permission helper
def is_admin(user_id: int, config: dict) -> bool:
    """Check if user is in admin list"""
    return str(user_id) in config.get('admin_users', [])


async def check_admin_permission(interaction, config: dict) -> bool:
    """Check if user has admin permission and send error if not"""
    if not is_admin(interaction.user.id, config):
        await interaction.response.send_message(
            "You don't have permission to use this command. Only bot administrators can use this.",
            ephemeral=True
        )
        return False
    return True
