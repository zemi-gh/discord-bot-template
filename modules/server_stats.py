import discord
from discord.ext import commands, tasks
import asyncio
import sys
import os

# Add config directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'config'))

from config.config_loader import (
    load_all_configs, save_all_configs,
    load_server_stats_config, save_server_stats_config,
    is_admin
)

def setup_server_stats_commands(client, config):
    """Setup server stats commands and background tasks"""

    # Background task to update server stats every 10 minutes
    @tasks.loop(minutes=10)
    async def update_server_stats():
        """Update server stats channels every 10 minutes"""
        stats_settings = config.get('server_stats', {})

        for guild in client.guilds:
            guild_settings = stats_settings.get(str(guild.id))
            if not guild_settings or not guild_settings.get('enabled', False):
                continue

            try:
                # Get the channels
                all_members_channel = client.get_channel(guild_settings.get('all_members_channel_id'))
                members_channel = client.get_channel(guild_settings.get('members_channel_id'))
                bots_channel = client.get_channel(guild_settings.get('bots_channel_id'))

                if not all([all_members_channel, members_channel, bots_channel]):
                    print(f"⚠️ Server stats channels missing for {guild.name}")
                    continue

                # Calculate stats
                total_members = guild.member_count
                bots_count = sum(1 for member in guild.members if member.bot)
                users_count = total_members - bots_count

                # Update channel names
                await all_members_channel.edit(name=f"All Members: {total_members}")
                await members_channel.edit(name=f"Members: {users_count}")
                await bots_channel.edit(name=f"Bots: {bots_count}")

                print(f"📊 Updated server stats for {guild.name}: {total_members} total, {users_count} users, {bots_count} bots")

            except Exception as e:
                print(f"❌ Error updating server stats for {guild.name}: {e}")

    @update_server_stats.before_loop
    async def before_update_server_stats():
        """Wait until the bot is ready before starting the update loop"""
        await client.wait_until_ready()

    # Start the background task
    update_server_stats.start()

    @client.tree.command(name="serverstats", description="Manage server stats tracking")
    async def serverstats(interaction: discord.Interaction, action: str = None):
        """
        Manage server stats tracking
        Usage: /serverstats [on|off]
        """
        if not is_admin(interaction.user.id, config):
            embed = discord.Embed(
                title="❌ Access Denied",
                description="You need bot administrator permissions to use this command.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        guild = interaction.guild
        guild_id = str(guild.id)

        # Initialize server stats config if not exists
        if 'server_stats' not in config:
            config['server_stats'] = {}
        if guild_id not in config['server_stats']:
            config['server_stats'][guild_id] = {
                'enabled': False,
                'category_id': None,
                'all_members_channel_id': None,
                'members_channel_id': None,
                'bots_channel_id': None
            }

        guild_settings = config['server_stats'][guild_id]
        branding = config.get('branding', {})
        bot_name = branding.get('bot_name', 'Template Bot')

        if action is None:
            # Show current status
            status = "🟢 Enabled" if guild_settings.get('enabled', False) else "🔴 Disabled"
            embed = discord.Embed(
                title="📊 Server Stats Status",
                description=f"Server stats tracking is currently: **{status}**",
                color=0x3498db
            )
            embed.add_field(
                name="Usage",
                value="• `/serverstats on` - Enable and create stats channels\n• `/serverstats off` - Disable and remove stats channels",
                inline=False
            )
            embed.set_footer(text=branding.get('footer_text', f'{bot_name} - Made with ❤️'))
            await interaction.response.send_message(embed=embed)
            return

        if action.lower() == "on":
            if guild_settings.get('enabled', False):
                embed = discord.Embed(
                    title="⚠️ Already Enabled",
                    description="Server stats tracking is already enabled!",
                    color=0xf39c12
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            try:
                # Create category
                category = await guild.create_category("📊 Server Stats")

                # Calculate current stats
                total_members = guild.member_count
                bots_count = sum(1 for member in guild.members if member.bot)
                users_count = total_members - bots_count

                # Create voice channels for stats (they can't be joined but display numbers)
                all_members_channel = await guild.create_voice_channel(
                    f"All Members: {total_members}",
                    category=category
                )
                members_channel = await guild.create_voice_channel(
                    f"Members: {users_count}",
                    category=category
                )
                bots_channel = await guild.create_voice_channel(
                    f"Bots: {bots_count}",
                    category=category
                )

                # Set permissions so no one can join the voice channels
                everyone_role = guild.default_role
                for channel in [all_members_channel, members_channel, bots_channel]:
                    await channel.set_permissions(everyone_role, connect=False, view_channel=True)

                # Save configuration
                guild_settings.update({
                    'enabled': True,
                    'category_id': category.id,
                    'all_members_channel_id': all_members_channel.id,
                    'members_channel_id': members_channel.id,
                    'bots_channel_id': bots_channel.id
                })
                save_all_configs(config)

                embed = discord.Embed(
                    title="✅ Server Stats Enabled",
                    description="Server stats tracking has been enabled! Stats will update every 10 minutes.",
                    color=0x27ae60
                )
                embed.add_field(
                    name="📊 Current Stats",
                    value=f"**Total Members:** {total_members}\n**Users:** {users_count}\n**Bots:** {bots_count}",
                    inline=False
                )
                embed.add_field(
                    name="📍 Location",
                    value=f"Check the **{category.name}** category!",
                    inline=False
                )
                embed.set_footer(text=branding.get('footer_text', f'{bot_name} - Made with ❤️'))

                await interaction.response.send_message(embed=embed)

            except Exception as e:
                embed = discord.Embed(
                    title="❌ Setup Failed",
                    description=f"Failed to create server stats channels: {str(e)}",
                    color=0xe74c3c
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

        elif action.lower() == "off":
            if not guild_settings.get('enabled', False):
                embed = discord.Embed(
                    title="⚠️ Already Disabled",
                    description="Server stats tracking is already disabled!",
                    color=0xf39c12
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            try:
                # Delete channels and category
                channels_to_delete = [
                    client.get_channel(guild_settings.get('all_members_channel_id')),
                    client.get_channel(guild_settings.get('members_channel_id')),
                    client.get_channel(guild_settings.get('bots_channel_id'))
                ]

                category = client.get_channel(guild_settings.get('category_id'))

                # Delete channels
                for channel in channels_to_delete:
                    if channel:
                        await channel.delete()

                # Delete category
                if category:
                    await category.delete()

                # Update configuration
                guild_settings.update({
                    'enabled': False,
                    'category_id': None,
                    'all_members_channel_id': None,
                    'members_channel_id': None,
                    'bots_channel_id': None
                })
                save_all_configs(config)

                embed = discord.Embed(
                    title="✅ Server Stats Disabled",
                    description="Server stats tracking has been disabled and all stats channels have been removed.",
                    color=0x27ae60
                )
                embed.set_footer(text=branding.get('footer_text', f'{bot_name} - Made with ❤️'))

                await interaction.response.send_message(embed=embed)

            except Exception as e:
                embed = discord.Embed(
                    title="❌ Cleanup Failed",
                    description=f"Failed to remove server stats channels: {str(e)}",
                    color=0xe74c3c
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

        else:
            embed = discord.Embed(
                title="❌ Invalid Option",
                description="Please use `/serverstats on` or `/serverstats off`",
                color=0xe74c3c
            )
            embed.set_footer(text=branding.get('footer_text', f'{bot_name} - Made with ❤️'))
            await interaction.response.send_message(embed=embed, ephemeral=True)