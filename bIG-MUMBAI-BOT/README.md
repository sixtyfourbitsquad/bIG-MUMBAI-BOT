# Big Mumbai Channel Bot

A complete Telegram bot for managing a channel join bot with scheduled messaging capabilities.

## Features

- Welcome message with customizable photo, caption, and join button
- User tracking in SQLite database
- Automatic scheduled messages (configurable interval)
- Admin panel with inline keyboard interface
- Broadcast messages to all users
- Automatic handling of blocked users
- Statistics dashboard

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your bot token and admin IDs:

```
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321
```

**How to get your Bot Token:**
1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the instructions
3. Copy the token provided by BotFather

**How to get your Admin ID:**
1. Open Telegram and search for [@userinfobot](https://t.me/userinfobot)
2. Start the bot and it will show your user ID
3. Add multiple admin IDs separated by commas (no spaces)

### 3. Run the Bot

```bash
python bot.py
```

The bot will start and begin processing commands.

## Deployment

### Deploy to Render

1. **Create a new Web Service** on Render
2. **Connect your repository** or deploy from a Git URL
3. **Build Command:**
   ```
   pip install -r requirements.txt
   ```
4. **Start Command:**
   ```
   python bot.py
   ```
5. **Environment Variables:**
   - Add `BOT_TOKEN` and `ADMIN_IDS` in the Environment tab
6. **Instance Type:** Free tier is sufficient for small to medium bots

### Deploy to Railway

1. **Create a new project** on Railway
2. **Add a new service** from GitHub/GitLab repository
3. **Environment Variables:**
   - Go to Variables tab
   - Add `BOT_TOKEN` and `ADMIN_IDS`
4. **No Procfile needed** - Railway auto-detects Python projects
5. **Deploy** - Railway will automatically install dependencies and run `python bot.py`

### Optional: Using Procfile

If you prefer to use a Procfile, create one:

```
worker: python bot.py
```

Then deploy as a "Worker" type service on Railway.

## Admin Commands

### `/admin`
Opens the admin panel with the following options:

- **📝 Edit Channel Link** - Update the channel invite link
- **🔘 Edit Button Text** - Change the button text
- **📄 Edit Caption** - Modify the welcome message caption
- **🖼️ Upload / Change Image** - Upload or change the welcome photo
- **💬 Edit Auto Message** - Set the automatic message text
- **⏰ Set Interval Hours** - Configure how often auto messages are sent (default: 8 hours)
- **🔄 Toggle Auto Messages** - Turn automatic messages ON/OFF
- **📢 Broadcast Now** - Send a message to all users immediately
- **📊 Stats** - View total and active user statistics

## Project Structure

```
.
├── bot.py              # Main bot file with /start command
├── admin.py            # Admin panel and command handlers
├── db.py               # Database operations (SQLite)
├── scheduler.py        # Scheduled messaging logic
├── config.py           # Configuration and environment variables
├── requirements.txt    # Python dependencies
├── .env.example        # Example environment file
├── README.md           # This file
└── bot_database.db     # SQLite database (created automatically)
```

## Default Settings

- **Interval Hours:** 8 hours
- **Auto Messages:** Enabled by default
- **Channel Link:** https://t.me/bigmumbaiofficial (can be changed via admin panel)

## Notes

- The bot automatically marks users as inactive if they block the bot
- Images are stored as file IDs to avoid re-uploading
- Scheduled messages respect Telegram rate limits
- All admin functions require authentication via ADMIN_IDS

## Troubleshooting

**Bot not responding:**
- Check that BOT_TOKEN is correct in .env
- Ensure the bot is not stopped/deleted in BotFather

**Admin commands not working:**
- Verify your user ID is in ADMIN_IDS
- Check ADMIN_IDS format (comma-separated, no spaces)

**Database errors:**
- Ensure the bot has write permissions in the project directory
- Delete `bot_database.db` to reset (will lose all data)

**Scheduled messages not sending:**
- Check if auto messages are enabled in admin panel
- Verify the interval is set correctly
- Check logs for error messages

## License

This project is provided as-is for use with Telegram bots.

