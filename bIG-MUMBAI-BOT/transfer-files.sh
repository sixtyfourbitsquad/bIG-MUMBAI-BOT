#!/bin/bash

# File Transfer Script for Windows (Git Bash or WSL)
# This script helps transfer bot files to your VPS

# Configuration
VPS_IP="your_vps_ip_here"
VPS_USER="root"
BOT_DIR="~/telegram-bot"
LOCAL_DIR="C:/Work/tg bot/BIG MUMABI"

echo "=========================================="
echo "Telegram Bot File Transfer Script"
echo "=========================================="
echo ""

# Check if VPS_IP is set
if [ "$VPS_IP" == "your_vps_ip_here" ]; then
    echo "Please edit this script and set VPS_IP to your VPS IP address"
    exit 1
fi

echo "This will transfer files from:"
echo "  Local: $LOCAL_DIR"
echo "  Remote: $VPS_USER@$VPS_IP:$BOT_DIR"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Transfer cancelled."
    exit 1
fi

# Transfer files
echo "Transferring files..."
scp -r "$LOCAL_DIR"/* "$VPS_USER@$VPS_IP:$BOT_DIR/"

echo ""
echo "Files transferred successfully!"
echo ""
echo "Next steps on VPS:"
echo "1. SSH to your VPS: ssh $VPS_USER@$VPS_IP"
echo "2. Edit .env file: nano $BOT_DIR/.env"
echo "3. Start the bot: sudo systemctl start telegram-bot.service"

