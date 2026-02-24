# Big Mumbai Telegram Bot — How It Works & What It Can Do

**Report type:** Working capabilities and operation (ChatGPT-style)  
**Project:** Big Mumbai TG BOT (Feb 24, 2026)  
**Platform:** Telegram · Python · python-telegram-bot

---

## What Is This Bot?

The **Big Mumbai** bot is a Telegram bot that helps you grow a channel and keep users engaged. When someone starts the bot, they see a welcome (image, text, and buttons). One button sends them to your Telegram channel; another lets them download a file you set (e.g. APK or PDF). Admins can change all of this from Telegram—no code edits—and can send broadcasts or schedule automatic reminder messages.

---

## How the Bot Works (High-Level Flow)

1. **User sends `/start`** → Bot saves them in the database and sends the welcome (image + caption + two buttons).
2. **User taps “Join channel”** → Opens the channel link in Telegram (link is set by admin).
3. **User taps “Download file”** → Bot sends the file stored in settings (document/photo/video/audio, etc.).
4. **Admin sends `/admin`** → If the user is in `ADMIN_IDS`, they see an inline admin panel. Each option leads to a short “conversation”: bot asks for input, admin sends it, bot saves it and confirms.
5. **Background scheduler** → Every N hours (N set in admin), the bot sends the “auto message” text to all *active* users. If a send fails (e.g. user blocked the bot), that user is marked inactive and skipped in future broadcasts and auto-messages.

So in short: **user flow** is start → welcome → channel/file; **admin flow** is /admin → menu → edit things or broadcast; **automation** is the recurring auto-message and inactive-user cleanup.

---

## 1. User-Facing Capabilities (What Users Can Do)

### 1.1 Start and Welcome

| What | How it works |
|------|----------------|
| **`/start`** | Trigger for new and returning users. The bot registers the user in the database (user_id, username, first_name) and then sends the welcome content. |
| **Welcome content** | Can show a **photo** (stored by Telegram `file_id`) and a **caption**. If no image is set or sending the photo fails, the bot sends the caption as plain text with the same buttons. |
| **“Join channel” button** | Inline button with a label you set (e.g. “Join Big Mumbai Channel”). Tapping it opens the configured channel link (public like `https://t.me/channel` or private invite like `https://t.me/+xxx`). |
| **“Download file” button** | Second inline button (e.g. “📥 Download Files”). When pressed, the bot sends the file currently set in admin (document, photo, video, audio, voice, or video note) with its caption. |

So from a user’s perspective: they only use **Start** and two **buttons**—no other commands.

### 1.2 File Delivery

- **Types supported:** Document (APK, PDF, etc.), photo, video, audio, voice, video note.
- **Behavior:** On “Download file” the bot looks up the stored `file_id` and `file_type` in the database and sends the file with the configured caption.
- **If no file is set:** The user gets a “No file available” message.

---

## 2. Admin Capabilities (What Admins Can Do)

Access: **`/admin`** — only users whose Telegram user ID is in `ADMIN_IDS` (in `.env`) can use it. Others get “You are not authorized.”

### 2.1 Admin Panel Options (What Each Does)

| Option | What it does | How it works |
|--------|----------------|--------------|
| **📝 Edit Channel Link** | Set/update the channel URL. | Bot asks for the new link. Accepts `https://t.me/...`, `@channel`, `t.me/...`; normalizes to `https://t.me/...`. Supports public and private invite links. Saved in DB. |
| **🔘 Edit Button Text** | Change the “Join channel” button label. | Bot shows current text, asks for new text. You send one message; it’s saved and used on the next welcome. |
| **📄 Edit Caption** | Change the welcome message (below image or as main text). | Bot shows current caption, asks for new one. Your next message is stored as the new caption. |
| **🖼️ Upload / Change Image** | Set the welcome image. | Bot asks for a photo. You send one; its `file_id` is stored. Next welcome uses this image (or falls back to text if send fails). |
| **📁 Upload File** | Set the file users get via “Download file”. | You send a document/photo/video/audio/voice/video note. Bot stores `file_id`, `file_type`, and optional caption. |
| **🔘 Edit File Button Text** | Change the “Download file” button label. | Same pattern as “Edit Button Text” but for the file button. |
| **💬 Edit Auto Message** | Set the text used for scheduled auto-messages. | Bot shows current auto message, asks for new text. Stored and used by the scheduler. |
| **⏰ Set Interval Hours** | Set how often (in hours) the scheduler sends the auto-message. | You send a number (e.g. 8). Stored; scheduler waits this many hours between each batch. |
| **🔄 Toggle Auto Messages** | Turn scheduled auto-messages ON or OFF. | One tap; flips a setting in DB (1/0). Scheduler checks this before sending. |
| **📢 Broadcast Now** | Send a one-off message to all active users. | Bot asks for the message. You send text and/or photo with caption. Bot sends to each active user with a small delay; failed sends mark user inactive. |
| **📊 Stats** | View counts. | Shows total users, active users, and (by subtraction) inactive users. |

So admins never touch code for routine updates—everything is driven by the Telegram admin panel and stored in the database.

### 2.2 How Broadcasts Behave

- **Recipients:** Every user with `is_active = 1`.
- **Content:** Text only, or photo + caption.
- **Rate limiting:** Short delay (e.g. 0.05 s) between each send to reduce Telegram rate-limit risk.
- **Failures:** If sending fails (e.g. “blocked” or “chat not found”), that user is marked **inactive** and excluded from future broadcasts and auto-messages.

---

## 3. Automated / Background Behavior (How the Bot Keeps Working)

### 3.1 Scheduler (Auto-Messages)

- **What it does:** Sends the “Edit Auto Message” text to all active users on a timer.
- **How it works:**
  - A background loop runs: wait N hours (N = “Set Interval Hours”) → send the auto-message to all active users → wait N hours again → repeat.
  - Before sending, it checks the “Toggle Auto Messages” setting; if OFF, it skips sending and just waits for the next cycle.
  - It uses a small delay between each user to avoid rate limits.
  - If a send fails because the user blocked the bot or chat not found, that user is marked inactive so they are not bothered again and are excluded from future broadcasts and auto-messages.

So the “working” of the bot here is: **timer → load active users → send one text message to each → mark failures inactive → sleep N hours → repeat.**

### 3.2 User and State Management

- **Registration:** On `/start`, the user is added or updated in the `users` table (user_id, username, first_name, is_active=1).
- **Active vs inactive:** Users are marked inactive when a send fails (blocked/deleted). Only **active** users get broadcasts and auto-messages.
- **Stats:** “Stats” in admin reads from the DB: total users and active users (inactive = total − active).

---

## 4. Technical Overview (How the Code Is Structured)

### 4.1 Stack

- **Language:** Python  
- **Telegram:** `python-telegram-bot` (async)  
- **Storage:** SQLite (`bot_database.db`)  
- **Config:** `.env` with `BOT_TOKEN` and `ADMIN_IDS` (comma-separated user IDs)

### 4.2 Main Components and How They Interact

- **`bot.py`** — Entry point. Builds the Telegram `Application`, registers handlers for `/start`, `/admin`, and the “download file” callback. Connects the admin conversation handler and the scheduler. Sets up an explicit event loop for compatibility (e.g. Windows / Python 3.14).
- **`admin.py`** — `AdminPanel` class. Handles `/admin` (shows menu), all admin inline button callbacks, and the conversation steps (waiting for channel link, button text, caption, image, file, etc.). Each step has a handler that validates/saves input and either moves to the next step or ends the conversation.
- **`db.py`** — `Database` class. SQLite: creates/uses `users` and `settings` tables. Methods: add_user, get_active_users, mark_user_inactive, get_setting, set_setting, get_stats. Used by bot, admin, and scheduler.
- **`scheduler.py`** — `MessageScheduler`. Holds a reference to the DB and the bot. Runs `scheduler_loop()` as an asyncio task: sleep N hours → `send_auto_messages()` (if enabled) → repeat. `send_auto_messages()` loads active users and sends the auto-message text to each, marking failures inactive.
- **`config.py`** — Loads `BOT_TOKEN` and `ADMIN_IDS` from `.env`; raises if missing.

So the “working” at the code level is: **Telegram updates → handlers in bot.py and admin.py → DB reads/writes in db.py → scheduler task in scheduler.py sends messages and updates active state.**

### 4.3 Database Schema (What Is Stored)

- **`users`:** `user_id` (PK), `username`, `first_name`, `is_active`, `created_at`, `last_message_sent`.
- **`settings`:** Key-value store. Keys include: channel_link, button_text, file_button_text, caption_text, image_file_id, file_id, file_type, file_name, file_caption, auto_message_text, interval_hours, auto_messages_enabled. Values are strings (or NULL where applicable).

### 4.4 Reliability and Edge Cases

- **Errors:** A global error handler in `bot.py` logs exceptions so the bot doesn’t crash on unexpected errors.
- **Photo fallback:** If sending the welcome photo fails (e.g. file_id invalid), the bot sends the caption as text with the same buttons so the user still gets the message and buttons.
- **Event loop:** Explicit asyncio event loop setup in `main()` for compatibility on Windows and with Python 3.14.

---

## 5. Security and Access Control

- **Admin-only:** Every `/admin` entry and admin callback checks that `update.effective_user.id` (or `query.from_user.id`) is in `ADMIN_IDS`. Non-admins get an “unauthorized” response.
- **Secrets:** Token and admin IDs come from `.env`, not from code.

---

## 6. Summary Table (Capabilities at a Glance)

| Area | What the bot can do |
|------|----------------------|
| **User** | `/start` → welcome (image + caption), “Join channel” button, “Download file” button. |
| **Admin** | Edit channel link, button texts, caption, image, file + file button text, auto-message text and interval, toggle auto-messages, broadcast now, view stats—all via Telegram. |
| **Automation** | Scheduled auto-messages at configurable interval; automatic marking of inactive users on send failure. |
| **Data** | SQLite: users (with active flag), key-value settings, stats (total/active users). |

---

## 7. Conclusion

The Big Mumbai bot:

1. **For users:** One entry point (`/start`) with a customizable welcome, channel link, and file download—all via two buttons.
2. **For admins:** Full control over content and behavior through an inline admin panel, with no code changes for routine updates.
3. **For engagement:** Optional scheduled reminders and on-demand broadcasts, with automatic cleanup of blocked/inactive users.

It is suitable for **channel growth**, **file distribution** (e.g. APK/docs), and **repeated engagement** with a stored user base, all manageable through the Telegram admin interface. This report explained both its **working capabilities** (what it can do) and **how it works** (flow, components, and logic).

---

*Report generated to explain the working capabilities and operation of the Big Mumbai TG BOT project.*
