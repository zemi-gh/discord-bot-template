#!/bin/bash

# ============================================================================
# Discord Bot Startup Script
# ============================================================================
# This script handles the complete setup and startup process for the Discord bot
# including environment setup, dependency installation, configuration validation,
# and bot execution with proper error handling and logging.
# ============================================================================

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/startup_$(date +%Y%m%d_%H%M%S).log"
BOT_LOG_FILE="$LOG_DIR/bot_$(date +%Y%m%d_%H%M%S).log"
CONFIG_FILE="$SCRIPT_DIR/config/config.json"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"
VENV_DIR="$SCRIPT_DIR/venv"

# Create logs directory
mkdir -p "$LOG_DIR"

# ============================================================================
# Utility Functions
# ============================================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

print_header() {
    echo -e "${PURPLE}"
    echo "============================================================================"
    echo "                    🚀 DISCORD BOT STARTUP SCRIPT"
    echo "============================================================================"
    echo -e "${NC}"
    log "INFO" "Starting Discord bot startup process"
}

print_section() {
    echo -e "\n${CYAN}▶ $1${NC}"
    log "INFO" "Section: $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    log "SUCCESS" "$1"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    log "WARNING" "$1"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    log "ERROR" "$1"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
    log "INFO" "$1"
}

# ============================================================================
# System Requirements Check
# ============================================================================

check_system_requirements() {
    print_section "Checking System Requirements"

    # Check if Python 3.9+ is installed
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_success "Python 3 found: $PYTHON_VERSION"

        # Check if version is 3.9+
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 9 ]; then
            print_success "Python version is compatible (3.9+)"
        else
            print_error "Python 3.9+ is required. Current version: $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 is not installed. Please install Python 3.9+"
        exit 1
    fi

    # Check if pip is available
    if command -v pip3 >/dev/null 2>&1; then
        print_success "pip3 is available"
    elif command -v pip >/dev/null 2>&1; then
        print_success "pip is available"
    else
        print_error "pip is not installed. Please install pip"
        exit 1
    fi

    # Check if git is available (optional)
    if command -v git >/dev/null 2>&1; then
        print_success "Git is available"
    else
        print_warning "Git is not installed (optional for updates)"
    fi

    # Check available disk space
    AVAILABLE_SPACE=$(df "$SCRIPT_DIR" | awk 'NR==2 {print $4}')
    if [ "$AVAILABLE_SPACE" -gt 100000 ]; then
        print_success "Sufficient disk space available"
    else
        print_warning "Low disk space detected"
    fi
}

# ============================================================================
# Virtual Environment Setup
# ============================================================================

setup_virtual_environment() {
    print_section "Setting Up Virtual Environment"

    if [ -d "$VENV_DIR" ]; then
        print_info "Virtual environment already exists"
    else
        print_info "Creating new virtual environment..."
        python3 -m venv "$VENV_DIR"
        if [ $? -eq 0 ]; then
            print_success "Virtual environment created successfully"
        else
            print_error "Failed to create virtual environment"
            exit 1
        fi
    fi

    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    if [ $? -eq 0 ]; then
        print_success "Virtual environment activated"
    else
        print_error "Failed to activate virtual environment"
        exit 1
    fi

    # Upgrade pip
    print_info "Upgrading pip..."
    pip install --upgrade pip >/dev/null 2>&1
    print_success "pip upgraded"
}

# ============================================================================
# Dependencies Installation
# ============================================================================

install_dependencies() {
    print_section "Installing Dependencies"

    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        print_error "requirements.txt not found!"
        exit 1
    fi

    print_info "Installing Python packages from requirements.txt..."
    pip install -r "$REQUIREMENTS_FILE"

    if [ $? -eq 0 ]; then
        print_success "All dependencies installed successfully"
    else
        print_error "Failed to install some dependencies"
        exit 1
    fi

    # Verify critical packages
    print_info "Verifying critical packages..."
    python3 -c "import discord; print('discord.py:', discord.__version__)" 2>/dev/null
    if [ $? -eq 0 ]; then
        print_success "discord.py is properly installed"
    else
        print_error "discord.py installation failed"
        exit 1
    fi
}

# ============================================================================
# Configuration Validation
# ============================================================================

validate_configuration() {
    print_section "Validating Configuration"

    # Check if config directory exists
    if [ ! -d "$SCRIPT_DIR/config" ]; then
        print_info "Creating config directory..."
        mkdir -p "$SCRIPT_DIR/config"
    fi

    # Check if config.json exists
    if [ ! -f "$CONFIG_FILE" ]; then
        print_warning "config.json not found. Bot will create default configuration."
        print_info "You will need to edit config/config.json with your bot token before the bot can start properly."
        return 0
    fi

    # Validate JSON syntax
    python3 -c "import json; json.load(open('$CONFIG_FILE'))" 2>/dev/null
    if [ $? -eq 0 ]; then
        print_success "Configuration file is valid JSON"
    else
        print_error "Configuration file contains invalid JSON"
        exit 1
    fi

    # Check for bot token
    BOT_TOKEN=$(python3 -c "import json; config=json.load(open('$CONFIG_FILE')); print(config.get('bot_token', ''))" 2>/dev/null)
    if [ "$BOT_TOKEN" = "YOUR_DISCORD_BOT_TOKEN_HERE" ] || [ -z "$BOT_TOKEN" ]; then
        print_warning "Bot token not configured. Please edit config/config.json"
        print_info "The bot will start but may fail to connect to Discord"
    else
        print_success "Bot token is configured"
    fi

    # Check for admin users
    ADMIN_COUNT=$(python3 -c "import json; config=json.load(open('$CONFIG_FILE')); print(len(config.get('admin_users', [])))" 2>/dev/null)
    if [ "$ADMIN_COUNT" -eq 0 ]; then
        print_warning "No admin users configured"
        print_info "Use /addadmin command to add administrators after bot starts"
    else
        print_success "$ADMIN_COUNT admin user(s) configured"
    fi
}

# ============================================================================
# File Permissions Check
# ============================================================================

check_permissions() {
    print_section "Checking File Permissions"

    # Check if main.py is readable
    if [ -r "$SCRIPT_DIR/main.py" ]; then
        print_success "main.py is readable"
    else
        print_error "Cannot read main.py"
        exit 1
    fi

    # Check if config directory is writable
    if [ -w "$SCRIPT_DIR/config" ]; then
        print_success "Config directory is writable"
    else
        print_error "Config directory is not writable"
        exit 1
    fi

    # Check if logs directory is writable
    if [ -w "$LOG_DIR" ]; then
        print_success "Logs directory is writable"
    else
        print_error "Logs directory is not writable"
        exit 1
    fi
}

# ============================================================================
# Port and Network Check
# ============================================================================

check_network() {
    print_section "Checking Network Connectivity"

    # Check internet connectivity
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        print_success "Internet connectivity available"
    else
        print_warning "No internet connectivity detected"
        print_info "Bot may fail to connect to Discord"
    fi

    # Check Discord API connectivity
    if command -v curl >/dev/null 2>&1; then
        if curl -s --connect-timeout 5 https://discord.com/api/v10/gateway >/dev/null; then
            print_success "Discord API is reachable"
        else
            print_warning "Discord API connectivity issues detected"
        fi
    else
        print_info "curl not available, skipping Discord API check"
    fi
}

# ============================================================================
# Bot Startup
# ============================================================================

start_bot() {
    print_section "Starting Discord Bot"

    cd "$SCRIPT_DIR"

    print_info "Launching bot with logging..."
    print_info "Log file: $BOT_LOG_FILE"
    print_info "Press Ctrl+C to stop the bot"

    echo -e "\n${WHITE}============================================================================"
    echo "                           🤖 BOT OUTPUT"
    echo "============================================================================${NC}\n"

    # Start the bot with both console and file logging
    python3 main.py 2>&1 | tee "$BOT_LOG_FILE"

    BOT_EXIT_CODE=$?

    echo -e "\n${WHITE}============================================================================"
    echo "                           🛑 BOT STOPPED"
    echo "============================================================================${NC}\n"

    if [ $BOT_EXIT_CODE -eq 0 ]; then
        print_success "Bot stopped normally"
    else
        print_error "Bot stopped with error code: $BOT_EXIT_CODE"
        print_info "Check the log file for details: $BOT_LOG_FILE"
    fi

    return $BOT_EXIT_CODE
}

# ============================================================================
# Cleanup and Signal Handling
# ============================================================================

cleanup() {
    print_info "Cleaning up..."
    if [ -n "$VENV_DIR" ] && [ -d "$VENV_DIR" ]; then
        deactivate 2>/dev/null || true
    fi
    print_info "Cleanup completed"
}

# Set up signal handlers
trap cleanup EXIT
trap 'print_warning "Received interrupt signal, stopping bot..."; exit 1' INT TERM

# ============================================================================
# Help Function
# ============================================================================

show_help() {
    echo -e "${CYAN}Discord Bot Startup Script${NC}"
    echo
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  --help, -h          Show this help message"
    echo "  --no-venv          Skip virtual environment setup"
    echo "  --skip-deps        Skip dependency installation"
    echo "  --skip-checks      Skip system requirement checks"
    echo "  --dev              Development mode (verbose logging)"
    echo
    echo "Examples:"
    echo "  $0                 # Full startup with all checks"
    echo "  $0 --no-venv       # Start without virtual environment"
    echo "  $0 --dev           # Start in development mode"
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    # Parse command line arguments
    SKIP_VENV=false
    SKIP_DEPS=false
    SKIP_CHECKS=false
    DEV_MODE=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                exit 0
                ;;
            --no-venv)
                SKIP_VENV=true
                shift
                ;;
            --skip-deps)
                SKIP_DEPS=true
                shift
                ;;
            --skip-checks)
                SKIP_CHECKS=true
                shift
                ;;
            --dev)
                DEV_MODE=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Start the process
    print_header

    if [ "$SKIP_CHECKS" = false ]; then
        check_system_requirements
        check_permissions
        check_network
    fi

    if [ "$SKIP_VENV" = false ]; then
        setup_virtual_environment
    fi

    if [ "$SKIP_DEPS" = false ]; then
        install_dependencies
    fi

    validate_configuration

    # Start the bot
    start_bot

    exit $?
}

# Run main function with all arguments
main "$@"