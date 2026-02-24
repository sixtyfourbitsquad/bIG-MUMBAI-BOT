import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.error import TelegramError
from db import Database

logger = logging.getLogger(__name__)

# Broadcast tuning for Render hobby / Telegram rate limits
BROADCAST_DELAY_PER_USER = 0.08   # seconds between each user
BROADCAST_BATCH_SIZE = 40        # users per batch
BROADCAST_BATCH_PAUSE = 2.0      # seconds pause between batches (yields to event loop, avoids timeout)

# Conversation states
WAITING_CHANNEL_LINK, WAITING_BUTTON_TEXT, WAITING_CAPTION, WAITING_IMAGE, \
WAITING_AUTO_MESSAGE, WAITING_INTERVAL, WAITING_BROADCAST, WAITING_BROADCAST_FILE, WAITING_FILE, WAITING_FILE_BUTTON_TEXT = range(10)


class AdminPanel:
    def __init__(self, db: Database, admin_ids: list):
        self.db = db
        self.admin_ids = admin_ids

    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in self.admin_ids

    async def admin_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show admin menu"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return

        keyboard = [
            [InlineKeyboardButton("📝 Edit Channel Link", callback_data="admin_edit_channel_link")],
            [InlineKeyboardButton("🔘 Edit Button Text", callback_data="admin_edit_button_text")],
            [InlineKeyboardButton("📄 Edit Caption", callback_data="admin_edit_caption")],
            [InlineKeyboardButton("🖼️ Upload / Change Image", callback_data="admin_edit_image")],
            [InlineKeyboardButton("📁 Upload File (APK/Images/Documents)", callback_data="admin_upload_file")],
            [InlineKeyboardButton("🔘 Edit File Button Text", callback_data="admin_edit_file_button_text")],
            [InlineKeyboardButton("💬 Edit Auto Message", callback_data="admin_edit_auto_message")],
            [InlineKeyboardButton("⏰ Set Interval Hours", callback_data="admin_edit_interval")],
            [InlineKeyboardButton("🔄 Toggle Auto Messages", callback_data="admin_toggle_auto")],
            [InlineKeyboardButton("📢 Broadcast Now", callback_data="admin_broadcast")],
            [InlineKeyboardButton("📊 Stats", callback_data="admin_stats")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        auto_status = "ON" if self.db.get_setting("auto_messages_enabled") == "1" else "OFF"
        text = f"👑 **Admin Panel**\n\nAuto Messages: {auto_status}"
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

    async def admin_callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin callback queries"""
        query = update.callback_query
        await query.answer()

        if not self.is_admin(query.from_user.id):
            await query.edit_message_text("❌ You are not authorized.")
            return

        callback_data = query.data

        if callback_data == "admin_edit_channel_link":
            current_link = self.db.get_setting("channel_link") or "Not set"
            await query.edit_message_text(
                "📝 **Edit Channel Link**\n\n"
                f"Current: `{current_link}`\n\n"
                "Please send the new channel invite link:\n\n"
                "• Public channel: `https://t.me/channelname` or `@channelname`\n"
                "• Private channel: `https://t.me/+invitecode` or `https://t.me/joinchat/invitecode`",
                parse_mode="Markdown"
            )
            return WAITING_CHANNEL_LINK

        elif callback_data == "admin_edit_button_text":
            await query.edit_message_text(
                "🔘 **Edit Button Text**\n\n"
                f"Current: {self.db.get_setting('button_text')}\n\n"
                "Please send the new button text:",
                parse_mode="Markdown"
            )
            return WAITING_BUTTON_TEXT

        elif callback_data == "admin_edit_caption":
            await query.edit_message_text(
                "📄 **Edit Caption**\n\n"
                f"Current: {self.db.get_setting('caption_text')}\n\n"
                "Please send the new caption text:",
                parse_mode="Markdown"
            )
            return WAITING_CAPTION

        elif callback_data == "admin_edit_image":
            await query.edit_message_text(
                "🖼️ **Upload / Change Image**\n\n"
                "Please send a photo to update the welcome image:",
                parse_mode="Markdown"
            )
            return WAITING_IMAGE

        elif callback_data == "admin_edit_auto_message":
            await query.edit_message_text(
                "💬 **Edit Auto Message**\n\n"
                f"Current: {self.db.get_setting('auto_message_text')}\n\n"
                "Please send the new auto message text:",
                parse_mode="Markdown"
            )
            return WAITING_AUTO_MESSAGE

        elif callback_data == "admin_edit_interval":
            await query.edit_message_text(
                "⏰ **Set Interval Hours**\n\n"
                f"Current: {self.db.get_setting('interval_hours')} hours\n\n"
                "Please send the number of hours (e.g., 8):",
                parse_mode="Markdown"
            )
            return WAITING_INTERVAL

        elif callback_data == "admin_toggle_auto":
            current = self.db.get_setting("auto_messages_enabled")
            new_value = "0" if current == "1" else "1"
            self.db.set_setting("auto_messages_enabled", new_value)
            status = "ON" if new_value == "1" else "OFF"
            await query.edit_message_text(f"✅ Auto messages turned {status}")
            return ConversationHandler.END

        elif callback_data == "admin_broadcast":
            await query.edit_message_text(
                "📢 **Broadcast Message**\n\n"
                "Send your broadcast content (text and/or photo with caption).\n\n"
                "In the next step you can optionally attach a file (document, video, audio, etc.).",
                parse_mode="Markdown"
            )
            return WAITING_BROADCAST

        elif callback_data == "admin_upload_file":
            await query.edit_message_text(
                "📁 **Upload File**\n\n"
                "Please send a file (APK, image, document, video, audio, etc.):\n\n"
                "Supported formats:\n"
                "• APK files\n"
                "• Images (JPG, PNG, etc.)\n"
                "• Documents (PDF, ZIP, etc.)\n"
                "• Videos\n"
                "• Audio files",
                parse_mode="Markdown"
            )
            return WAITING_FILE

        elif callback_data == "admin_edit_file_button_text":
            current_text = self.db.get_setting("file_button_text") or "📥 Download Files"
            await query.edit_message_text(
                "🔘 **Edit File Button Text**\n\n"
                f"Current: {current_text}\n\n"
                "Please send the new file button text:",
                parse_mode="Markdown"
            )
            return WAITING_FILE_BUTTON_TEXT

        elif callback_data == "admin_stats":
            stats = self.db.get_stats()
            text = (
                f"📊 **Bot Statistics**\n\n"
                f"Total Users: {stats['total_users']}\n"
                f"Active Users: {stats['active_users']}\n"
                f"Inactive Users: {stats['total_users'] - stats['active_users']}"
            )
            await query.edit_message_text(text, parse_mode="Markdown")
            return ConversationHandler.END

    async def handle_channel_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle channel link update"""
        try:
            raw_link = update.message.text.strip()
            logger.info(f"Received channel link: {raw_link}")
            
            # Normalize the link
            new_link = raw_link
            
            # If user sent @username, convert to https://t.me/username
            if new_link.startswith("@"):
                new_link = f"https://t.me/{new_link[1:]}"
            
            # Normalize protocol
            if new_link.startswith("t.me/"):
                new_link = f"https://{new_link}"
            elif new_link.startswith("http://t.me/"):
                new_link = new_link.replace("http://", "https://")
            elif not new_link.startswith("http"):
                # If it doesn't start with http or @, it might just be a channel name
                if "/" not in new_link and "+" not in new_link:
                    new_link = f"https://t.me/{new_link}"
            
            # Accept any link that starts with https://t.me/ or http://t.me/
            # This includes public channels, private channels with +, and joinchat links
            if not (new_link.startswith("https://t.me/") or new_link.startswith("http://t.me/")):
                await update.message.reply_text(
                    "❌ Invalid link format. Please send a valid Telegram link.\n\n"
                    "Examples:\n"
                    "• `https://t.me/channelname` (public)\n"
                    "• `https://t.me/+invitecode` (private)\n"
                    "• `https://t.me/joinchat/invitecode` (private)\n"
                    "• `@channelname`",
                    parse_mode="Markdown"
                )
                logger.warning(f"Invalid link format rejected: {raw_link} -> {new_link}")
                return WAITING_CHANNEL_LINK
            
            # Ensure https:// for all links
            if new_link.startswith("http://"):
                new_link = new_link.replace("http://", "https://", 1)
            
            # Save the link
            logger.info(f"Saving channel link: {new_link}")
            self.db.set_setting("channel_link", new_link)
            
            # Verify it was saved
            saved_link = self.db.get_setting("channel_link")
            logger.info(f"Verified saved link: {saved_link}")
            
            await update.message.reply_text(
                f"✅ Channel link updated successfully!\n\n"
                f"New link: `{saved_link}`",
                parse_mode="Markdown"
            )
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error handling channel link: {e}", exc_info=True)
            await update.message.reply_text(
                f"❌ An error occurred: {str(e)}\n\n"
                "Please try again or contact support."
            )
            return WAITING_CHANNEL_LINK

    async def handle_button_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button text update"""
        new_text = update.message.text.strip()
        self.db.set_setting("button_text", new_text)
        await update.message.reply_text(f"✅ Button text updated to: {new_text}")
        return ConversationHandler.END

    async def handle_caption(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle caption update"""
        new_caption = update.message.text
        self.db.set_setting("caption_text", new_caption)
        await update.message.reply_text("✅ Caption updated successfully!")
        return ConversationHandler.END

    async def handle_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle image update"""
        if not update.message.photo:
            await update.message.reply_text("❌ Please send a photo.")
            return WAITING_IMAGE

        # Get the largest photo
        photo = update.message.photo[-1]
        file_id = photo.file_id
        self.db.set_setting("image_file_id", file_id)
        await update.message.reply_text("✅ Image updated successfully!")
        return ConversationHandler.END

    async def handle_auto_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle auto message update"""
        new_message = update.message.text
        self.db.set_setting("auto_message_text", new_message)
        await update.message.reply_text("✅ Auto message text updated successfully!")
        return ConversationHandler.END

    async def handle_interval(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle interval update"""
        try:
            hours = int(update.message.text.strip())
            if hours < 1:
                raise ValueError("Hours must be at least 1")
            self.db.set_setting("interval_hours", str(hours))
            await update.message.reply_text(f"✅ Interval updated to {hours} hours")
        except ValueError as e:
            await update.message.reply_text(f"❌ Invalid input: {e}. Please send a number.")
            return WAITING_INTERVAL
        return ConversationHandler.END

    async def handle_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle broadcast step 1: collect text and/or image."""
        message_text = (update.message.text or update.message.caption or "").strip()
        photo_file_id = None
        if update.message.photo:
            photo_file_id = update.message.photo[-1].file_id

        if not message_text and not photo_file_id:
            await update.message.reply_text(
                "❌ Please send at least text or a photo (with optional caption)."
            )
            return WAITING_BROADCAST

        context.user_data["broadcast_text"] = message_text or ""
        context.user_data["broadcast_photo_id"] = photo_file_id

        await update.message.reply_text(
            "✅ Got it. Now you can **attach a file** (document, APK, video, audio, etc.) "
            "or type /skip to send without a file.",
            parse_mode="Markdown"
        )
        return WAITING_BROADCAST_FILE

    async def handle_broadcast_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle broadcast step 2: optional file or /skip, then start broadcast in background."""
        # Check for /skip
        if update.message.text and update.message.text.strip().lower() == "/skip":
            context.user_data["broadcast_file_id"] = None
            context.user_data["broadcast_file_type"] = None
            context.user_data["broadcast_file_caption"] = ""
        else:
            file_caption = (update.message.caption or "").strip()
            if update.message.document:
                context.user_data["broadcast_file_id"] = update.message.document.file_id
                context.user_data["broadcast_file_type"] = "document"
                context.user_data["broadcast_file_caption"] = file_caption
            elif update.message.photo:
                context.user_data["broadcast_file_id"] = update.message.photo[-1].file_id
                context.user_data["broadcast_file_type"] = "photo"
                context.user_data["broadcast_file_caption"] = file_caption
            elif update.message.video:
                context.user_data["broadcast_file_id"] = update.message.video.file_id
                context.user_data["broadcast_file_type"] = "video"
                context.user_data["broadcast_file_caption"] = file_caption
            elif update.message.audio:
                context.user_data["broadcast_file_id"] = update.message.audio.file_id
                context.user_data["broadcast_file_type"] = "audio"
                context.user_data["broadcast_file_caption"] = file_caption
            elif update.message.voice:
                context.user_data["broadcast_file_id"] = update.message.voice.file_id
                context.user_data["broadcast_file_type"] = "audio"
                context.user_data["broadcast_file_caption"] = file_caption
            elif update.message.video_note:
                context.user_data["broadcast_file_id"] = update.message.video_note.file_id
                context.user_data["broadcast_file_type"] = "video"
                context.user_data["broadcast_file_caption"] = file_caption
            else:
                await update.message.reply_text(
                    "❌ Please send a file (document, photo, video, audio, etc.) or type /skip."
                )
                return WAITING_BROADCAST_FILE

        # Snapshot payload for background task (no reference to context)
        payload = {
            "text": context.user_data.get("broadcast_text", ""),
            "photo_id": context.user_data.get("broadcast_photo_id"),
            "file_id": context.user_data.get("broadcast_file_id"),
            "file_type": context.user_data.get("broadcast_file_type"),
            "file_caption": context.user_data.get("broadcast_file_caption", ""),
        }
        users = self.db.get_active_users()
        status_msg = await update.message.reply_text(
            f"📢 Broadcasting to {len(users)} users in background (optimized for Render). You'll get a summary when done."
        )
        chat_id = update.effective_chat.id
        message_id = status_msg.message_id
        bot = context.bot
        db = self.db

        async def run_broadcast():
            await self._broadcast_to_users(bot, db, payload, chat_id, message_id)

        asyncio.create_task(run_broadcast())
        return ConversationHandler.END

    async def _broadcast_to_users(
        self,
        bot: Bot,
        db: Database,
        payload: dict,
        status_chat_id: int,
        status_message_id: int,
    ):
        """Send broadcast to all active users in batches (Render-friendly, avoids timeouts)."""
        users = db.get_active_users()
        text = payload.get("text", "")
        photo_id = payload.get("photo_id")
        b_file_id = payload.get("file_id")
        b_file_type = payload.get("file_type")
        b_file_caption = payload.get("file_caption", "")

        success_count = 0
        failed_count = 0
        total = len(users)

        def send_to_user(user):
            async def _send():
                nonlocal success_count, failed_count
                try:
                    if photo_id:
                        await bot.send_photo(
                            chat_id=user["user_id"],
                            photo=photo_id,
                            caption=text if text else None,
                        )
                    elif text:
                        await bot.send_message(chat_id=user["user_id"], text=text)
                    await asyncio.sleep(0.02)
                    if b_file_id:
                        if b_file_type == "photo":
                            await bot.send_photo(
                                chat_id=user["user_id"],
                                photo=b_file_id,
                                caption=b_file_caption or None,
                            )
                        elif b_file_type == "video":
                            await bot.send_video(
                                chat_id=user["user_id"],
                                video=b_file_id,
                                caption=b_file_caption or None,
                            )
                        elif b_file_type == "audio":
                            await bot.send_audio(
                                chat_id=user["user_id"],
                                audio=b_file_id,
                                caption=b_file_caption or None,
                            )
                        else:
                            await bot.send_document(
                                chat_id=user["user_id"],
                                document=b_file_id,
                                caption=b_file_caption or None,
                            )
                        await asyncio.sleep(0.02)
                    success_count += 1
                except TelegramError as e:
                    logger.warning(f"Broadcast failed to {user['user_id']}: {e}")
                    if "blocked" in str(e).lower() or "chat not found" in str(e).lower():
                        db.mark_user_inactive(user["user_id"])
                    failed_count += 1

            return _send

        for i, user in enumerate(users):
            await send_to_user(user)()
            await asyncio.sleep(BROADCAST_DELAY_PER_USER)
            # Batch pause: yield to event loop, avoid Render timeout and rate limits
            if (i + 1) % BROADCAST_BATCH_SIZE == 0:
                await asyncio.sleep(BROADCAST_BATCH_PAUSE)

        try:
            await bot.edit_message_text(
                chat_id=status_chat_id,
                message_id=status_message_id,
                text=f"📢 Broadcast completed!\n✅ Success: {success_count}\n❌ Failed: {failed_count}",
            )
        except Exception as e:
            logger.warning(f"Could not edit broadcast status message: {e}")

    async def handle_file_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle file upload (APK, images, documents, etc.)"""
        try:
            file_id = None
            file_type = None
            file_name = None
            
            # Check for different file types
            if update.message.document:
                file_id = update.message.document.file_id
                file_type = "document"
                file_name = update.message.document.file_name or "file"
            elif update.message.photo:
                # Get the largest photo
                file_id = update.message.photo[-1].file_id
                file_type = "photo"
                file_name = "photo.jpg"
            elif update.message.video:
                file_id = update.message.video.file_id
                file_type = "video"
                file_name = update.message.video.file_name or "video.mp4"
            elif update.message.audio:
                file_id = update.message.audio.file_id
                file_type = "audio"
                file_name = update.message.audio.file_name or "audio.mp3"
            elif update.message.voice:
                file_id = update.message.voice.file_id
                file_type = "audio"
                file_name = "voice.ogg"
            elif update.message.video_note:
                file_id = update.message.video_note.file_id
                file_type = "video"
                file_name = "video_note.mp4"
            else:
                await update.message.reply_text("❌ Please send a file (document, photo, video, or audio).")
                return WAITING_FILE
            
            # Save file information
            self.db.set_setting("file_id", file_id)
            self.db.set_setting("file_type", file_type)
            if file_name:
                self.db.set_setting("file_name", file_name)
            
            # Get or set default caption
            file_caption = update.message.caption or f"📥 {file_name}"
            self.db.set_setting("file_caption", file_caption)
            
            await update.message.reply_text(
                f"✅ File uploaded successfully!\n\n"
                f"Type: {file_type}\n"
                f"Name: {file_name}\n"
                f"Caption: {file_caption}\n\n"
                f"Users can now download this file by clicking the download button."
            )
            logger.info(f"File uploaded: {file_type} - {file_name}")
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error handling file upload: {e}", exc_info=True)
            await update.message.reply_text(f"❌ An error occurred: {str(e)}")
            return WAITING_FILE

    async def handle_file_button_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle file button text update"""
        new_text = update.message.text.strip()
        self.db.set_setting("file_button_text", new_text)
        await update.message.reply_text(f"✅ File button text updated to: {new_text}")
        return ConversationHandler.END

    def get_conversation_handler(self):
        """Get conversation handler for admin commands"""
        return ConversationHandler(
            entry_points=[CallbackQueryHandler(self.admin_callback_handler, pattern="^admin_")],
            states={
                WAITING_CHANNEL_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_channel_link)],
                WAITING_BUTTON_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_button_text)],
                WAITING_CAPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_caption)],
                WAITING_IMAGE: [MessageHandler(filters.PHOTO, self.handle_image)],
                WAITING_FILE: [MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.VOICE | filters.VIDEO_NOTE, self.handle_file_upload)],
                WAITING_FILE_BUTTON_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_file_button_text)],
                WAITING_AUTO_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_auto_message)],
                WAITING_INTERVAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_interval)],
                WAITING_BROADCAST: [MessageHandler(filters.ALL, self.handle_broadcast)],
                WAITING_BROADCAST_FILE: [MessageHandler(filters.ALL, self.handle_broadcast_file)],
            },
            fallbacks=[CallbackQueryHandler(self.admin_callback_handler)],
            per_chat=True,
            per_user=True,
        )

