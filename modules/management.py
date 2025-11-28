import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import timedelta, datetime
from typing import Optional
import sys
import os

# Add config directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'config'))

from config.config_loader import (
    load_all_configs, save_all_configs,
    load_bot_config, save_bot_config,
    load_settings_config, save_settings_config,
    is_admin, check_admin_permission
)

# Setup function to register all management commands
def setup_management_commands(client, config):

    # ==================== MESSAGE MANAGEMENT ====================

    @client.tree.command(name="purge", description="[ADMIN] Delete a specified number of messages")
    @app_commands.describe(amount="Number of messages to delete (1-100)")
    async def purge(interaction: discord.Interaction, amount: int):
        if not await check_admin_permission(interaction, config):
            return

        if amount < 1 or amount > 100:
            await interaction.response.send_message("❌ Please specify a number between 1 and 100.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"✅ Successfully deleted {len(deleted)} message(s).", ephemeral=True)

    @client.tree.command(name="clear", description="[ADMIN] Clear messages from a specific user")
    @app_commands.describe(
        user="The user whose messages to delete",
        amount="Number of messages to check (default: 100)"
    )
    async def clear(interaction: discord.Interaction, user: discord.Member, amount: int = 100):
        if not await check_admin_permission(interaction, config):
            return

        await interaction.response.defer(ephemeral=True)

        def check(m):
            return m.author.id == user.id

        deleted = await interaction.channel.purge(limit=amount, check=check)
        await interaction.followup.send(f"✅ Deleted {len(deleted)} message(s) from {user.mention}.", ephemeral=True)

    # ==================== USER MODERATION ====================

    @client.tree.command(name="kick", description="[ADMIN] Kick a member from the server")
    @app_commands.describe(
        member="The member to kick",
        reason="Reason for kicking"
    )
    async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if not await check_admin_permission(interaction, config):
            return

        if member.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message("❌ I cannot kick this user due to role hierarchy.", ephemeral=True)
            return

        await member.kick(reason=reason)
        await interaction.response.send_message(f"✅ {member.mention} has been kicked.\n**Reason:** {reason}")

    @client.tree.command(name="ban", description="[ADMIN] Ban a member from the server")
    @app_commands.describe(
        member="The member to ban",
        reason="Reason for banning",
        delete_messages="Delete message history (days, 0-7)"
    )
    async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided", delete_messages: int = 0):
        if not await check_admin_permission(interaction, config):
            return

        if member.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message("❌ I cannot ban this user due to role hierarchy.", ephemeral=True)
            return

        await member.ban(reason=reason, delete_message_days=min(delete_messages, 7))
        await interaction.response.send_message(f"✅ {member.mention} has been banned.\n**Reason:** {reason}")

    @client.tree.command(name="unban", description="[ADMIN] Unban a user from the server")
    @app_commands.describe(user_id="The user ID to unban")
    async def unban(interaction: discord.Interaction, user_id: str):
        if not await check_admin_permission(interaction, config):
            return

        await interaction.response.defer()

        try:
            user = await client.fetch_user(int(user_id))
            await interaction.guild.unban(user)
            await interaction.followup.send(f"✅ {user.mention} has been unbanned.")
        except:
            await interaction.followup.send("❌ Could not find or unban that user.", ephemeral=True)

    @client.tree.command(name="timeout", description="[ADMIN] Timeout a member")
    @app_commands.describe(
        member="The member to timeout",
        duration="Duration in minutes",
        reason="Reason for timeout"
    )
    async def timeout(interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = "No reason provided"):
        if not await check_admin_permission(interaction, config):
            return

        if member.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message("❌ I cannot timeout this user due to role hierarchy.", ephemeral=True)
            return

        await member.timeout(timedelta(minutes=duration), reason=reason)
        await interaction.response.send_message(f"✅ {member.mention} has been timed out for {duration} minute(s).\n**Reason:** {reason}")

    @client.tree.command(name="untimeout", description="[ADMIN] Remove timeout from a member")
    @app_commands.describe(member="The member to remove timeout from")
    async def untimeout(interaction: discord.Interaction, member: discord.Member):
        if not await check_admin_permission(interaction, config):
            return

        await member.timeout(None)
        await interaction.response.send_message(f"✅ Timeout removed from {member.mention}.")

    @client.tree.command(name="warn", description="[ADMIN] Warn a member")
    @app_commands.describe(
        member="The member to warn",
        reason="Reason for warning"
    )
    async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
        if not await check_admin_permission(interaction, config):
            return

        try:
            embed = discord.Embed(
                title="⚠️ Warning",
                description=f"You have been warned in **{interaction.guild.name}**",
                color=0xff9900
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Warned by", value=interaction.user.mention, inline=False)

            await member.send(embed=embed)
            await interaction.response.send_message(f"✅ {member.mention} has been warned.\n**Reason:** {reason}")
        except:
            await interaction.response.send_message(f"✅ {member.mention} has been warned, but I couldn't DM them.\n**Reason:** {reason}")

    # ==================== NICKNAME MANAGEMENT ====================

    @client.tree.command(name="nickname", description="[ADMIN] Change a member's nickname")
    @app_commands.describe(
        member="The member to change nickname",
        nickname="New nickname (leave empty to reset)"
    )
    async def nickname(interaction: discord.Interaction, member: discord.Member, nickname: str = None):
        if not await check_admin_permission(interaction, config):
            return

        if member.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message("❌ I cannot change this user's nickname due to role hierarchy.", ephemeral=True)
            return

        old_nick = member.display_name
        await member.edit(nick=nickname)

        if nickname:
            await interaction.response.send_message(f"✅ Changed {member.mention}'s nickname from **{old_nick}** to **{nickname}**.")
        else:
            await interaction.response.send_message(f"✅ Reset {member.mention}'s nickname.")

    # ==================== ROLE MANAGEMENT ====================

    @client.tree.command(name="addrole", description="[ADMIN] Add a role to a member")
    @app_commands.describe(
        member="The member to add role to",
        role="The role to add"
    )
    async def addrole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        if not await check_admin_permission(interaction, config):
            return

        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message("❌ I cannot assign this role due to role hierarchy.", ephemeral=True)
            return

        await member.add_roles(role)
        await interaction.response.send_message(f"✅ Added {role.mention} to {member.mention}.")

    @client.tree.command(name="removerole", description="[ADMIN] Remove a role from a member")
    @app_commands.describe(
        member="The member to remove role from",
        role="The role to remove"
    )
    async def removerole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        if not await check_admin_permission(interaction, config):
            return

        await member.remove_roles(role)
        await interaction.response.send_message(f"✅ Removed {role.mention} from {member.mention}.")

    @client.tree.command(name="createrole", description="[ADMIN] Create a new role")
    @app_commands.describe(
        name="Role name",
        color="Role color (hex, e.g., #FF0000)"
    )
    async def createrole(interaction: discord.Interaction, name: str, color: str = None):
        if not await check_admin_permission(interaction, config):
            return

        role_color = discord.Color.default()
        if color:
            try:
                role_color = discord.Color(int(color.replace("#", ""), 16))
            except:
                await interaction.response.send_message("❌ Invalid color format. Use hex format like #FF0000", ephemeral=True)
                return

        role = await interaction.guild.create_role(name=name, color=role_color)
        await interaction.response.send_message(f"✅ Created role {role.mention}.")

    @client.tree.command(name="deleterole", description="[ADMIN] Delete a role")
    @app_commands.describe(role="The role to delete")
    async def deleterole(interaction: discord.Interaction, role: discord.Role):
        if not await check_admin_permission(interaction, config):
            return

        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message("❌ I cannot delete this role due to role hierarchy.", ephemeral=True)
            return

        role_name = role.name
        await role.delete()
        await interaction.response.send_message(f"✅ Deleted role **{role_name}**.")

    # ==================== CHANNEL MANAGEMENT ====================

    @client.tree.command(name="lock", description="[ADMIN] Lock a channel")
    @app_commands.describe(channel="Channel to lock (defaults to current)")
    async def lock(interaction: discord.Interaction, channel: discord.TextChannel = None):
        if not await check_admin_permission(interaction, config):
            return

        channel = channel or interaction.channel
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)

        await interaction.response.send_message(f"🔒 {channel.mention} has been locked.")

    @client.tree.command(name="unlock", description="[ADMIN] Unlock a channel")
    @app_commands.describe(channel="Channel to unlock (defaults to current)")
    async def unlock(interaction: discord.Interaction, channel: discord.TextChannel = None):
        if not await check_admin_permission(interaction, config):
            return

        channel = channel or interaction.channel
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = None
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)

        await interaction.response.send_message(f"🔓 {channel.mention} has been unlocked.")

    @client.tree.command(name="slowmode", description="[ADMIN] Set slowmode for a channel")
    @app_commands.describe(
        seconds="Slowmode duration in seconds (0 to disable)",
        channel="Channel to set slowmode (defaults to current)"
    )
    async def slowmode(interaction: discord.Interaction, seconds: int, channel: discord.TextChannel = None):
        if not await check_admin_permission(interaction, config):
            return

        if seconds < 0 or seconds > 21600:
            await interaction.response.send_message("❌ Slowmode must be between 0 and 21600 seconds (6 hours).", ephemeral=True)
            return

        channel = channel or interaction.channel
        await channel.edit(slowmode_delay=seconds)

        if seconds == 0:
            await interaction.response.send_message(f"✅ Slowmode disabled in {channel.mention}.")
        else:
            await interaction.response.send_message(f"✅ Slowmode set to {seconds} second(s) in {channel.mention}.")

    # ==================== WELCOME SYSTEM ====================

    @client.tree.command(name="setwelcome", description="[ADMIN] Set welcome channel")
    @app_commands.describe(channel="The channel for welcome messages")
    async def setwelcome(interaction: discord.Interaction, channel: discord.TextChannel):
        if not await check_admin_permission(interaction, config):
            return

        config['settings']['welcome_channel_id'] = str(channel.id)
        config['settings']['welcome_enabled'] = True
        save_all_configs(config)

        await interaction.response.send_message(f"✅ Welcome channel set to {channel.mention}.")

    @client.tree.command(name="welcomemessage", description="[ADMIN] Set welcome message")
    @app_commands.describe(message="Welcome message (use {user} for mention, {server} for server name)")
    async def welcomemessage(interaction: discord.Interaction, message: str):
        if not await check_admin_permission(interaction, config):
            return

        config['settings']['welcome_message'] = message
        save_all_configs(config)

        await interaction.response.send_message(f"✅ Welcome message set to:\n{message}")

    @client.tree.command(name="togglewelcome", description="[ADMIN] Enable/disable welcome messages")
    async def togglewelcome(interaction: discord.Interaction):
        if not await check_admin_permission(interaction, config):
            return

        config['settings']['welcome_enabled'] = not config['settings']['welcome_enabled']
        save_all_configs(config)

        status = "enabled" if config['settings']['welcome_enabled'] else "disabled"
        await interaction.response.send_message(f"✅ Welcome messages {status}.")

    # ==================== SERVER INFO ====================

    @client.tree.command(name="serverinfo", description="Display server information")
    async def serverinfo(interaction: discord.Interaction):
        guild = interaction.guild

        embed = discord.Embed(
            title=f"📊 {guild.name} Server Information",
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
        embed.add_field(name="😊 Emojis", value=len(guild.emojis), inline=True)
        embed.add_field(name="🚀 Boost Level", value=guild.premium_tier, inline=True)
        embed.add_field(name="💎 Boosts", value=guild.premium_subscription_count, inline=True)

        await interaction.response.send_message(embed=embed)

    @client.tree.command(name="userinfo", description="Display user information")
    @app_commands.describe(member="The member to get info about (defaults to you)")
    async def userinfo(interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user

        embed = discord.Embed(
            title=f"👤 User Information",
            color=member.color
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(name="Username", value=f"{member.name}", inline=True)
        embed.add_field(name="Display Name", value=member.display_name, inline=True)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="Joined Server", value=f"<t:{int(member.joined_at.timestamp())}:R>", inline=True)
        embed.add_field(name="Roles", value=f"{len(member.roles)-1}", inline=True)

        if member.premium_since:
            embed.add_field(name="Boosting Since", value=f"<t:{int(member.premium_since.timestamp())}:R>", inline=True)

        await interaction.response.send_message(embed=embed)

    # ==================== ANNOUNCEMENT SYSTEM ====================

    @client.tree.command(name="announce", description="[ADMIN] Send an announcement")
    @app_commands.describe(
        channel="Channel to send announcement",
        title="Announcement title",
        message="Announcement message"
    )
    async def announce(interaction: discord.Interaction, channel: discord.TextChannel, title: str, message: str):
        if not await check_admin_permission(interaction, config):
            return

        embed = discord.Embed(
            title=f"📢 {title}",
            description=message,
            color=0xe74c3c
        )
        embed.set_footer(text=f"Announcement by {interaction.user.name}")

        await channel.send(embed=embed)
        await interaction.response.send_message(f"✅ Announcement sent to {channel.mention}!", ephemeral=True)

    # ==================== ADMIN MANAGEMENT ====================

    @client.tree.command(name="addadmin", description="[ADMIN] Add a user to admin list")
    @app_commands.describe(user="User to add as admin")
    async def addadmin(interaction: discord.Interaction, user: discord.Member):
        if not await check_admin_permission(interaction, config):
            return

        user_id = str(user.id)
        if user_id in config['admin_users']:
            await interaction.response.send_message(f"❌ {user.mention} is already an admin.", ephemeral=True)
            return

        config['admin_users'].append(user_id)
        save_all_configs(config)

        await interaction.response.send_message(f"✅ {user.mention} has been added as a bot administrator.")

    @client.tree.command(name="removeadmin", description="[ADMIN] Remove a user from admin list")
    @app_commands.describe(user="User to remove from admin")
    async def removeadmin(interaction: discord.Interaction, user: discord.Member):
        if not await check_admin_permission(interaction, config):
            return

        user_id = str(user.id)
        if user_id not in config['admin_users']:
            await interaction.response.send_message(f"❌ {user.mention} is not an admin.", ephemeral=True)
            return

        config['admin_users'].remove(user_id)
        save_all_configs(config)

        await interaction.response.send_message(f"✅ {user.mention} has been removed from bot administrators.")

    @client.tree.command(name="listadmins", description="[ADMIN] List all bot administrators")
    async def listadmins(interaction: discord.Interaction):
        if not await check_admin_permission(interaction, config):
            return

        admin_mentions = []
        for user_id in config['admin_users']:
            try:
                user = await client.fetch_user(int(user_id))
                admin_mentions.append(f"• {user.mention} ({user.name})")
            except:
                admin_mentions.append(f"• Unknown User (ID: {user_id})")

        embed = discord.Embed(
            title="👑 Bot Administrators",
            description="\n".join(admin_mentions) if admin_mentions else "No administrators configured.",
            color=0xf1c40f
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ==================== AUTO-ROLE SYSTEM ====================

    @client.tree.command(name="setautorole", description="[ADMIN] Set role to be given on member join")
    @app_commands.describe(role="Role to give to new members")
    async def setautorole(interaction: discord.Interaction, role: discord.Role):
        if not await check_admin_permission(interaction, config):
            return

        config['settings']['auto_role_id'] = str(role.id)
        save_all_configs(config)

        embed = discord.Embed(
            title="✅ Auto-Role Configured",
            description=f"New members will automatically receive {role.mention}",
            color=0x2ecc71
        )

        await interaction.response.send_message(embed=embed)

    @client.tree.command(name="removeautorole", description="[ADMIN] Remove auto-role")
    async def removeautorole(interaction: discord.Interaction):
        if not await check_admin_permission(interaction, config):
            return

        config['settings']['auto_role_id'] = None
        save_all_configs(config)

        embed = discord.Embed(
            title="✅ Auto-Role Removed",
            description="Auto-role has been disabled",
            color=0xe74c3c
        )

        await interaction.response.send_message(embed=embed)

    # ==================== BOT STATUS ====================

    @client.tree.command(name="setstatus", description="[ADMIN] Set the bot's status")
    @app_commands.describe(
        status_type="Type of status",
        text="Status text"
    )
    @app_commands.choices(status_type=[
        app_commands.Choice(name="Playing", value="playing"),
        app_commands.Choice(name="Watching", value="watching"),
        app_commands.Choice(name="Listening", value="listening"),
        app_commands.Choice(name="Competing", value="competing")
    ])
    async def setstatus(interaction: discord.Interaction, status_type: str, text: str):
        if not await check_admin_permission(interaction, config):
            return

        activity_type = {
            "playing": discord.ActivityType.playing,
            "watching": discord.ActivityType.watching,
            "listening": discord.ActivityType.listening,
            "competing": discord.ActivityType.competing
        }

        activity = discord.Activity(type=activity_type[status_type], name=text)
        await client.change_presence(activity=activity)

        config['settings']['status_type'] = status_type
        config['settings']['status_text'] = text
        save_all_configs(config)

        embed = discord.Embed(
            title="✅ Status Updated",
            description=f"Bot status set to: **{status_type.capitalize()} {text}**",
            color=0x3498db
        )

        await interaction.response.send_message(embed=embed)

    @client.tree.command(name="clearstatus", description="[ADMIN] Clear the bot's status")
    async def clearstatus(interaction: discord.Interaction):
        if not await check_admin_permission(interaction, config):
            return

        await client.change_presence(activity=None)

        config['settings']['status_type'] = None
        config['settings']['status_text'] = None
        save_all_configs(config)

        embed = discord.Embed(
            title="✅ Status Cleared",
            description="Bot status has been cleared",
            color=0x95a5a6
        )

        await interaction.response.send_message(embed=embed)

    # ==================== POLL SYSTEM ====================

    @client.tree.command(name="poll", description="Create a poll")
    @app_commands.describe(
        question="Poll question",
        option1="First option",
        option2="Second option",
        option3="Third option (optional)",
        option4="Fourth option (optional)",
        option5="Fifth option (optional)"
    )
    async def poll(
        interaction: discord.Interaction,
        question: str,
        option1: str,
        option2: str,
        option3: str = None,
        option4: str = None,
        option5: str = None
    ):
        options = [option1, option2, option3, option4, option5]
        options = [opt for opt in options if opt is not None]

        if len(options) < 2:
            await interaction.response.send_message("❌ You need at least 2 options!", ephemeral=True)
            return

        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

        description = "\n".join([f"{emojis[i]} {options[i]}" for i in range(len(options))])

        embed = discord.Embed(
            title=f"📊 {question}",
            description=description,
            color=0x3498db,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"Poll created by {interaction.user}", icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()

        for i in range(len(options)):
            await message.add_reaction(emojis[i])

    # ==================== EMBED CREATOR ====================

    @client.tree.command(name="embed", description="[ADMIN] Create a custom embed")
    @app_commands.describe(
        title="Embed title",
        description="Embed description",
        color="Hex color (e.g., #3498db)",
        channel="Channel to send to (optional)"
    )
    async def create_embed(
        interaction: discord.Interaction,
        title: str,
        description: str,
        color: str = "#3498db",
        channel: discord.TextChannel = None
    ):
        if not await check_admin_permission(interaction, config):
            return

        try:
            embed_color = discord.Color(int(color.replace("#", ""), 16))
        except:
            await interaction.response.send_message("❌ Invalid color format. Use hex format like #3498db", ephemeral=True)
            return

        embed = discord.Embed(
            title=title,
            description=description,
            color=embed_color,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"Created by {interaction.user}", icon_url=interaction.user.display_avatar.url)

        target_channel = channel or interaction.channel
        await target_channel.send(embed=embed)

        await interaction.response.send_message(f"✅ Embed sent to {target_channel.mention}!", ephemeral=True)

    # ==================== UTILITY COMMANDS ====================

    @client.tree.command(name="membercount", description="Display server member count")
    async def membercount(interaction: discord.Interaction):
        guild = interaction.guild

        total_members = guild.member_count
        bots = len([m for m in guild.members if m.bot])
        humans = total_members - bots
        online = len([m for m in guild.members if m.status != discord.Status.offline])

        embed = discord.Embed(
            title=f"👥 {guild.name} Member Count",
            color=0x3498db
        )

        embed.add_field(name="Total Members", value=f"```{total_members}```", inline=True)
        embed.add_field(name="Humans", value=f"```{humans}```", inline=True)
        embed.add_field(name="Bots", value=f"```{bots}```", inline=True)
        embed.add_field(name="Online", value=f"```{online}```", inline=True)

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        await interaction.response.send_message(embed=embed)

    @client.tree.command(name="avatar", description="Display user's avatar")
    @app_commands.describe(user="User to get avatar (defaults to you)")
    async def avatar(interaction: discord.Interaction, user: discord.Member = None):
        user = user or interaction.user

        embed = discord.Embed(
            title=f"{user.display_name}'s Avatar",
            color=user.color
        )
        embed.set_image(url=user.display_avatar.url)
        embed.add_field(name="Download", value=f"[Click Here]({user.display_avatar.url})")

        await interaction.response.send_message(embed=embed)

    @client.tree.command(name="roleinfo", description="Display role information")
    @app_commands.describe(role="Role to get info about")
    async def roleinfo(interaction: discord.Interaction, role: discord.Role):
        embed = discord.Embed(
            title=f"Role Information: {role.name}",
            color=role.color
        )

        embed.add_field(name="ID", value=role.id, inline=True)
        embed.add_field(name="Color", value=str(role.color), inline=True)
        embed.add_field(name="Position", value=role.position, inline=True)
        embed.add_field(name="Members", value=len(role.members), inline=True)
        embed.add_field(name="Mentionable", value=role.mentionable, inline=True)
        embed.add_field(name="Hoisted", value=role.hoist, inline=True)
        embed.add_field(name="Created", value=f"<t:{int(role.created_at.timestamp())}:R>", inline=True)

        await interaction.response.send_message(embed=embed)

    @client.tree.command(name="channelinfo", description="Display channel information")
    @app_commands.describe(channel="Channel to get info about (defaults to current)")
    async def channelinfo(interaction: discord.Interaction, channel: discord.TextChannel = None):
        channel = channel or interaction.channel

        embed = discord.Embed(
            title=f"Channel Information: #{channel.name}",
            color=0x3498db
        )

        embed.add_field(name="ID", value=channel.id, inline=True)
        embed.add_field(name="Category", value=channel.category.name if channel.category else "None", inline=True)
        embed.add_field(name="Position", value=channel.position, inline=True)
        embed.add_field(name="NSFW", value=channel.is_nsfw(), inline=True)
        embed.add_field(name="Slowmode", value=f"{channel.slowmode_delay}s", inline=True)
        embed.add_field(name="Created", value=f"<t:{int(channel.created_at.timestamp())}:R>", inline=True)

        if channel.topic:
            embed.add_field(name="Topic", value=channel.topic, inline=False)

        await interaction.response.send_message(embed=embed)

    @client.tree.command(name="botinfo", description="Display bot information")
    async def botinfo(interaction: discord.Interaction):
        branding = config.get('branding', {})
        bot_name = branding.get('bot_name', 'Template Bot')
        bot_description = branding.get('bot_description', 'A customizable Discord bot template for server management and community engagement!')

        embed = discord.Embed(
            title=f"🤖 {bot_name} Information",
            description=bot_description,
            color=0x3498db
        )

        embed.add_field(name="Servers", value=len(client.guilds), inline=True)
        embed.add_field(name="Users", value=len(client.users), inline=True)
        embed.add_field(name="Commands", value=len(client.tree.get_commands()), inline=True)

        features_list = branding.get('features_list', '👑 Server Management\n🎫 Ticket System\n📊 Polls & Utilities\n⚙️ Customizable')
        embed.add_field(
            name="Features",
            value=features_list,
            inline=False
        )

        if client.user.display_avatar:
            embed.set_thumbnail(url=client.user.display_avatar.url)

        embed.set_footer(text="Made with ❤️ using discord.py")

        await interaction.response.send_message(embed=embed)

    # Welcome message and auto-role handler (to be called from main.py)
    @client.event
    async def on_member_join(member):
        # Auto-role
        auto_role_id = config['settings'].get('auto_role_id')
        if auto_role_id:
            role = member.guild.get_role(int(auto_role_id))
            if role:
                try:
                    await member.add_roles(role)
                except:
                    pass

        # Welcome message
        if not config['settings']['welcome_enabled']:
            return

        channel_id = config['settings'].get('welcome_channel_id')
        if not channel_id:
            return

        channel = client.get_channel(int(channel_id))
        if not channel:
            return

        message = config['settings']['welcome_message']
        message = message.replace('{user}', member.mention)
        message = message.replace('{server}', member.guild.name)
        message = message.replace('{members}', str(member.guild.member_count))

        embed = discord.Embed(
            title="👋 Welcome!",
            description=message,
            color=0x2ecc71,
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Member #{member.guild.member_count}")

        await channel.send(embed=embed)

__all__ = ['setup_management_commands', 'load_config', 'save_config', 'is_admin']
