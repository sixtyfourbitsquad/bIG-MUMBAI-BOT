#!/bin/bash

# Telegram Bot VPS Setup Script
# Run this script on your VPS to set up the bot

set -e

echo "=========================================="
echo "Telegram Bot VPS Setup Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Update system
echo -e "${YELLOW}[1/8] Updating system packages...${NC}"
apt update
apt upgrade -y

# Install required packages
echo -e "${YELLOW}[2/8] Installing Python and dependencies...${NC}"
apt install -y python3 python3-pip python3-venv git

# Create bot directory
BOT_DIR="/root/telegram-bot"
echo -e "${YELLOW}[3/8] Creating bot directory at $BOT_DIR...${NC}"
mkdir -p "$BOT_DIR"
cd "$BOT_DIR"

# Create virtual environment
echo -e "${YELLOW}[4/8] Creating Python virtual environment...${NC}"
python3 -m venv venv

# Activate virtual environment and install dependencies
echo -e "${YELLOW}[5/8] Installing Python packages...${NC}"
source venv/bin/activate
pip install --upgrade pip

# Check if requirements.txt exists
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo -e "${YELLOW}requirements.txt not found. Installing default packages...${NC}"
    pip install python-telegram-bot==21.0.1 python-dotenv==1.0.0
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[6/8] Creating .env file...${NC}"
    cat > .env << EOF
# Telegram Bot Configuration
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789
EOF
    echo -e "${GREEN}.env file created. Please edit it with your bot token and admin ID.${NC}"
else
    echo -e "${GREEN}[6/8] .env file already exists.${NC}"
fi

# Create systemd service file
echo -e "${YELLOW}[7/8] Creating systemd service...${NC}"
cat > /etc/systemd/system/telegram-bot.service << EOF
[Unit]
Description=Telegram Bot Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$BOT_DIR
Environment="PATH=$BOT_DIR/venv/bin"
ExecStart=$BOT_DIR/venv/bin/python3 $BOT_DIR/bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
echo -e "${YELLOW}[8/8] Configuring systemd service...${NC}"
systemctl daemon-reload
systemctl enable telegram-bot.service

echo ""
echo -e "${GREEN}=========================================="
echo "Setup Complete!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Edit .env file: nano $BOT_DIR/.env"
echo "   - Add your BOT_TOKEN from @BotFather"
echo "   - Add your ADMIN_IDS (get from @userinfobot)"
echo ""
echo "2. Transfer your bot files to: $BOT_DIR"
echo "   - bot.py"
echo "   - admin.py"
echo "   - db.py"
echo "   - config.py"
echo "   - scheduler.py"
echo "   - requirements.txt"
echo ""
echo "3. Start the bot:"
echo "   sudo systemctl start telegram-bot.service"
echo ""
echo "4. Check status:"
echo "   sudo systemctl status telegram-bot.service"
echo ""
echo "5. View logs:"
echo "   sudo journalctl -u telegram-bot.service -f"
echo ""
echo -e "${YELLOW}Note: The bot will not start until you:${NC}"
echo "  - Edit .env with correct values"
echo "  - Transfer all bot files to $BOT_DIR"
echo ""

