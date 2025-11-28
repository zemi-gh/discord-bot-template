import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View, Select, Modal, TextInput
import asyncio
from typing import Optional
import sys
import os

# Add config directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'config'))

from config.config_loader import (
    load_all_configs, save_all_configs,
    is_admin
)

# Admin Panel Permissions Storage
ADMIN_PANEL_USERS = {}  # {guild_id: [user_ids]}

def can_use_admin_panel(user_id: int, guild_id: int, guild_owner_id: int) -> bool:
    """Check if a user can access the admin panel."""
    # Server owner always has access
    if user_id == guild_owner_id:
        return True

    # Check if user is in the allowed list
    guild_key = str(guild_id)
    if guild_key in ADMIN_PANEL_USERS:
        return str(user_id) in ADMIN_PANEL_USERS[guild_key]

    return False

def add_admin_panel_user(user_id: int, guild_id: int):
    """Add a user to the admin panel access list."""
    guild_key = str(guild_id)
    if guild_key not in ADMIN_PANEL_USERS:
        ADMIN_PANEL_USERS[guild_key] = []

    user_key = str(user_id)
    if user_key not in ADMIN_PANEL_USERS[guild_key]:
        ADMIN_PANEL_USERS[guild_key].append(user_key)

def remove_admin_panel_user(user_id: int, guild_id: int):
    """Remove a user from the admin panel access list."""
    guild_key = str(guild_id)
    user_key = str(user_id)

    if guild_key in ADMIN_PANEL_USERS:
        if user_key in ADMIN_PANEL_USERS[guild_key]:
            ADMIN_PANEL_USERS[guild_key].remove(user_key)

# ==================== MODALS ====================

class BanMemberModal(Modal, title="Ban Member"):
    member_id = TextInput(
        label="Member ID to Ban",
        placeholder="Enter the user ID",
        required=True,
        max_length=20
    )
    reason = TextInput(
        label="Reason",
        placeholder="Enter ban reason",
        required=False,
        max_length=200,
        default="No reason provided"
    )
    delete_days = TextInput(
        label="Delete Message History (0-7 days)",
        placeholder="Enter 0-7",
        required=False,
        max_length=1,
        default="0"
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.member_id.value)
            delete_days = int(self.delete_days.value) if self.delete_days.value else 0
            delete_days = max(0, min(delete_days, 7))

            user = await interaction.client.fetch_user(user_id)
            await interaction.guild.ban(user, reason=self.reason.value, delete_message_days=delete_days)

            embed = discord.Embed(
                title="✅ Member Banned",
                description=f"**{user.name}** has been banned from the server.",
                color=0xe74c3c
            )
            embed.add_field(name="User ID", value=user_id, inline=True)
            embed.add_field(name="Reason", value=self.reason.value, inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Invalid user ID format!", ephemeral=True)
        except discord.NotFound:
            await interaction.response.send_message("❌ User not found!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to ban this user!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

class KickMemberModal(Modal, title="Kick Member"):
    member_id = TextInput(
        label="Member ID to Kick",
        placeholder="Enter the user ID",
        required=True,
        max_length=20
    )
    reason = TextInput(
        label="Reason",
        placeholder="Enter kick reason",
        required=False,
        max_length=200,
        default="No reason provided"
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.member_id.value)
            member = interaction.guild.get_member(user_id)

            if not member:
                await interaction.response.send_message("❌ Member not found in this server!", ephemeral=True)
                return

            await member.kick(reason=self.reason.value)

            embed = discord.Embed(
                title="✅ Member Kicked",
                description=f"**{member.name}** has been kicked from the server.",
                color=0xf39c12
            )
            embed.add_field(name="User ID", value=user_id, inline=True)
            embed.add_field(name="Reason", value=self.reason.value, inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Invalid user ID format!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to kick this user!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

class TimeoutMemberModal(Modal, title="Timeout Member"):
    member_id = TextInput(
        label="Member ID to Timeout",
        placeholder="Enter the user ID",
        required=True,
        max_length=20
    )
    duration = TextInput(
        label="Duration (minutes)",
        placeholder="Enter timeout duration in minutes",
        required=True,
        max_length=6
    )
    reason = TextInput(
        label="Reason",
        placeholder="Enter timeout reason",
        required=False,
        max_length=200,
        default="No reason provided"
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            from datetime import timedelta

            user_id = int(self.member_id.value)
            minutes = int(self.duration.value)

            if minutes < 1 or minutes > 40320:  # Max 28 days
                await interaction.response.send_message("❌ Duration must be between 1 and 40320 minutes (28 days)!", ephemeral=True)
                return

            member = interaction.guild.get_member(user_id)
            if not member:
                await interaction.response.send_message("❌ Member not found in this server!", ephemeral=True)
                return

            await member.timeout(timedelta(minutes=minutes), reason=self.reason.value)

            embed = discord.Embed(
                title="✅ Member Timed Out",
                description=f"**{member.name}** has been timed out.",
                color=0xf39c12
            )
            embed.add_field(name="Duration", value=f"{minutes} minutes", inline=True)
            embed.add_field(name="Reason", value=self.reason.value, inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Invalid input format!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to timeout this user!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

class CreateChannelModal(Modal, title="Create Channel"):
    name = TextInput(
        label="Channel Name",
        placeholder="Enter channel name",
        required=True,
        max_length=100
    )
    topic = TextInput(
        label="Topic (Optional)",
        placeholder="Enter channel topic",
        required=False,
        max_length=1024,
        style=discord.TextStyle.paragraph
    )

    def __init__(self, channel_type: str):
        super().__init__()
        self.channel_type = channel_type

    async def on_submit(self, interaction: discord.Interaction):
        try:
            if self.channel_type == "text":
                channel = await interaction.guild.create_text_channel(
                    name=self.name.value,
                    topic=self.topic.value if self.topic.value else None
                )
            elif self.channel_type == "voice":
                channel = await interaction.guild.create_voice_channel(
                    name=self.name.value
                )
            else:
                await interaction.response.send_message("❌ Invalid channel type!", ephemeral=True)
                return

            embed = discord.Embed(
                title="✅ Channel Created",
                description=f"**{channel.mention}** has been created!",
                color=0x2ecc71
            )
            embed.add_field(name="Type", value=self.channel_type.capitalize(), inline=True)
            if self.topic.value and self.channel_type == "text":
                embed.add_field(name="Topic", value=self.topic.value, inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to create channels!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

class CreateRoleModal(Modal, title="Create Role"):
    name = TextInput(
        label="Role Name",
        placeholder="Enter role name",
        required=True,
        max_length=100
    )
    color = TextInput(
        label="Color (Hex, e.g., #FF0000)",
        placeholder="Enter hex color code",
        required=False,
        max_length=7
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            role_color = discord.Color.default()
            if self.color.value:
                role_color = discord.Color(int(self.color.value.replace("#", ""), 16))

            role = await interaction.guild.create_role(name=self.name.value, color=role_color)

            embed = discord.Embed(
                title="✅ Role Created",
                description=f"**{role.mention}** has been created!",
                color=role_color
            )
            embed.add_field(name="Role ID", value=role.id, inline=True)

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Invalid color format! Use hex format like #FF0000", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to create roles!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

class MassDeleteModal(Modal, title="Mass Delete Messages"):
    amount = TextInput(
        label="Number of Messages (1-100)",
        placeholder="Enter number of messages to delete",
        required=True,
        max_length=3
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            count = int(self.amount.value)
            if count < 1 or count > 100:
                await interaction.response.send_message("❌ Amount must be between 1 and 100!", ephemeral=True)
                return

            await interaction.response.defer(ephemeral=True)
            deleted = await interaction.channel.purge(limit=count)

            embed = discord.Embed(
                title="✅ Messages Deleted",
                description=f"Deleted **{len(deleted)}** messages from this channel.",
                color=0xe74c3c
            )

            await interaction.followup.send(embed=embed, ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Invalid number format!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to delete messages!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

# ==================== ADMIN PANEL VIEW ====================

class AdminPanelView(View):
    def __init__(self, config):
        super().__init__(timeout=None)
        self.config = config

    @discord.ui.button(label="🔨 Ban Member", style=discord.ButtonStyle.danger, custom_id="admin_ban")
    async def ban_button(self, interaction: discord.Interaction, button: Button):
        if not can_use_admin_panel(interaction.user.id, interaction.guild.id, interaction.guild.owner_id):
            await interaction.response.send_message("❌ You don't have permission to use the admin panel!", ephemeral=True)
            return

        await interaction.response.send_modal(BanMemberModal())

    @discord.ui.button(label="👢 Kick Member", style=discord.ButtonStyle.danger, custom_id="admin_kick")
    async def kick_button(self, interaction: discord.Interaction, button: Button):
        if not can_use_admin_panel(interaction.user.id, interaction.guild.id, interaction.guild.owner_id):
            await interaction.response.send_message("❌ You don't have permission to use the admin panel!", ephemeral=True)
            return

        await interaction.response.send_modal(KickMemberModal())

    @discord.ui.button(label="⏰ Timeout Member", style=discord.ButtonStyle.primary, custom_id="admin_timeout")
    async def timeout_button(self, interaction: discord.Interaction, button: Button):
        if not can_use_admin_panel(interaction.user.id, interaction.guild.id, interaction.guild.owner_id):
            await interaction.response.send_message("❌ You don't have permission to use the admin panel!", ephemeral=True)
            return

        await interaction.response.send_modal(TimeoutMemberModal())

    @discord.ui.button(label="🗑️ Mass Delete", style=discord.ButtonStyle.danger, custom_id="admin_purge")
    async def purge_button(self, interaction: discord.Interaction, button: Button):
        if not can_use_admin_panel(interaction.user.id, interaction.guild.id, interaction.guild.owner_id):
            await interaction.response.send_message("❌ You don't have permission to use the admin panel!", ephemeral=True)
            return

        await interaction.response.send_modal(MassDeleteModal())

    @discord.ui.button(label="📝 Create Text Channel", style=discord.ButtonStyle.success, custom_id="admin_create_text")
    async def create_text_channel_button(self, interaction: discord.Interaction, button: Button):
        if not can_use_admin_panel(interaction.user.id, interaction.guild.id, interaction.guild.owner_id):
            await interaction.response.send_message("❌ You don't have permission to use the admin panel!", ephemeral=True)
            return

        await interaction.response.send_modal(CreateChannelModal("text"))

    @discord.ui.button(label="🔊 Create Voice Channel", style=discord.ButtonStyle.success, custom_id="admin_create_voice")
    async def create_voice_channel_button(self, interaction: discord.Interaction, button: Button):
        if not can_use_admin_panel(interaction.user.id, interaction.guild.id, interaction.guild.owner_id):
            await interaction.response.send_message("❌ You don't have permission to use the admin panel!", ephemeral=True)
            return

        await interaction.response.send_modal(CreateChannelModal("voice"))

    @discord.ui.button(label="🎭 Create Role", style=discord.ButtonStyle.success, custom_id="admin_create_role")
    async def create_role_button(self, interaction: discord.Interaction, button: Button):
        if not can_use_admin_panel(interaction.user.id, interaction.guild.id, interaction.guild.owner_id):
            await interaction.response.send_message("❌ You don't have permission to use the admin panel!", ephemeral=True)
            return

        await interaction.response.send_modal(CreateRoleModal())

    @discord.ui.button(label="🔒 Lock Channel", style=discord.ButtonStyle.secondary, custom_id="admin_lock")
    async def lock_channel_button(self, interaction: discord.Interaction, button: Button):
        if not can_use_admin_panel(interaction.user.id, interaction.guild.id, interaction.guild.owner_id):
            await interaction.response.send_message("❌ You don't have permission to use the admin panel!", ephemeral=True)
            return

        try:
            channel = interaction.channel
            overwrite = channel.overwrites_for(interaction.guild.default_role)
            overwrite.send_messages = False
            await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)

            embed = discord.Embed(
                title="🔒 Channel Locked",
                description=f"{channel.mention} has been locked.",
                color=0x95a5a6
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to lock this channel!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

    @discord.ui.button(label="🔓 Unlock Channel", style=discord.ButtonStyle.secondary, custom_id="admin_unlock")
    async def unlock_channel_button(self, interaction: discord.Interaction, button: Button):
        if not can_use_admin_panel(interaction.user.id, interaction.guild.id, interaction.guild.owner_id):
            await interaction.response.send_message("❌ You don't have permission to use the admin panel!", ephemeral=True)
            return

        try:
            channel = interaction.channel
            overwrite = channel.overwrites_for(interaction.guild.default_role)
            overwrite.send_messages = None
            await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)

            embed = discord.Embed(
                title="🔓 Channel Unlocked",
                description=f"{channel.mention} has been unlocked.",
                color=0x2ecc71
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to unlock this channel!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

    @discord.ui.button(label="📊 Server Info", style=discord.ButtonStyle.primary, custom_id="admin_serverinfo")
    async def server_info_button(self, interaction: discord.Interaction, button: Button):
        if not can_use_admin_panel(interaction.user.id, interaction.guild.id, interaction.guild.owner_id):
            await interaction.response.send_message("❌ You don't have permission to use the admin panel!", ephemeral=True)
            return

        guild = interaction.guild

        embed = discord.Embed(
            title=f"📊 {guild.name} - Server Information",
            color=0x3498db
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="👑 Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="🆔 Server ID", value=guild.id, inline=True)
        embed.add_field(name="📅 Created", value=f"<t:{int(guild.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="👥 Members", value=guild.member_count, inline=True)
        embed.add_field(name="💬 Channels", value=len(guild.channels), inline=True)
        embed.add_field(name="🎭 Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="🚀 Boost Level", value=guild.premium_tier, inline=True)
        embed.add_field(name="💎 Boosts", value=guild.premium_subscription_count, inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="👥 Manage Access", style=discord.ButtonStyle.primary, custom_id="admin_manage_access", row=4)
    async def manage_access_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Only the server owner can manage admin panel access!", ephemeral=True)
            return

        guild_key = str(interaction.guild.id)
        allowed_users = ADMIN_PANEL_USERS.get(guild_key, [])

        if not allowed_users:
            description = "No additional users have access to the admin panel.\nUse `/adminpanel-grant @user` to grant access."
        else:
            user_list = []
            for user_id in allowed_users:
                try:
                    user = await interaction.client.fetch_user(int(user_id))
                    user_list.append(f"• {user.mention} ({user.name})")
                except:
                    user_list.append(f"• Unknown User (ID: {user_id})")

            description = "**Users with admin panel access:**\n" + "\n".join(user_list)
            description += "\n\nUse `/adminpanel-grant @user` to add more users.\nUse `/adminpanel-revoke @user` to remove users."

        embed = discord.Embed(
            title="👥 Admin Panel Access Management",
            description=description,
            color=0xf1c40f
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

# ==================== SETUP FUNCTION ====================

def setup_admin_panel_commands(client, config):

    @client.tree.command(name="adminpanel", description="[OWNER] Open the server admin panel dashboard")
    async def adminpanel(interaction: discord.Interaction):
        if not can_use_admin_panel(interaction.user.id, interaction.guild.id, interaction.guild.owner_id):
            await interaction.response.send_message("❌ Only the server owner and authorized users can access the admin panel!", ephemeral=True)
            return

        embed = discord.Embed(
            title="🎛️ Server Admin Panel",
            description=(
                "Welcome to the comprehensive server administration dashboard!\n\n"
                "**Available Controls:**\n"
                "🔨 **Ban Member** - Permanently ban users from the server\n"
                "👢 **Kick Member** - Remove users from the server\n"
                "⏰ **Timeout Member** - Temporarily mute users\n"
                "🗑️ **Mass Delete** - Bulk delete messages\n"
                "📝 **Create Text Channel** - Add new text channels\n"
                "🔊 **Create Voice Channel** - Add new voice channels\n"
                "🎭 **Create Role** - Add new roles\n"
                "🔒 **Lock Channel** - Prevent members from sending messages\n"
                "🔓 **Unlock Channel** - Allow members to send messages\n"
                "📊 **Server Info** - View detailed server information\n"
                "👥 **Manage Access** - Control who can use this panel\n\n"
                f"**Access Level:** {'Server Owner' if interaction.user.id == interaction.guild.owner_id else 'Authorized User'}"
            ),
            color=0x9b59b6
        )
        embed.set_footer(text="All actions are logged and require appropriate permissions")

        view = AdminPanelView(config)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @client.tree.command(name="adminpanel-grant", description="[OWNER] Grant admin panel access to a user")
    @app_commands.describe(user="User to grant access")
    async def adminpanel_grant(interaction: discord.Interaction, user: discord.Member):
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Only the server owner can grant admin panel access!", ephemeral=True)
            return

        if user.id == interaction.guild.owner_id:
            await interaction.response.send_message("❌ The server owner already has full access!", ephemeral=True)
            return

        add_admin_panel_user(user.id, interaction.guild.id)

        embed = discord.Embed(
            title="✅ Access Granted",
            description=f"{user.mention} can now access the admin panel!",
            color=0x2ecc71
        )
        embed.add_field(name="Command", value="/adminpanel", inline=False)

        await interaction.response.send_message(embed=embed)

    @client.tree.command(name="adminpanel-revoke", description="[OWNER] Revoke admin panel access from a user")
    @app_commands.describe(user="User to revoke access from")
    async def adminpanel_revoke(interaction: discord.Interaction, user: discord.Member):
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Only the server owner can revoke admin panel access!", ephemeral=True)
            return

        if user.id == interaction.guild.owner_id:
            await interaction.response.send_message("❌ Cannot revoke access from the server owner!", ephemeral=True)
            return

        remove_admin_panel_user(user.id, interaction.guild.id)

        embed = discord.Embed(
            title="✅ Access Revoked",
            description=f"{user.mention} can no longer access the admin panel.",
            color=0xe74c3c
        )

        await interaction.response.send_message(embed=embed)

    @client.tree.command(name="adminpanel-list", description="[OWNER] List all users with admin panel access")
    async def adminpanel_list(interaction: discord.Interaction):
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Only the server owner can view admin panel access list!", ephemeral=True)
            return

        guild_key = str(interaction.guild.id)
        allowed_users = ADMIN_PANEL_USERS.get(guild_key, [])

        embed = discord.Embed(
            title="👥 Admin Panel Access List",
            color=0x3498db
        )

        # Add owner
        owner_text = f"• {interaction.guild.owner.mention} (Server Owner)"
        embed.add_field(name="🏆 Full Access", value=owner_text, inline=False)

        # Add authorized users
        if allowed_users:
            user_list = []
            for user_id in allowed_users:
                try:
                    user = await interaction.client.fetch_user(int(user_id))
                    user_list.append(f"• {user.mention}")
                except:
                    user_list.append(f"• Unknown User (ID: {user_id})")

            embed.add_field(name="✅ Authorized Users", value="\n".join(user_list), inline=False)
        else:
            embed.add_field(name="✅ Authorized Users", value="No additional users", inline=False)

        embed.set_footer(text="Use /adminpanel-grant to add users")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # Add persistent view
    client.add_view(AdminPanelView(config))

__all__ = ['setup_admin_panel_commands']
