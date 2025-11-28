# Discord Bot Template

A customizable Discord bot template with server management, ticket system, and server statistics features.

## Features

- 🎛️ **Admin Panel** - Button-based dashboard for easy server administration
- 👑 **Server Management** - Moderation, roles, channels & more
- 🎫 **Ticket System** - Professional support ticket management
- 🏆 **Ranked Matchmaking** - 1v1, 2v2, 3v3 competitive matches with ELO system
- 📊 **Server Statistics** - Auto-updating member count channels
- 📊 **Polls & Utilities** - Engage your community
- ⚙️ **Fully Customizable** - Configure all branding via config.json

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure the bot:
   - Edit `config/config.json` with your bot token and admin user IDs
   - Customize the branding section to match your bot's name and style

3. Run the bot:
   ```bash
   ./start.sh    # Start the bot with full setup
   ./stop.sh     # Stop the bot safely
   python main.py  # Or run directly
   ```

## Configuration

The bot is fully customizable via `config/config.json`. Key sections:

### Branding
Change your bot's name and appearance throughout all commands and embeds:

```json
"branding": {
    "bot_name": "Your Bot Name",
    "bot_description": "Your bot description",
    "welcome_title": "👋 Welcome message title",
    "welcome_description": "Welcome message content",
    "help_title": "🚀 Help command title",
    "footer_text": "Footer text for embeds",
    "ticket_footer": "Ticket system footer",
    "features_list": "Features shown in /botinfo"
}
```

### Server Statistics
The `/serverstats` command creates auto-updating voice channels showing member counts:

- **All Members**: Total members and bots
- **Members**: Human users only
- **Bots**: Bot accounts only

Channels update every 10 minutes automatically.

### Admin Panel System
A comprehensive button-based administration dashboard for server owners:

- **Easy Access**: Single command `/adminpanel` opens the full dashboard
- **Button Controls**: Interactive buttons for all admin actions
- **Moderation Tools**: Ban, kick, timeout members with modal forms
- **Channel Management**: Create text/voice channels, lock/unlock channels
- **Role Management**: Create new roles with custom colors
- **Mass Actions**: Bulk delete messages in channels
- **Server Information**: Quick access to server stats and info
- **Access Control**: Server owner can grant dashboard access to trusted users
- **Permission System**: Only authorized users can use the panel
- **Safe & Secure**: All actions require proper Discord permissions

**Admin Panel Commands:**
- `/adminpanel` - Open the admin panel dashboard
- `/adminpanel-grant @user` - Grant panel access to a user (owner only)
- `/adminpanel-revoke @user` - Revoke panel access (owner only)
- `/adminpanel-list` - List users with panel access (owner only)

### Ranked Matchmaking System
A complete competitive matchmaking system with ELO rating:

- **Queue System**: Join 1v1, 2v2, or 3v3 queues with `/q <mode>`
- **Auto-Matching**: When enough players join, match is created automatically
- **Random Match Details**: 8-character match ID with 4-character name/password
- **Team Assignment**: Automatic balanced team assignment
- **ELO Rating**: Start at 200 ELO, gain/lose 19-24 points per match
- **Result Reporting**: All players report results, majority decides winner
- **Dispute Resolution**: Conflicting reports result in no ELO change
- **Unified Leaderboard**: Single ranking system across all game modes

## Commands

### Admin Panel Commands (Owner Only)
- `/adminpanel` - Open the comprehensive admin dashboard
- `/adminpanel-grant @user` - Grant admin panel access to a user
- `/adminpanel-revoke @user` - Revoke admin panel access from a user
- `/adminpanel-list` - View all users with admin panel access

### Admin Commands
- `/serverstats on` - Enable server stats with auto-updating channels
- `/serverstats off` - Disable and remove stats channels
- `/addadmin @user` - Add bot administrator
- `/ticket-setup` - Configure ticket system
- `/setwelcome #channel` - Set welcome channel
- And many more moderation and management commands...

### Ranked Matchmaking Commands
- `/q 1s` - Join 1v1 ranked queue
- `/q 2s` - Join 2v2 ranked queue
- `/q 3s` - Join 3v3 ranked queue
- `/qr <match_id> <winner>` - Report match results (team1 or team2)
- `/leaderboard` - Show ranked leaderboard
- `/queue-status` - Check current queue status
- `/leave-queue` - Leave all ranked queues

### Public Commands
- `/help` - Show all available commands
- `/serverinfo` - Server information
- `/userinfo @user` - User information
- `/poll "Question" "Option1" "Option2"` - Create polls
- And more utility commands...

## Bot Management Scripts

The bot includes comprehensive management scripts:

### setup.sh
Interactive setup script that configures:
- Virtual environment creation
- Dependency installation
- Bot configuration (token, admins, status)
- Background running methods (screen, systemd, nohup)
- Helper script generation

```bash
chmod +x setup.sh
./setup.sh
```

### start.sh
Comprehensive startup script with:
- System requirements checking
- Virtual environment activation
- Dependency verification
- Configuration validation
- Network connectivity checks
- Automatic logging

```bash
./start.sh              # Full startup with all checks
./start.sh --skip-deps  # Skip dependency installation
./start.sh --dev        # Development mode with verbose logging
```

### stop.sh
Safe shutdown script that:
- Detects running method (screen/systemd/nohup/direct)
- Graceful shutdown with SIGTERM
- Force shutdown with SIGKILL if needed
- Cleanup of PID files and sessions

```bash
./stop.sh              # Safe stop with auto-detection
./stop.sh --force      # Force stop immediately
./stop.sh --quiet      # Minimal output
```

## Customization

No code changes needed! Simply edit `config/config.json` and restart the bot to apply changes. The bot will automatically use your custom branding in all embeds, messages, and commands.

## Support

For issues or questions, create an issue in the repository.