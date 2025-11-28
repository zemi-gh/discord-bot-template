#!/bin/bash

# Discord Bot Setup Script
# This script will install dependencies, configure the bot, and set it up to run in the background

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    color=$1
    message=$2
    echo -e "${color}${message}${NC}"
}

# Function to print section headers
print_header() {
    echo ""
    print_color "$CYAN" "======================================================"
    print_color "$CYAN" "$1"
    print_color "$CYAN" "======================================================"
    echo ""
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Clear screen
clear

print_header "🚀 Discord Bot Setup Script"

print_color "$GREEN" "Welcome to the Discord Bot setup wizard!"
print_color "$YELLOW" "This script will:"
echo "  ✓ Check system requirements"
echo "  ✓ Install Python dependencies"
echo "  ✓ Configure your bot"
echo "  ✓ Set up background running"
echo ""

read -p "Press Enter to continue..."

# ========================================
# Step 1: Check Python version
# ========================================
print_header "Step 1/6: Checking Python Installation"

if ! command_exists python3; then
    print_color "$RED" "❌ Python 3 is not installed!"
    print_color "$YELLOW" "Please install Python 3.9 or higher and try again."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

print_color "$BLUE" "Found Python version: $PYTHON_VERSION"

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]; }; then
    print_color "$RED" "❌ Python 3.9 or higher is required!"
    print_color "$YELLOW" "You have Python $PYTHON_VERSION"
    exit 1
fi

print_color "$GREEN" "✓ Python version is compatible!"

# ========================================
# Step 2: Create virtual environment
# ========================================
print_header "Step 2/6: Setting Up Virtual Environment"

if [ -d "venv" ]; then
    print_color "$YELLOW" "Virtual environment already exists."
    read -p "Do you want to recreate it? (y/n): " recreate_venv
    if [ "$recreate_venv" = "y" ]; then
        rm -rf venv
        python3 -m venv venv
        print_color "$GREEN" "✓ Virtual environment recreated!"
    fi
else
    python3 -m venv venv
    print_color "$GREEN" "✓ Virtual environment created!"
fi

# Activate virtual environment
source venv/bin/activate

# ========================================
# Step 3: Install dependencies
# ========================================
print_header "Step 3/6: Installing Dependencies"

print_color "$BLUE" "Installing Python packages..."

pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

print_color "$GREEN" "✓ All dependencies installed!"

# ========================================
# Step 4: Configure the bot
# ========================================
print_header "Step 4/6: Bot Configuration"

print_color "$YELLOW" "Let's configure your bot!"
echo ""

# Ask for bot token
print_color "$CYAN" "📝 Discord Bot Token"
print_color "$YELLOW" "Get your token from: https://discord.com/developers/applications"
read -p "Enter your Discord bot token: " BOT_TOKEN

# Ask for guild ID
echo ""
print_color "$CYAN" "🏰 Guild (Server) ID"
print_color "$YELLOW" "Enable Developer Mode in Discord, then right-click your server and 'Copy ID'"
read -p "Enter your Discord server ID (optional, press Enter to skip): " GUILD_ID
if [ -z "$GUILD_ID" ]; then
    GUILD_ID="null"
fi

# Ask for admin user IDs
echo ""
print_color "$CYAN" "👑 Bot Administrator(s)"
print_color "$YELLOW" "Right-click on yourself in Discord and select 'Copy ID'"
ADMIN_USERS="[]"
while true; do
    read -p "Enter a Discord user ID (or press Enter to finish): " USER_ID
    if [ -z "$USER_ID" ]; then
        break
    fi

    if [ "$ADMIN_USERS" = "[]" ]; then
        ADMIN_USERS="[\"$USER_ID\"]"
    else
        ADMIN_USERS=$(echo $ADMIN_USERS | sed "s/\]/, \"$USER_ID\"]/")
    fi

    print_color "$GREEN" "✓ Added admin: $USER_ID"
done

# Ask for bot name
echo ""
print_color "$CYAN" "🤖 Bot Branding"
read -p "Enter your bot name [default: RLC Bot]: " BOT_NAME
BOT_NAME=${BOT_NAME:-RLC Bot}

read -p "Enter bot description [default: A customizable Discord bot]: " BOT_DESC
BOT_DESC=${BOT_DESC:-A customizable Discord bot for server management and community engagement!}

# Ask for bot status
echo ""
print_color "$CYAN" "🎮 Bot Status (Optional)"
read -p "Enter bot status type (playing/watching/listening/competing) [default: playing]: " STATUS_TYPE
STATUS_TYPE=${STATUS_TYPE:-playing}

read -p "Enter bot status text [default: /help for commands]: " STATUS_TEXT
STATUS_TEXT=${STATUS_TEXT:-/help for commands}

# Create config directory if it doesn't exist
mkdir -p config

# Create config.json
print_color "$BLUE" "Creating config.json..."

cat > config/config.json << EOF
{
    "bot_token": "$BOT_TOKEN",
    "admin_users": $ADMIN_USERS,
    "guild_id": "$GUILD_ID",
    "branding": {
        "bot_name": "$BOT_NAME",
        "bot_description": "$BOT_DESC",
        "welcome_title": "Welcome to $BOT_NAME!",
        "welcome_description": "I'm **$BOT_NAME**, your customizable Discord bot featuring:\\n\\n**Server Management** - Moderation, roles, channels & more\\n**Ticket System** - Professional support ticket management\\n**Ranked Matchmaking** - Competitive 1v1, 2v2, 3v3 matches\\n**Polls & Utilities** - Engage your community\\n\\nType \\\`/help\\\` to see all available commands!",
        "help_title": "$BOT_NAME - Command List",
        "footer_text": "$BOT_NAME - Made with love",
        "ticket_footer": "$BOT_NAME Ticket System",
        "features_list": "Server Management\\nTicket System\\nRanked Matchmaking\\nPolls & Utilities\\nCustomizable"
    },
    "settings": {
        "welcome_enabled": false,
        "welcome_channel_id": null,
        "welcome_message": "Welcome {user} to {server}!\\nYou are member #{members}",
        "log_channel_id": null,
        "auto_role_id": null,
        "status_type": "$STATUS_TYPE",
        "status_text": "$STATUS_TEXT"
    },
    "ticket_settings": {
        "ticket_category_id": null,
        "support_role_id": null,
        "transcript_channel_id": null,
        "transcript_enabled": true
    },
    "server_stats": {},
    "ranked": {}
}
EOF

print_color "$GREEN" "✓ Configuration saved!"

# ========================================
# Step 5: Choose background running method
# ========================================
print_header "Step 5/6: Background Running Setup"

print_color "$YELLOW" "Choose how to run the bot in the background:"
echo ""
echo "  1) Screen (recommended - easy to attach/detach)"
echo "  2) Systemd Service (runs on system startup)"
echo "  3) Nohup (simple background process)"
echo ""

read -p "Enter your choice (1-3) [default: 1]: " RUN_METHOD
RUN_METHOD=${RUN_METHOD:-1}

case $RUN_METHOD in
    1)
        # Screen method
        if ! command_exists screen; then
            print_color "$YELLOW" "Screen is not installed. Installing..."

            if command_exists apt-get; then
                sudo apt-get update > /dev/null 2>&1
                sudo apt-get install -y screen > /dev/null 2>&1
            elif command_exists yum; then
                sudo yum install -y screen > /dev/null 2>&1
            else
                print_color "$RED" "Could not install screen automatically."
                print_color "$YELLOW" "Please install screen manually and run this script again."
                exit 1
            fi
        fi

        print_color "$GREEN" "✓ Screen is available!"
        RUN_COMMAND="screen"
        ;;
    2)
        # Systemd service
        SERVICE_FILE="/etc/systemd/system/rlc-bot.service"
        CURRENT_DIR=$(pwd)
        CURRENT_USER=$(whoami)

        print_color "$BLUE" "Creating systemd service..."

        sudo bash -c "cat > $SERVICE_FILE" << EOF
[Unit]
Description=RLC Discord Bot
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
ExecStart=$CURRENT_DIR/venv/bin/python $CURRENT_DIR/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

        sudo systemctl daemon-reload
        sudo systemctl enable rlc-bot.service

        print_color "$GREEN" "✓ Systemd service created!"
        RUN_COMMAND="systemd"
        ;;
    3)
        # Nohup method
        print_color "$GREEN" "✓ Will use nohup for background running"
        RUN_COMMAND="nohup"
        ;;
    *)
        print_color "$RED" "Invalid choice. Defaulting to screen."
        RUN_COMMAND="screen"
        ;;
esac

# ========================================
# Step 6: Create helper scripts
# ========================================
print_header "Step 6/6: Creating Helper Scripts"

CURRENT_DIR=$(pwd)

# Create start.sh
cat > start.sh << 'EOF'
#!/bin/bash
source venv/bin/activate

if pgrep -f "python.*main.py" > /dev/null; then
    echo "⚠️  Bot is already running!"
    exit 1
fi

EOF

if [ "$RUN_COMMAND" = "screen" ]; then
    cat >> start.sh << 'EOF'
screen -dmS rlc-bot python main.py
echo "✅ Bot started in screen session 'rlc-bot'"
echo "💡 Use ./logs.sh to view logs"
echo "💡 Use 'screen -r rlc-bot' to attach to the session"
EOF
elif [ "$RUN_COMMAND" = "systemd" ]; then
    cat >> start.sh << 'EOF'
sudo systemctl start rlc-bot.service
echo "✅ Bot started as systemd service"
echo "💡 Use ./logs.sh to view logs"
echo "💡 Use ./status.sh to check status"
EOF
else
    cat >> start.sh << 'EOF'
nohup python main.py > logs/bot.log 2>&1 &
echo $! > .bot.pid
echo "✅ Bot started in background"
echo "💡 Use ./logs.sh to view logs"
EOF
fi

chmod +x start.sh

# Create stop.sh
cat > stop.sh << 'EOF'
#!/bin/bash

EOF

if [ "$RUN_COMMAND" = "screen" ]; then
    cat >> stop.sh << 'EOF'
if screen -list | grep -q "rlc-bot"; then
    screen -S rlc-bot -X quit
    echo "✅ Bot stopped"
else
    echo "⚠️  Bot is not running"
fi
EOF
elif [ "$RUN_COMMAND" = "systemd" ]; then
    cat >> stop.sh << 'EOF'
sudo systemctl stop rlc-bot.service
echo "✅ Bot stopped"
EOF
else
    cat >> stop.sh << 'EOF'
if [ -f .bot.pid ]; then
    PID=$(cat .bot.pid)
    if ps -p $PID > /dev/null; then
        kill $PID
        rm .bot.pid
        echo "✅ Bot stopped"
    else
        echo "⚠️  Bot is not running"
        rm .bot.pid
    fi
else
    pkill -f "python.*main.py"
    echo "✅ Bot stopped"
fi
EOF
fi

chmod +x stop.sh

# Create restart.sh
cat > restart.sh << 'EOF'
#!/bin/bash
echo "🔄 Restarting bot..."
./stop.sh
sleep 2
./start.sh
EOF

chmod +x restart.sh

# Create logs.sh
cat > logs.sh << 'EOF'
#!/bin/bash

EOF

if [ "$RUN_COMMAND" = "screen" ]; then
    cat >> logs.sh << 'EOF'
if screen -list | grep -q "rlc-bot"; then
    echo "📋 Bot logs (Ctrl+C to exit):"
    echo "💡 To attach to screen session, use: screen -r rlc-bot"
    echo ""
    screen -S rlc-bot -X hardcopy logs/bot.log
    tail -f logs/bot.log 2>/dev/null || echo "No logs yet. Bot may be starting..."
else
    echo "⚠️  Bot is not running in screen"
fi
EOF
elif [ "$RUN_COMMAND" = "systemd" ]; then
    cat >> logs.sh << 'EOF'
echo "📋 Bot logs (Ctrl+C to exit):"
echo ""
sudo journalctl -u rlc-bot.service -f
EOF
else
    cat >> logs.sh << 'EOF'
if [ -f logs/bot.log ]; then
    echo "📋 Bot logs (Ctrl+C to exit):"
    echo ""
    tail -f logs/bot.log
else
    echo "⚠️  No log file found"
fi
EOF
fi

chmod +x logs.sh

# Create status.sh
cat > status.sh << 'EOF'
#!/bin/bash

echo "🤖 Discord Bot Status"
echo "======================="
echo ""

EOF

if [ "$RUN_COMMAND" = "screen" ]; then
    cat >> status.sh << 'EOF'
if screen -list | grep -q "rlc-bot"; then
    echo "Status: ✅ Running (in screen)"
    echo "Session: rlc-bot"
    echo ""
    echo "Commands:"
    echo "  ./logs.sh          - View logs"
    echo "  screen -r rlc-bot  - Attach to session"
    echo "  ./stop.sh          - Stop the bot"
    echo "  ./restart.sh       - Restart the bot"
else
    echo "Status: ❌ Not running"
    echo ""
    echo "Start the bot with: ./start.sh"
fi
EOF
elif [ "$RUN_COMMAND" = "systemd" ]; then
    cat >> status.sh << 'EOF'
sudo systemctl status rlc-bot.service --no-pager
echo ""
echo "Commands:"
echo "  ./logs.sh     - View logs"
echo "  ./stop.sh     - Stop the bot"
echo "  ./start.sh    - Start the bot"
echo "  ./restart.sh  - Restart the bot"
EOF
else
    cat >> status.sh << 'EOF'
if pgrep -f "python.*main.py" > /dev/null; then
    PID=$(pgrep -f "python.*main.py")
    echo "Status: ✅ Running"
    echo "PID: $PID"
else
    echo "Status: ❌ Not running"
fi

echo ""
echo "Commands:"
echo "  ./start.sh    - Start the bot"
echo "  ./stop.sh     - Stop the bot"
echo "  ./restart.sh  - Restart the bot"
echo "  ./logs.sh     - View logs"
EOF
fi

chmod +x status.sh

# Create logs directory
mkdir -p logs

print_color "$GREEN" "✓ Helper scripts created!"

# ========================================
# Setup Complete
# ========================================
print_header "🎉 Setup Complete!"

print_color "$GREEN" "Your Discord Bot is now configured and ready to run!"
echo ""

print_color "$CYAN" "📁 Configuration saved to:"
echo "  └─ config/config.json"
echo ""

print_color "$CYAN" "🛠️  Helper scripts created:"
echo "  └─ ./start.sh      - Start the bot"
echo "  └─ ./stop.sh       - Stop the bot"
echo "  └─ ./restart.sh    - Restart the bot"
echo "  └─ ./logs.sh       - View bot logs"
echo "  └─ ./status.sh     - Check bot status"
echo ""

print_color "$YELLOW" "🚀 Quick Start:"
if [ "$RUN_COMMAND" = "systemd" ]; then
    echo "  1. Start the bot: ./start.sh"
    echo "  2. Check status:  ./status.sh"
    echo "  3. View logs:     ./logs.sh"
    echo ""
    print_color "$BLUE" "  The bot will automatically start on system reboot!"
else
    echo "  1. Start the bot: ./start.sh"
    echo "  2. View logs:     ./logs.sh"
    echo "  3. Check status:  ./status.sh"
fi

echo ""
read -p "Do you want to start the bot now? (y/n): " START_NOW

if [ "$START_NOW" = "y" ]; then
    echo ""
    print_color "$BLUE" "Starting bot..."
    ./start.sh
    echo ""

    sleep 3

    print_color "$GREEN" "🎉 Done! Your bot should now be running!"
    echo ""
    print_color "$YELLOW" "💡 Tips:"
    echo "  • Use ./logs.sh to check if the bot connected successfully"
    echo "  • Make sure your bot has the right permissions in Discord"
    echo "  • Use /help command in Discord to see all available commands"
else
    echo ""
    print_color "$YELLOW" "You can start the bot later with: ./start.sh"
fi

echo ""
print_color "$PURPLE" "======================================================"
print_color "$PURPLE" "Thank you for using this Discord Bot! 🚀"
print_color "$PURPLE" "======================================================"
echo ""
