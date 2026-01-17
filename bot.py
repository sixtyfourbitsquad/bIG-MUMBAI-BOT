import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError

from config import BOT_TOKEN, ADMIN_IDS
from db import Database
from admin import AdminPanel
from scheduler import MessageScheduler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize components
db = Database()
admin_panel = AdminPanel(db, ADMIN_IDS)
scheduler = None  # Will be initialized after bot is created


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    
    try:
        # Add user to database
        db.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name
        )
        
        # Get settings
        channel_link = db.get_setting("channel_link")
        button_text = db.get_setting("button_text") or "Join Big Mumbai Channel"
        file_button_text = db.get_setting("file_button_text") or "📥 Download Files"
        caption_text = db.get_setting("caption_text") or "Welcome to Big Mumbai Official!"
        image_file_id = db.get_setting("image_file_id")
        
        # Create inline buttons - channel link and file download
        keyboard = [
            [InlineKeyboardButton(button_text, url=channel_link)],
            [InlineKeyboardButton(file_button_text, callback_data="download_file")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send photo if available, otherwise send text
        if image_file_id:
            try:
                await update.message.reply_photo(
                    photo=image_file_id,
                    caption=caption_text,
                    reply_markup=reply_markup
                )
            except TelegramError as e:
                logger.warning(f"Failed to send photo, falling back to text: {e}")
                await update.message.reply_text(
                    text=caption_text,
                    reply_markup=reply_markup
                )
        else:
            await update.message.reply_text(
                text=caption_text,
                reply_markup=reply_markup
            )
            
        logger.info(f"User {user.id} started the bot")
        
    except Exception as e:
        logger.error(f"Error in start_command: {e}", exc_info=True)
        await update.message.reply_text("❌ An error occurred. Please try again later.")


async def download_file_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle file download button click"""
    query = update.callback_query
    await query.answer()
    
    try:
        # Get file information from database
        file_type = db.get_setting("file_type")  # 'document', 'photo', 'video', etc.
        file_id = db.get_setting("file_id")
        file_caption = db.get_setting("file_caption") or "📥 Here's your file!"
        
        if not file_id:
            await query.message.reply_text("❌ No file available at the moment. Please check back later.")
            return
        
        # Send file based on type
        if file_type == "photo":
            await query.message.reply_photo(photo=file_id, caption=file_caption)
        elif file_type == "video":
            await query.message.reply_video(video=file_id, caption=file_caption)
        elif file_type == "audio":
            await query.message.reply_audio(audio=file_id, caption=file_caption)
        else:
            # Default to document (APK, PDF, etc.)
            await query.message.reply_document(document=file_id, caption=file_caption)
        
        logger.info(f"File sent to user {query.from_user.id}")
        
    except Exception as e:
        logger.error(f"Error sending file: {e}", exc_info=True)
        await query.message.reply_text("❌ An error occurred while sending the file. Please try again later.")


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command"""
    await admin_panel.admin_menu(update, context)




async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)


def main():
    """Main function to start the bot"""
    global scheduler
    
    # Fix for Python 3.14: Create event loop explicitly
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Create and set event loop for Python 3.14 compatibility
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        # No event loop exists (Python 3.14 behavior)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CallbackQueryHandler(download_file_callback, pattern="^download_file$"))
    application.add_handler(admin_panel.get_conversation_handler())
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Initialize scheduler
    scheduler = MessageScheduler(db, application.bot)
    
    # Start scheduler
    async def post_init(app: Application):
        """Initialize after bot is ready"""
        # Create task in the current event loop
        scheduler.task = asyncio.create_task(scheduler.scheduler_loop())
        logger.info("Scheduler started")
    
    # Start the bot
    logger.info("Starting bot...")
    application.post_init = post_init
    application.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=None)


if __name__ == "__main__":
    main()

