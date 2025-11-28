#!/bin/bash

# ============================================================================
# Discord Bot Stop Script
# ============================================================================
# This script safely stops the Discord bot regardless of how it was started
# (screen, systemd, nohup, or direct execution)
# ============================================================================

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.bot.pid"
LOG_DIR="$SCRIPT_DIR/logs"

# Utility functions
print_header() {
    echo -e "${PURPLE}"
    echo "============================================================================"
    echo "                    🛑 DISCORD BOT STOP SCRIPT"
    echo "============================================================================"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_section() {
    echo -e "\n${CYAN}▶ $1${NC}"
}

# Function to check if bot is running
is_bot_running() {
    if pgrep -f "python.*main.py" > /dev/null; then
        return 0
    fi
    return 1
}

# Function to get bot PID
get_bot_pid() {
    pgrep -f "python.*main.py"
}

# Function to stop bot via screen
stop_screen() {
    print_section "Checking Screen Sessions"

    if command -v screen >/dev/null 2>&1; then
        if screen -list | grep -q "rlc-bot"; then
            print_info "Found screen session 'rlc-bot'"
            screen -S rlc-bot -X quit
            sleep 2

            if screen -list | grep -q "rlc-bot"; then
                print_warning "Screen session still active, force closing..."
                screen -S rlc-bot -X kill
                return 0
            else
                print_success "Screen session terminated"
                return 0
            fi
        fi
    fi
    return 1
}

# Function to stop bot via systemd
stop_systemd() {
    print_section "Checking Systemd Service"

    if command -v systemctl >/dev/null 2>&1; then
        if systemctl is-active --quiet rlc-bot.service 2>/dev/null; then
            print_info "Found systemd service 'rlc-bot.service'"
            sudo systemctl stop rlc-bot.service

            sleep 2

            if systemctl is-active --quiet rlc-bot.service; then
                print_error "Failed to stop systemd service"
                return 1
            else
                print_success "Systemd service stopped"
                return 0
            fi
        fi
    fi
    return 1
}

# Function to stop bot via PID file
stop_pid_file() {
    print_section "Checking PID File"

    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        print_info "Found PID file with PID: $PID"

        if ps -p "$PID" > /dev/null 2>&1; then
            print_info "Sending SIGTERM to process $PID..."
            kill "$PID" 2>/dev/null

            # Wait for process to terminate (max 10 seconds)
            for i in {1..10}; do
                if ! ps -p "$PID" > /dev/null 2>&1; then
                    rm -f "$PID_FILE"
                    print_success "Bot stopped gracefully"
                    return 0
                fi
                sleep 1
            done

            # Force kill if still running
            print_warning "Process didn't stop gracefully, sending SIGKILL..."
            kill -9 "$PID" 2>/dev/null
            rm -f "$PID_FILE"
            print_success "Bot force stopped"
            return 0
        else
            print_warning "Process $PID not found, cleaning up PID file"
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Function to stop bot by process name
stop_by_process() {
    print_section "Searching for Bot Process"

    if is_bot_running; then
        BOT_PID=$(get_bot_pid)
        print_info "Found bot process with PID: $BOT_PID"

        print_info "Sending SIGTERM to process..."
        kill "$BOT_PID" 2>/dev/null

        # Wait for process to terminate (max 10 seconds)
        for i in {1..10}; do
            if ! is_bot_running; then
                print_success "Bot stopped gracefully"
                return 0
            fi
            sleep 1
        done

        # Force kill if still running
        print_warning "Process didn't stop gracefully, sending SIGKILL..."
        kill -9 "$BOT_PID" 2>/dev/null
        sleep 1

        if ! is_bot_running; then
            print_success "Bot force stopped"
            return 0
        else
            print_error "Failed to stop bot process"
            return 1
        fi
    fi
    return 1
}

# Function to show stop summary
show_summary() {
    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}                         🎉 Bot Stopped Successfully!${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════════════════════${NC}"
    echo ""
    print_info "Next steps:"
    echo "  • To start the bot again: ./start.sh"
    echo "  • To view logs: ls -lh $LOG_DIR/"
    echo "  • To check status: ps aux | grep main.py"
    echo ""
}

# Function to show help
show_help() {
    echo "Discord Bot Stop Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help, -h       Show this help message"
    echo "  --force, -f      Force stop without graceful shutdown"
    echo "  --quiet, -q      Minimal output"
    echo ""
    echo "This script automatically detects how the bot was started and stops it accordingly."
    echo "It checks for screen sessions, systemd services, PID files, and running processes."
}

# Main execution
main() {
    FORCE=false
    QUIET=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                exit 0
                ;;
            --force|-f)
                FORCE=true
                shift
                ;;
            --quiet|-q)
                QUIET=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    if [ "$QUIET" = false ]; then
        print_header
    fi

    # Try different stop methods in order of preference
    STOPPED=false

    # Method 1: Try systemd first (cleanest for production)
    if ! $STOPPED && stop_systemd; then
        STOPPED=true
    fi

    # Method 2: Try screen session
    if ! $STOPPED && stop_screen; then
        STOPPED=true
    fi

    # Method 3: Try PID file
    if ! $STOPPED && stop_pid_file; then
        STOPPED=true
    fi

    # Method 4: Find and stop by process name
    if ! $STOPPED && stop_by_process; then
        STOPPED=true
    fi

    # Check final status
    if $STOPPED; then
        # Double check the bot is really stopped
        sleep 1
        if is_bot_running; then
            print_error "Bot process still running after stop attempt!"
            BOT_PID=$(get_bot_pid)
            print_info "Bot PID: $BOT_PID"
            exit 1
        fi

        if [ "$QUIET" = false ]; then
            show_summary
        else
            print_success "Bot stopped"
        fi
        exit 0
    else
        print_warning "Bot does not appear to be running"
        print_info "Checking for any python main.py processes..."

        if is_bot_running; then
            print_warning "Found running process, attempting force stop..."
            if $FORCE || stop_by_process; then
                exit 0
            fi
        fi

        print_info "No bot processes found"
        exit 0
    fi
}

# Run main function with all arguments
main "$@"
