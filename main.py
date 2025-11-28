import discord
from discord.ext import commands
from discord import app_commands
import os
import sys

# Add config directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'config'))

from config.config_loader import (
    load_all_configs, save_all_configs, is_admin,
    load_bot_config, save_bot_config,
    load_settings_config, save_settings_config,
    load_branding_config, save_branding_config,
    load_tickets_config, save_tickets_config,
    load_server_stats_config, save_server_stats_config,
    load_ranked_config, save_ranked_config
)
from modules.management import *
from modules.tickets import *
from modules.server_stats import *
from modules.ranked import *
from modules.admin_panel import *

print("="*50)
print(" Starting Up...")
print("="*50)

# Load all configs (maintains backward compatibility)
config = load_all_configs()
token = config.get('bot_token')
guild_id = config.get('guild_id')

# User data removed - no longer needed for ranking features

print("✅ Configuration loaded!")
print(f"👥 {len(config.get('admin_users', []))} admin(s) configured")

# Start the Discord bot
class Client(commands.Bot):
    async def setup_hook(self):
        # Add persistent views for tickets
        self.add_view(TicketView(config))
        self.add_view(TicketControlView(config))
        print("🎫 Ticket system views registered!")

        # Add persistent views for admin panel
        from modules.admin_panel import AdminPanelView
        self.add_view(AdminPanelView(config))
        print("🎛️ Admin panel views registered!")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Required for welcome messages and member events
client = Client(command_prefix='!', intents=intents)

print("🔧 Setting up commands...")

# Ranked commands removed - no longer included

# Setup management commands
setup_management_commands(client, config)
print("  ✓ Management commands loaded")

# Setup ticket commands
setup_ticket_commands(client, config)
print("  ✓ Ticket system loaded")

# Setup server stats commands
setup_server_stats_commands(client, config)
print("  ✓ Server stats system loaded")

# Setup ranked commands
setup_ranked_commands(client, config)
print("  ✓ Ranked matchmaking system loaded")

# Setup admin panel commands
setup_admin_panel_commands(client, config)
print("  ✓ Admin panel system loaded")

# Sync commands with Discord
@client.event
async def on_ready():
    print("="*50)
    print(f"✅ Logged in as {client.user}")
    print(f"📊 Connected to {len(client.guilds)} server(s)")
    print(f"👥 Serving {len(client.users)} user(s)")

    # Set bot status
    status_type = config.get('settings', {}).get('status_type')
    status_text = config.get('settings', {}).get('status_text')

    if status_type and status_text:
        activity_types = {
            "playing": discord.ActivityType.playing,
            "watching": discord.ActivityType.watching,
            "listening": discord.ActivityType.listening,
            "competing": discord.ActivityType.competing
        }
        activity = discord.Activity(
            type=activity_types.get(status_type, discord.ActivityType.playing),
            name=status_text
        )
        await client.change_presence(activity=activity)
        print(f"🎮 Status set: {status_type.capitalize()} {status_text}")

    # Sync commands
    try:
        await client.tree.sync()
        print(f"🔄 Commands synced globally!")

        # Also sync to specific guild if configured
        if guild_id:
            guild = discord.Object(guild_id)
            synced = await client.tree.sync(guild=guild)
            print(f"🔄 {len(synced)} commands synced to guild {guild_id}")
    except Exception as e:
        print(f'❌ Error syncing commands: {e}')

    # Start server stats background task if it exists
    if hasattr(client, 'server_stats_task') and not client.server_stats_task.is_running():
        client.server_stats_task.start()
        print("📊 Server stats background task started")

    print("="*50)
    bot_name = config.get('branding', {}).get('bot_name', 'Template Bot')
    print(f" 🎉 {bot_name} is ready!")
    print("="*50)

# This sends a message when the bot joins a new server
@client.event
async def on_guild_join(guild):
    print(f"📥 Joined new server: {guild.name} (ID: {guild.id})")

    channel = guild.system_channel or next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)

    if channel:
        branding = config.get('branding', {})
        bot_name = branding.get('bot_name', 'Template Bot')
        embed = discord.Embed(
            title=branding.get('welcome_title', f'👋 Thank you for inviting {bot_name}!'),
            description=branding.get('welcome_description',
                f"I'm **{bot_name}**, your customizable Discord bot featuring:\n\n"
                "👑 **Server Management** - Moderation, roles, channels & more\n"
                "🎫 **Ticket System** - Professional support ticket management\n"
                "📊 **Polls & Utilities** - Engage your community\n\n"
                "Type `/help` to see all available commands!"
            ),
            color=0x3498db
        )
        embed.add_field(
            name="⚙️ Getting Started",
            value=(
                "1. Run `/addadmin @user` to set up administrators\n"
                "2. Use `/ticket-setup` to configure the ticket system\n"
                "3. Use `/setwelcome` to set up welcome messages\n"
                "4. Type `/help` to explore all features!"
            ),
            inline=False
        )
        embed.set_footer(text=branding.get('footer_text', f'{bot_name} - Made with ❤️'))

        await channel.send(embed=embed)

@client.tree.command(name='help', description='View all available commands')
async def help(interaction: discord.Interaction):
    is_admin_user = is_admin(interaction.user.id, config)
    branding = config.get('branding', {})
    bot_name = branding.get('bot_name', 'Template Bot')

    embed = discord.Embed(
        title=branding.get('help_title', f'🚀 {bot_name} - Command List'),
        description="Here are all the commands you can use!",
        color=0x3498db
    )

    # Rocket League commands removed

    # Ranked Commands
    ranked_commands = (
        "🏆 **Ranked Matchmaking**\n"
        "```\n"
        "/q <mode>         Join ranked queue (1s/2s/3s)\n"
        "/qr <id> <winner> Report match results\n"
        "/leaderboard      Show ranked leaderboard\n"
        "/queue-status     Show current queue status\n"
        "/leave-queue      Leave all ranked queues\n"
        "```"
    )
    embed.add_field(name="\u200b", value=ranked_commands, inline=False)

    # Utility Commands
    utility_commands = (
        "🔧 **Utility & Info**\n"
        "```\n"
        "/serverinfo       Server information\n"
        "/userinfo         User information\n"
        "/membercount      Member statistics\n"
        "/avatar           User's avatar\n"
        "/roleinfo         Role information\n"
        "/channelinfo      Channel information\n"
        "/botinfo          Bot information\n"
        "/poll             Create a poll\n"
        "```"
    )
    embed.add_field(name="\u200b", value=utility_commands, inline=False)

    # Admin Commands (only shown to admins)
    if is_admin_user:
        admin_mod = (
            "👑 **Moderation** [ADMIN]\n"
            "```\n"
            "/purge            Delete messages\n"
            "/clear            Clear user messages\n"
            "/kick             Kick member\n"
            "/ban              Ban member\n"
            "/unban            Unban user\n"
            "/timeout          Timeout member\n"
            "/untimeout        Remove timeout\n"
            "/warn             Warn member\n"
            "```"
        )
        embed.add_field(name="\u200b", value=admin_mod, inline=False)

        admin_manage = (
            "⚙️ **Management** [ADMIN]\n"
            "```\n"
            "/nickname         Change nickname\n"
            "/addrole          Add role\n"
            "/removerole       Remove role\n"
            "/createrole       Create role\n"
            "/deleterole       Delete role\n"
            "/lock             Lock channel\n"
            "/unlock           Unlock channel\n"
            "/slowmode         Set slowmode\n"
            "```"
        )
        embed.add_field(name="\u200b", value=admin_manage, inline=False)

        admin_config = (
            "🎨 **Configuration** [ADMIN]\n"
            "```\n"
            "/setwelcome       Set welcome channel\n"
            "/welcomemessage   Set welcome text\n"
            "/togglewelcome    Toggle welcomes\n"
            "/setautorole      Set auto-role\n"
            "/removeautorole   Remove auto-role\n"
            "/setstatus        Set bot status\n"
            "/clearstatus      Clear bot status\n"
            "/announce         Send announcement\n"
            "/embed            Create embed\n"
            "/serverstats      Server stats tracking\n"
            "```"
        )
        embed.add_field(name="\u200b", value=admin_config, inline=False)

        admin_ticket = (
            "🎫 **Tickets** [ADMIN]\n"
            "```\n"
            "/ticket-setup     Configure tickets\n"
            "/ticket-panel     Create ticket panel\n"
            "/ticket-add       Add user to ticket\n"
            "/ticket-remove    Remove user\n"
            "/ticket-rename    Rename ticket\n"
            "```"
        )
        embed.add_field(name="\u200b", value=admin_ticket, inline=False)

        admin_bot = (
            "🤖 **Bot Admin** [ADMIN]\n"
            "```\n"
            "/addadmin         Add bot admin\n"
            "/removeadmin      Remove bot admin\n"
            "/listadmins       List bot admins\n"
            "```"
        )
        embed.add_field(name="\u200b", value=admin_bot, inline=False)

        # Admin Panel section (only for server owners)
        if interaction.user.id == interaction.guild.owner_id or (interaction.guild and interaction.user.guild_permissions.administrator):
            admin_panel = (
                "🎛️ **Admin Panel** [OWNER]\n"
                "```\n"
                "/adminpanel        Open admin dashboard\n"
                "/adminpanel-grant  Grant panel access\n"
                "/adminpanel-revoke Revoke panel access\n"
                "/adminpanel-list   List authorized users\n"
                "```"
            )
            embed.add_field(name="\u200b", value=admin_panel, inline=False)

    embed.set_footer(text="💡 Tip: Commands marked [ADMIN] require bot administrator permissions")

    await interaction.response.send_message(embed=embed)

# Error handling
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    print(f"❌ Error: {error}")

print("🚀 Starting bot...")
print("="*50)

try:
    client.run(token)
except Exception as e:
    print(f"❌ Failed to start bot: {e}")
    print("💡 Make sure your bot token is correct in config/config.json")
