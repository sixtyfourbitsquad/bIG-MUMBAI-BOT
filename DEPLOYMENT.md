# VPS Deployment Guide

Complete guide to deploy the Telegram bot on a VPS (Ubuntu/Debian).

## Prerequisites

- A VPS with Ubuntu 20.04+ or Debian 11+
- SSH access to your VPS
- Your bot token from @BotFather
- Your admin Telegram user ID

## Step 1: Connect to Your VPS

```bash
ssh root@your_vps_ip
# or
ssh username@your_vps_ip
```

## Step 2: Update System

```bash
sudo apt update
sudo apt upgrade -y
```

## Step 3: Install Python and Required Tools

```bash
# Install Python 3.10+ and pip
sudo apt install python3 python3-pip python3-venv git -y

# Verify installation
python3 --version
pip3 --version
```

## Step 4: Create Bot Directory

```bash
# Create directory for the bot
mkdir -p ~/telegram-bot
cd ~/telegram-bot
```

## Step 5: Transfer Files to VPS

### Option A: Using SCP (from your local machine)

```bash
# From your local machine, navigate to the bot directory
cd "C:\Work\tg bot\BIG MUMABI"

# Transfer all files
scp -r * root@your_vps_ip:~/telegram-bot/
```

### Option B: Using Git (Recommended)

```bash
# On VPS, clone your repository
cd ~/telegram-bot
git clone https://github.com/yourusername/your-repo.git .
# Or if you have a private repo, use SSH key
```

### Option C: Using SFTP Client

Use FileZilla, WinSCP, or similar to transfer files via SFTP.

## Step 6: Set Up Python Virtual Environment

```bash
cd ~/telegram-bot

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 7: Create .env File

```bash
# Create .env file
nano .env
```

Add the following content:

```env
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789
```

**Important:**
- Replace `your_bot_token_here` with your actual bot token from @BotFather
- Replace `123456789` with your Telegram user ID (get it from @userinfobot)
- For multiple admins: `ADMIN_IDS=123456789,987654321` (comma-separated, no spaces)

Save and exit (Ctrl+X, then Y, then Enter).

## Step 8: Test the Bot

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Test run
python3 bot.py
```

If it works, press Ctrl+C to stop. Now let's set it up as a service.

## Step 9: Create Systemd Service

Create a systemd service file to run the bot automatically:

```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

Add the following content:

```ini
[Unit]
Description=Telegram Bot Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/telegram-bot
Environment="PATH=/root/telegram-bot/venv/bin"
ExecStart=/root/telegram-bot/venv/bin/python3 /root/telegram-bot/bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Note:** Adjust paths if you're using a different user or directory.

Save and exit.

## Step 10: Enable and Start the Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable telegram-bot.service

# Start the service
sudo systemctl start telegram-bot.service

# Check status
sudo systemctl status telegram-bot.service
```

## Step 11: Monitor the Bot

### View logs in real-time:
```bash
sudo journalctl -u telegram-bot.service -f
```

### View recent logs:
```bash
sudo journalctl -u telegram-bot.service -n 50
```

### Restart the bot:
```bash
sudo systemctl restart telegram-bot.service
```

### Stop the bot:
```bash
sudo systemctl stop telegram-bot.service
```

## Step 12: Firewall Configuration (if needed)

If your VPS has a firewall, make sure it's configured:

```bash
# Check firewall status
sudo ufw status

# If firewall is active, allow SSH (if not already allowed)
sudo ufw allow 22/tcp
```

The bot doesn't need any open ports as it uses Telegram's API.

## Troubleshooting

### Bot not starting:
```bash
# Check logs
sudo journalctl -u telegram-bot.service -n 100

# Check if .env file exists and has correct values
cat ~/telegram-bot/.env

# Test manually
cd ~/telegram-bot
source venv/bin/activate
python3 bot.py
```

### Permission errors:
```bash
# Make sure files are readable
chmod +r ~/telegram-bot/*.py
chmod +r ~/telegram-bot/.env
```

### Database errors:
```bash
# Check database file permissions
ls -la ~/telegram-bot/bot_database.db
chmod 666 ~/telegram-bot/bot_database.db
```

### Service won't start:
```bash
# Check service status
sudo systemctl status telegram-bot.service

# Check if Python path is correct
which python3
# Update service file with correct path
```

## Updating the Bot

When you need to update the bot:

```bash
# Stop the service
sudo systemctl stop telegram-bot.service

# Update files (via git, scp, or sftp)
cd ~/telegram-bot
# ... update files ...

# Restart the service
sudo systemctl start telegram-bot.service

# Check status
sudo systemctl status telegram-bot.service
```

## Backup

Regular backups are recommended:

```bash
# Backup database
cp ~/telegram-bot/bot_database.db ~/telegram-bot/bot_database.db.backup

# Or create a backup script
nano ~/backup-bot.sh
```

Add to backup script:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp /root/telegram-bot/bot_database.db /root/backups/bot_database_$DATE.db
```

Make it executable:
```bash
chmod +x ~/backup-bot.sh
```

## Security Tips

1. **Keep .env file secure:**
   ```bash
   chmod 600 ~/telegram-bot/.env
   ```

2. **Keep system updated:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

3. **Use SSH keys instead of passwords**

4. **Regular backups of database**

## Quick Reference Commands

```bash
# Start bot
sudo systemctl start telegram-bot.service

# Stop bot
sudo systemctl stop telegram-bot.service

# Restart bot
sudo systemctl restart telegram-bot.service

# View logs
sudo journalctl -u telegram-bot.service -f

# Check status
sudo systemctl status telegram-bot.service

# Enable on boot
sudo systemctl enable telegram-bot.service

# Disable on boot
sudo systemctl disable telegram-bot.service
```

## Support

If you encounter issues:
1. Check logs: `sudo journalctl -u telegram-bot.service -n 100`
2. Verify .env file has correct values
3. Test manually: `python3 bot.py`
4. Check Python version: `python3 --version` (should be 3.10+)

