import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime
import io
import sys
import os

# Add config directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'config'))

from config.config_loader import (
    load_all_configs, save_all_configs,
    load_tickets_config, save_tickets_config,
    is_admin, check_admin_permission
)

# Ticket System
class TicketView(discord.ui.View):
    def __init__(self, config):
        super().__init__(timeout=None)
        self.config = config

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.green, emoji="🎫", custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild

        # Check if user already has an open ticket
        ticket_category_id = self.config.get('ticket_settings', {}).get('ticket_category_id')
        if ticket_category_id:
            category = guild.get_channel(int(ticket_category_id))
            if category:
                for channel in category.channels:
                    if channel.name == f"ticket-{interaction.user.name.lower()}":
                        await interaction.response.send_message("❌ You already have an open ticket!", ephemeral=True)
                        return

        await interaction.response.defer(ephemeral=True)

        # Get ticket category
        if not ticket_category_id:
            await interaction.followup.send("❌ Ticket system is not configured. Ask an admin to set it up.", ephemeral=True)
            return

        category = guild.get_channel(int(ticket_category_id))
        if not category:
            await interaction.followup.send("❌ Ticket category not found. Contact an administrator.", ephemeral=True)
            return

        # Get support role
        support_role_id = self.config.get('ticket_settings', {}).get('support_role_id')
        support_role = guild.get_role(int(support_role_id)) if support_role_id else None

        # Create ticket channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                attach_files=True,
                embed_links=True
            ),
            guild.me: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                manage_channels=True,
                manage_messages=True
            )
        }

        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                attach_files=True,
                embed_links=True
            )

        ticket_channel = await category.create_text_channel(
            name=f"ticket-{interaction.user.name.lower()}",
            overwrites=overwrites
        )

        # Send welcome message in ticket
        embed = discord.Embed(
            title="🎫 Support Ticket",
            description=f"Hello {interaction.user.mention}!\n\nThank you for creating a ticket. Our support team will be with you shortly.\n\nPlease describe your issue in detail.",
            color=0x2ecc71,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"Ticket created by {interaction.user}", icon_url=interaction.user.display_avatar.url)

        close_view = TicketControlView(self.config)
        await ticket_channel.send(f"{interaction.user.mention}" + (f" {support_role.mention}" if support_role else ""), embed=embed, view=close_view)

        await interaction.followup.send(f"✅ Ticket created! {ticket_channel.mention}", ephemeral=True)

class TicketControlView(discord.ui.View):
    def __init__(self, config):
        super().__init__(timeout=None)
        self.config = config

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, emoji="🔒", custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔒 Close Ticket",
            description="Are you sure you want to close this ticket?\nClick the button below to confirm.",
            color=0xe74c3c
        )

        confirm_view = TicketCloseConfirmView(self.config)
        await interaction.response.send_message(embed=embed, view=confirm_view, ephemeral=True)

    @discord.ui.button(label="Claim Ticket", style=discord.ButtonStyle.blurple, emoji="✋", custom_id="claim_ticket")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="✋ Ticket Claimed",
            description=f"This ticket has been claimed by {interaction.user.mention}",
            color=0x3498db,
            timestamp=datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed)

class TicketCloseConfirmView(discord.ui.View):
    def __init__(self, config):
        super().__init__(timeout=60)
        self.config = config

    @discord.ui.button(label="Confirm Close", style=discord.ButtonStyle.red, emoji="✅")
    async def confirm_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel

        # Create transcript
        transcript_enabled = self.config.get('ticket_settings', {}).get('transcript_enabled', True)

        if transcript_enabled:
            await interaction.response.send_message("🔒 Creating transcript and closing ticket...", ephemeral=True)

            # Generate transcript
            messages = []
            async for message in channel.history(limit=None, oldest_first=True):
                timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
                content = message.content if message.content else "[No content]"
                attachments = "\n".join([f"  Attachment: {a.url}" for a in message.attachments])
                messages.append(f"[{timestamp}] {message.author}: {content}")
                if attachments:
                    messages.append(attachments)

            transcript_text = "\n".join(messages)
            transcript_file = discord.File(
                io.BytesIO(transcript_text.encode('utf-8')),
                filename=f"transcript-{channel.name}.txt"
            )

            # Send transcript to log channel
            log_channel_id = self.config.get('ticket_settings', {}).get('transcript_channel_id')
            if log_channel_id:
                log_channel = interaction.guild.get_channel(int(log_channel_id))
                if log_channel:
                    embed = discord.Embed(
                        title="📝 Ticket Transcript",
                        description=f"**Ticket:** {channel.name}\n**Closed by:** {interaction.user.mention}",
                        color=0x95a5a6,
                        timestamp=datetime.utcnow()
                    )
                    await log_channel.send(embed=embed, file=transcript_file)

        else:
            await interaction.response.send_message("🔒 Closing ticket...", ephemeral=True)

        # Close ticket after delay
        await asyncio.sleep(3)
        await channel.delete()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.gray, emoji="❌")
    async def cancel_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("❌ Ticket close cancelled.", ephemeral=True)

# Setup function to register all ticket commands
def setup_ticket_commands(client, config):

    @client.tree.command(name="ticket-setup", description="[ADMIN] Set up the ticket system")
    @app_commands.describe(
        category="Category for ticket channels",
        support_role="Role that can see and manage tickets",
        transcript_channel="Channel for ticket transcripts"
    )
    async def ticket_setup(
        interaction: discord.Interaction,
        category: discord.CategoryChannel,
        support_role: discord.Role = None,
        transcript_channel: discord.TextChannel = None
    ):
        if not await check_admin_permission(interaction, config):
            return

        if 'ticket_settings' not in config:
            config['ticket_settings'] = {}

        config['ticket_settings']['ticket_category_id'] = str(category.id)
        if support_role:
            config['ticket_settings']['support_role_id'] = str(support_role.id)
        if transcript_channel:
            config['ticket_settings']['transcript_channel_id'] = str(transcript_channel.id)

        config['ticket_settings']['transcript_enabled'] = True

        save_all_configs(config)

        embed = discord.Embed(
            title="✅ Ticket System Configured",
            description=(
                f"**Category:** {category.mention}\n"
                f"**Support Role:** {support_role.mention if support_role else 'None'}\n"
                f"**Transcript Channel:** {transcript_channel.mention if transcript_channel else 'None'}"
            ),
            color=0x2ecc71
        )

        await interaction.response.send_message(embed=embed)

    @client.tree.command(name="ticket-panel", description="[ADMIN] Create a ticket panel")
    @app_commands.describe(
        channel="Channel to send the ticket panel",
        title="Title of the panel",
        description="Description of the panel"
    )
    async def ticket_panel(
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        title: str = "🎫 Support Tickets",
        description: str = "Click the button below to create a support ticket!"
    ):
        if not await check_admin_permission(interaction, config):
            return

        embed = discord.Embed(
            title=title,
            description=description,
            color=0x3498db
        )
        branding = config.get('branding', {})
        bot_name = branding.get('bot_name', 'Template Bot')
        ticket_footer = branding.get('ticket_footer', f'{bot_name} Ticket System')
        embed.set_footer(text=ticket_footer)

        view = TicketView(config)
        await channel.send(embed=embed, view=view)

        await interaction.response.send_message(f"✅ Ticket panel created in {channel.mention}!", ephemeral=True)

    @client.tree.command(name="ticket-add", description="[ADMIN] Add a user to the current ticket")
    @app_commands.describe(user="User to add to the ticket")
    async def ticket_add(interaction: discord.Interaction, user: discord.Member):
        if not await check_admin_permission(interaction, config):
            return

        channel = interaction.channel

        if not channel.name.startswith("ticket-"):
            await interaction.response.send_message("❌ This command can only be used in ticket channels!", ephemeral=True)
            return

        await channel.set_permissions(user, read_messages=True, send_messages=True)

        embed = discord.Embed(
            description=f"✅ {user.mention} has been added to this ticket by {interaction.user.mention}",
            color=0x2ecc71
        )

        await interaction.response.send_message(embed=embed)

    @client.tree.command(name="ticket-remove", description="[ADMIN] Remove a user from the current ticket")
    @app_commands.describe(user="User to remove from the ticket")
    async def ticket_remove(interaction: discord.Interaction, user: discord.Member):
        if not await check_admin_permission(interaction, config):
            return

        channel = interaction.channel

        if not channel.name.startswith("ticket-"):
            await interaction.response.send_message("❌ This command can only be used in ticket channels!", ephemeral=True)
            return

        await channel.set_permissions(user, overwrite=None)

        embed = discord.Embed(
            description=f"✅ {user.mention} has been removed from this ticket by {interaction.user.mention}",
            color=0xe74c3c
        )

        await interaction.response.send_message(embed=embed)

    @client.tree.command(name="ticket-rename", description="[ADMIN] Rename the current ticket")
    @app_commands.describe(new_name="New name for the ticket")
    async def ticket_rename(interaction: discord.Interaction, new_name: str):
        if not await check_admin_permission(interaction, config):
            return

        channel = interaction.channel

        if not channel.name.startswith("ticket-"):
            await interaction.response.send_message("❌ This command can only be used in ticket channels!", ephemeral=True)
            return

        old_name = channel.name
        await channel.edit(name=f"ticket-{new_name.lower()}")

        embed = discord.Embed(
            description=f"✅ Ticket renamed from `{old_name}` to `ticket-{new_name.lower()}`",
            color=0x3498db
        )

        await interaction.response.send_message(embed=embed)

__all__ = ['setup_ticket_commands', 'TicketView', 'TicketControlView']
