"""
Config Loader Utility
Manages loading and saving of separate config files for easier management.

Config files:
- bot.json       : Bot token, admin users, guild ID
- branding.json  : Bot branding (name, descriptions, footers)
- settings.json  : General settings (welcome, status, auto-role)
- tickets.json   : Ticket system settings
- server_stats.json : Server stats per guild
- ranked.json    : Ranked matchmaking data per guild
"""

import json
import os

CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))

# Config file paths
CONFIG_FILES = {
    'bot': 'bot.json',
    'branding': 'branding.json',
    'settings': 'settings.json',
    'tickets': 'tickets.json',
    'server_stats': 'server_stats.json',
    'ranked': 'ranked.json'
}

# Default configs for each file
DEFAULT_CONFIGS = {
    'bot': {
        "bot_token": "YOUR_DISCORD_BOT_TOKEN_HERE",
        "admin_users": [],
        "guild_id": ""
    },
    'branding': {
        "bot_name": "Template Bot",
        "bot_description": "A customizable Discord bot template for server management and community engagement!",
        "welcome_title": "Welcome to Template Bot!",
        "welcome_description": "I'm **Template Bot**, your customizable Discord bot featuring:\n\n**Server Management** - Moderation, roles, channels & more\n**Ticket System** - Professional support ticket management\n**Polls & Utilities** - Engage your community\n\nType `/help` to see all available commands!",
        "help_title": "Template Bot - Command List",
        "footer_text": "Template Bot - Made with love",
        "ticket_footer": "Template Bot Ticket System",
        "features_list": "Server Management\nTicket System\nPolls & Utilities\nCustomizable"
    },
    'settings': {
        "welcome_enabled": False,
        "welcome_channel_id": None,
        "welcome_message": "Welcome {user} to {server}!\nYou are member #{members}",
        "log_channel_id": None,
        "auto_role_id": None,
        "status_type": "playing",
        "status_text": "/help for commands"
    },
    'tickets': {
        "ticket_category_id": None,
        "support_role_id": None,
        "transcript_channel_id": None,
        "transcript_enabled": True
    },
    'server_stats': {},
    'ranked': {}
}


def get_config_path(config_name: str) -> str:
    """Get the full path for a config file"""
    return os.path.join(CONFIG_DIR, CONFIG_FILES[config_name])


def load_config_file(config_name: str) -> dict:
    """Load a specific config file, creating with defaults if it doesn't exist"""
    config_path = get_config_path(config_name)

    if not os.path.exists(config_path):
        # Create with default values
        save_config_file(config_name, DEFAULT_CONFIGS[config_name])
        return DEFAULT_CONFIGS[config_name].copy()

    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return DEFAULT_CONFIGS[config_name].copy()


def save_config_file(config_name: str, data: dict):
    """Save a specific config file"""
    config_path = get_config_path(config_name)
    with open(config_path, 'w') as f:
        json.dump(data, f, indent=4)


def load_all_configs() -> dict:
    """
    Load all config files and return a unified config dict
    This maintains backward compatibility with the old single-file structure
    """
    config = {}

    # Load bot config (top-level keys)
    bot_config = load_config_file('bot')
    config['bot_token'] = bot_config.get('bot_token', DEFAULT_CONFIGS['bot']['bot_token'])
    config['admin_users'] = bot_config.get('admin_users', [])
    config['guild_id'] = bot_config.get('guild_id', '')

    # Load nested configs
    config['branding'] = load_config_file('branding')
    config['settings'] = load_config_file('settings')
    config['ticket_settings'] = load_config_file('tickets')
    config['server_stats'] = load_config_file('server_stats')
    config['ranked'] = load_config_file('ranked')

    return config


def save_all_configs(config: dict):
    """
    Save all configs from a unified config dict to separate files
    """
    # Save bot config
    bot_config = {
        'bot_token': config.get('bot_token', DEFAULT_CONFIGS['bot']['bot_token']),
        'admin_users': config.get('admin_users', []),
        'guild_id': config.get('guild_id', '')
    }
    save_config_file('bot', bot_config)

    # Save nested configs
    if 'branding' in config:
        save_config_file('branding', config['branding'])
    if 'settings' in config:
        save_config_file('settings', config['settings'])
    if 'ticket_settings' in config:
        save_config_file('tickets', config['ticket_settings'])
    if 'server_stats' in config:
        save_config_file('server_stats', config['server_stats'])
    if 'ranked' in config:
        save_config_file('ranked', config['ranked'])


# Convenience functions for specific configs
def load_bot_config() -> dict:
    return load_config_file('bot')

def save_bot_config(data: dict):
    save_config_file('bot', data)

def load_branding_config() -> dict:
    return load_config_file('branding')

def save_branding_config(data: dict):
    save_config_file('branding', data)

def load_settings_config() -> dict:
    return load_config_file('settings')

def save_settings_config(data: dict):
    save_config_file('settings', data)

def load_tickets_config() -> dict:
    return load_config_file('tickets')

def save_tickets_config(data: dict):
    save_config_file('tickets', data)

def load_server_stats_config() -> dict:
    return load_config_file('server_stats')

def save_server_stats_config(data: dict):
    save_config_file('server_stats', data)

def load_ranked_config() -> dict:
    return load_config_file('ranked')

def save_ranked_config(data: dict):
    save_config_file('ranked', data)


# Permission helper (moved here for central access)
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
