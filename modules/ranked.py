"""
Ranked Matchmaking Module for Discord Bot

Features:
- 1v1, 2v2, 3v3 ranked matches
- ELO rating system (starting at 200, +/-19-24 points)
- Auto team assignment
- Random match IDs with 4-char names/passwords
- Match result reporting with dispute resolution
- Single unified leaderboard

Commands:
- /q <mode> - Join ranked queue (1s/2s/3s for 1v1/2v2/3v3)
- /qr <match_id> <winner> - Report match results
- /leaderboard - Show ranked leaderboard
- /queue-status - Show current queue status
"""

import discord
from discord.ext import commands
from discord import app_commands
import random
import string
import time
from typing import Optional, Dict, List, Tuple
import sys
import os

# Add config directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'config'))

from config.config_loader import (
    load_all_configs, save_all_configs,
    load_ranked_config, save_ranked_config
)


def generate_random_string(length: int = 4) -> str:
    """Generate random alphanumeric string"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def calculate_elo_change(winner_elo: int, loser_elo: int) -> Tuple[int, int]:
    """
    Calculate ELO changes for winner and loser
    Returns (winner_new_elo, loser_new_elo)
    """
    # Base change amount (19-24 points)
    base_change = random.randint(19, 24)

    # Factor in ELO difference (higher ranked players gain less from beating lower ranked)
    elo_diff = winner_elo - loser_elo
    if elo_diff > 100:
        change = max(15, base_change - 5)  # Less points for beating much lower ranked
    elif elo_diff < -100:
        change = min(29, base_change + 5)  # More points for beating higher ranked
    else:
        change = base_change

    winner_new = winner_elo + change
    loser_new = max(0, loser_elo - change)  # Don't go below 0

    return winner_new, loser_new


def get_player_data(config: dict, guild_id: str, user_id: str) -> dict:
    """Get or create player data"""
    ranked_data = config.setdefault('ranked', {})
    guild_data = ranked_data.setdefault(guild_id, {})
    players = guild_data.setdefault('players', {})

    if user_id not in players:
        players[user_id] = {
            'elo': 200,  # Starting ELO
            'wins': 0,
            'losses': 0,
            'matches_played': 0
        }

    return players[user_id]


def init_ranked_data(config: dict, guild_id: str):
    """Initialize ranked data structure for a guild"""
    ranked_data = config.setdefault('ranked', {})
    if guild_id not in ranked_data:
        ranked_data[guild_id] = {
            'enabled': True,
            'queues': {
                '1v1': [],
                '2v2': [],
                '3v3': []
            },
            'players': {},
            'active_matches': {},
            'completed_matches': [],
            'settings': {
                'queue_timeout': 300,  # 5 minutes
                'match_timeout': 3600  # 1 hour to report results
            }
        }


def auto_assign_teams(players: List[str], mode: str) -> Tuple[List[str], List[str]]:
    """
    Auto-assign players to balanced teams based on ELO
    Returns (team1, team2)
    """
    if mode == '1v1':
        return [players[0]], [players[1]]

    # For 2v2 and 3v3, try to balance teams by ELO
    # This is a simple implementation - could be improved with better algorithms
    random.shuffle(players)  # Add some randomness

    mid_point = len(players) // 2
    team1 = players[:mid_point]
    team2 = players[mid_point:]

    return team1, team2


def create_match(config: dict, guild_id: str, mode: str, players: List[str]) -> dict:
    """Create a new match with auto-assigned teams"""
    match_id = generate_random_string(8)
    match_name = generate_random_string(4)
    match_password = generate_random_string(4)

    team1, team2 = auto_assign_teams(players, mode)

    match_data = {
        'match_id': match_id,
        'mode': mode,
        'name': match_name,
        'password': match_password,
        'team1': team1,
        'team2': team2,
        'created_at': time.time(),
        'status': 'active',
        'reports': {},  # Will store which team each player reports as winner
        'completed': False
    }

    # Store in active matches
    ranked_data = config['ranked'][guild_id]
    ranked_data['active_matches'][match_id] = match_data

    return match_data


def setup_ranked_commands(client, config):
    """Set up all ranked matchmaking commands"""

    @client.tree.command(name="q", description="Join ranked matchmaking queue")
    @app_commands.describe(mode="Game mode: 1s (1v1), 2s (2v2), or 3s (3v3)")
    async def join_queue(interaction: discord.Interaction, mode: str):
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)

        # Validate mode
        mode_map = {'1s': '1v1', '2s': '2v2', '3s': '3v3'}
        if mode not in mode_map:
            await interaction.response.send_message(
                "❌ Invalid mode! Use `1s` for 1v1, `2s` for 2v2, or `3s` for 3v3",
                ephemeral=True
            )
            return

        queue_mode = mode_map[mode]
        init_ranked_data(config, guild_id)
        ranked_data = config['ranked'][guild_id]

        # Check if user is already in any queue
        for q_mode, queue in ranked_data['queues'].items():
            if user_id in queue:
                await interaction.response.send_message(
                    f"❌ You're already in the {q_mode} queue! Leave it first with `/leave-queue`",
                    ephemeral=True
                )
                return

        # Check if user is in an active match
        for match in ranked_data['active_matches'].values():
            if user_id in match['team1'] + match['team2']:
                await interaction.response.send_message(
                    f"❌ You're already in an active match! Complete it first.",
                    ephemeral=True
                )
                return

        # Add to queue
        queue = ranked_data['queues'][queue_mode]
        queue.append(user_id)

        # Get player data for ELO display
        player_data = get_player_data(config, guild_id, user_id)

        # Check if we can start a match
        required_players = {'1v1': 2, '2v2': 4, '3v3': 6}[queue_mode]

        embed = discord.Embed(
            title="🎮 Joined Ranked Queue",
            color=0x2ecc71
        )
        embed.add_field(name="Mode", value=queue_mode.upper(), inline=True)
        embed.add_field(name="Your ELO", value=str(player_data['elo']), inline=True)
        embed.add_field(name="Queue Status", value=f"{len(queue)}/{required_players}", inline=True)

        if len(queue) >= required_players:
            # Start match!
            players_in_match = queue[:required_players]
            del queue[:required_players]  # Remove players from queue

            match_data = create_match(config, guild_id, queue_mode, players_in_match)
            save_all_configs(config)

            # Create match embed
            match_embed = discord.Embed(
                title="🏁 Match Created!",
                description=f"**Match ID:** `{match_data['match_id']}`",
                color=0xf39c12
            )
            match_embed.add_field(name="Server Name", value=f"`{match_data['name']}`", inline=True)
            match_embed.add_field(name="Password", value=f"`{match_data['password']}`", inline=True)
            match_embed.add_field(name="Mode", value=queue_mode.upper(), inline=True)

            # Team assignments
            team1_mentions = [f"<@{uid}>" for uid in match_data['team1']]
            team2_mentions = [f"<@{uid}>" for uid in match_data['team2']]

            match_embed.add_field(
                name="🔴 Team 1",
                value="\n".join(team1_mentions),
                inline=True
            )
            match_embed.add_field(
                name="🔵 Team 2",
                value="\n".join(team2_mentions),
                inline=True
            )
            match_embed.add_field(
                name="📝 Instructions",
                value="Create a private match with the name and password above. After the match, use `/qr <match_id> <winning_team>` to report results.",
                inline=False
            )

            await interaction.response.send_message(embed=embed)
            await interaction.followup.send(embed=match_embed)

        else:
            save_all_configs(config)
            embed.add_field(
                name="⏳ Waiting",
                value=f"Need {required_players - len(queue)} more player(s)",
                inline=False
            )
            await interaction.response.send_message(embed=embed)

    @client.tree.command(name="qr", description="Report match results")
    @app_commands.describe(
        match_id="The match ID to report results for",
        winner="Which team won: 'team1' or 'team2'"
    )
    async def report_match(interaction: discord.Interaction, match_id: str, winner: str):
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)

        # Validate winner
        if winner.lower() not in ['team1', 'team2']:
            await interaction.response.send_message(
                "❌ Winner must be 'team1' or 'team2'",
                ephemeral=True
            )
            return

        winner = winner.lower()

        # Check if ranked system exists
        if 'ranked' not in config or guild_id not in config['ranked']:
            await interaction.response.send_message(
                "❌ Ranked system not initialized in this server",
                ephemeral=True
            )
            return

        ranked_data = config['ranked'][guild_id]

        # Find the match
        if match_id not in ranked_data['active_matches']:
            await interaction.response.send_message(
                "❌ Match not found or already completed",
                ephemeral=True
            )
            return

        match_data = ranked_data['active_matches'][match_id]

        # Check if user was in this match
        all_players = match_data['team1'] + match_data['team2']
        if user_id not in all_players:
            await interaction.response.send_message(
                "❌ You weren't in this match",
                ephemeral=True
            )
            return

        # Record the report
        match_data['reports'][user_id] = winner

        # Check if we have enough reports to decide
        reports_needed = len(all_players)
        reports_received = len(match_data['reports'])

        # Count votes
        team1_votes = sum(1 for vote in match_data['reports'].values() if vote == 'team1')
        team2_votes = sum(1 for vote in match_data['reports'].values() if vote == 'team2')

        embed = discord.Embed(
            title="📝 Match Report Received",
            description=f"Match: `{match_id}`",
            color=0x3498db
        )
        embed.add_field(name="Your Report", value=f"Team {'1' if winner == 'team1' else '2'} won", inline=True)
        embed.add_field(name="Reports", value=f"{reports_received}/{reports_needed}", inline=True)
        embed.add_field(name="Votes", value=f"Team 1: {team1_votes} | Team 2: {team2_votes}", inline=True)

        # Check if all players reported
        if reports_received == reports_needed:
            # Determine outcome
            if team1_votes > team2_votes:
                final_winner = 'team1'
                winning_team = match_data['team1']
                losing_team = match_data['team2']
            elif team2_votes > team1_votes:
                final_winner = 'team2'
                winning_team = match_data['team2']
                losing_team = match_data['team1']
            else:
                # Tie - match doesn't count
                match_data['status'] = 'disputed'
                match_data['completed'] = True
                ranked_data['completed_matches'].append(match_data)
                del ranked_data['active_matches'][match_id]
                save_all_configs(config)

                embed.title = "⚖️ Match Disputed"
                embed.description = "Teams reported different winners - match doesn't count"
                embed.color = 0xe74c3c
                await interaction.response.send_message(embed=embed)
                return

            # Process ELO changes
            elo_changes = []
            for winner_id in winning_team:
                winner_data = get_player_data(config, guild_id, winner_id)
                for loser_id in losing_team:
                    loser_data = get_player_data(config, guild_id, loser_id)

                    # Calculate average ELO change (simplified)
                    winner_new, loser_new = calculate_elo_change(winner_data['elo'], loser_data['elo'])
                    elo_change = winner_new - winner_data['elo']

                    winner_data['elo'] = winner_new
                    winner_data['wins'] += 1
                    winner_data['matches_played'] += 1

                    loser_data['elo'] = loser_new
                    loser_data['losses'] += 1
                    loser_data['matches_played'] += 1

                    elo_changes.append((winner_id, elo_change))
                    elo_changes.append((loser_id, -elo_change))
                    break  # Only calculate once per winner

            # Mark match as completed
            match_data['status'] = 'completed'
            match_data['winner'] = final_winner
            match_data['completed'] = True
            match_data['completed_at'] = time.time()
            ranked_data['completed_matches'].append(match_data)
            del ranked_data['active_matches'][match_id]

            save_all_configs(config)

            # Create completion embed
            result_embed = discord.Embed(
                title="🏆 Match Completed!",
                description=f"**Winner:** Team {final_winner[-1]}",
                color=0x27ae60
            )

            # Show ELO changes
            elo_text = ""
            for player_id, change in elo_changes:
                if change > 0:
                    elo_text += f"<@{player_id}> **+{change}**\n"
                else:
                    elo_text += f"<@{player_id}> **{change}**\n"

            result_embed.add_field(name="ELO Changes", value=elo_text, inline=False)

            await interaction.response.send_message(embed=embed)
            await interaction.followup.send(embed=result_embed)

        else:
            save_all_configs(config)
            await interaction.response.send_message(embed=embed)

    @client.tree.command(name="leaderboard", description="Show ranked leaderboard")
    async def show_leaderboard(interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)

        if 'ranked' not in config or guild_id not in config['ranked']:
            await interaction.response.send_message(
                "❌ No ranked data found for this server",
                ephemeral=True
            )
            return

        players = config['ranked'][guild_id].get('players', {})

        if not players:
            await interaction.response.send_message(
                "❌ No players have joined ranked matches yet",
                ephemeral=True
            )
            return

        # Sort players by ELO
        sorted_players = sorted(
            players.items(),
            key=lambda x: x[1]['elo'],
            reverse=True
        )

        embed = discord.Embed(
            title="🏆 Ranked Leaderboard",
            color=0xf1c40f
        )

        leaderboard_text = ""
        for i, (user_id, data) in enumerate(sorted_players[:10]):  # Top 10
            rank = i + 1
            emoji = {"1": "🥇", "2": "🥈", "3": "🥉"}.get(str(rank), f"{rank}.")

            try:
                user = await client.fetch_user(int(user_id))
                name = user.display_name
            except:
                name = f"User {user_id}"

            winrate = (data['wins'] / data['matches_played'] * 100) if data['matches_played'] > 0 else 0

            leaderboard_text += f"{emoji} **{name}** - {data['elo']} ELO\n"
            leaderboard_text += f"    W:{data['wins']} L:{data['losses']} ({winrate:.1f}%)\n\n"

        embed.description = leaderboard_text
        await interaction.response.send_message(embed=embed)

    @client.tree.command(name="queue-status", description="Show current queue status")
    async def queue_status(interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)

        if 'ranked' not in config or guild_id not in config['ranked']:
            await interaction.response.send_message(
                "❌ Ranked system not initialized",
                ephemeral=True
            )
            return

        ranked_data = config['ranked'][guild_id]
        queues = ranked_data['queues']

        embed = discord.Embed(
            title="📊 Queue Status",
            color=0x3498db
        )

        for mode, queue in queues.items():
            required = {'1v1': 2, '2v2': 4, '3v3': 6}[mode]
            embed.add_field(
                name=f"{mode.upper()} Queue",
                value=f"{len(queue)}/{required} players",
                inline=True
            )

        active_matches = len(ranked_data['active_matches'])
        embed.add_field(
            name="Active Matches",
            value=str(active_matches),
            inline=True
        )

        await interaction.response.send_message(embed=embed)

    @client.tree.command(name="leave-queue", description="Leave all ranked queues")
    async def leave_queue(interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)

        if 'ranked' not in config or guild_id not in config['ranked']:
            await interaction.response.send_message(
                "❌ Ranked system not initialized",
                ephemeral=True
            )
            return

        ranked_data = config['ranked'][guild_id]
        removed_from = []

        # Remove from all queues
        for mode, queue in ranked_data['queues'].items():
            if user_id in queue:
                queue.remove(user_id)
                removed_from.append(mode)

        if not removed_from:
            await interaction.response.send_message(
                "❌ You're not in any queue",
                ephemeral=True
            )
            return

        save_all_configs(config)

        embed = discord.Embed(
            title="Left Queue",
            description=f"Removed from: {', '.join(removed_from)}",
            color=0xe74c3c
        )
        await interaction.response.send_message(embed=embed)