import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Bot
from telegram.error import TelegramError
from db import Database

logger = logging.getLogger(__name__)


class MessageScheduler:
    def __init__(self, db: Database, bot: Bot):
        self.db = db
        self.bot = bot
        self.is_running = False
        self.task = None

    async def send_auto_messages(self):
        """Send scheduled messages to all active users"""
        try:
            # Check if auto messages are enabled
            if self.db.get_setting("auto_messages_enabled") != "1":
                logger.debug("Auto messages are disabled")
                return

            auto_message_text = self.db.get_setting("auto_message_text")
            if not auto_message_text:
                logger.warning("Auto message text is not set")
                return

            users = self.db.get_active_users()
            logger.info(f"Sending auto messages to {len(users)} users")

            success_count = 0
            failed_count = 0

            for user in users:
                try:
                    await self.bot.send_message(
                        chat_id=user["user_id"],
                        text=auto_message_text
                    )
                    self.db.update_last_message_sent(user["user_id"])
                    success_count += 1
                    logger.debug(f"Auto message sent to user {user['user_id']}")
                    
                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.05)
                    
                except TelegramError as e:
                    logger.warning(f"Failed to send message to user {user['user_id']}: {e}")
                    
                    # Check if user blocked the bot
                    if "blocked" in str(e).lower() or "chat not found" in str(e).lower():
                        self.db.mark_user_inactive(user["user_id"])
                        logger.info(f"User {user['user_id']} marked as inactive (blocked)")
                    
                    failed_count += 1

            logger.info(f"Auto messages completed: {success_count} success, {failed_count} failed")

        except Exception as e:
            logger.error(f"Error in send_auto_messages: {e}", exc_info=True)

    async def scheduler_loop(self):
        """Main scheduler loop"""
        self.is_running = True
        logger.info("Scheduler started")

        while self.is_running:
            try:
                # Get interval hours
                interval_hours = int(self.db.get_setting("interval_hours") or "8")
                
                # Wait for the interval
                logger.info(f"Waiting {interval_hours} hours before next auto message batch...")
                await asyncio.sleep(interval_hours * 3600)  # Convert hours to seconds
                
                # Send messages
                await self.send_auto_messages()

            except asyncio.CancelledError:
                logger.info("Scheduler cancelled")
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                # Wait a bit before retrying
                await asyncio.sleep(60)

    def start(self, application):
        """Start the scheduler using the application's event loop"""
        if not self.is_running:
            loop = application.job_queue.scheduler._loop if hasattr(application.job_queue, 'scheduler') else asyncio.get_event_loop()
            self.task = loop.create_task(self.scheduler_loop())
            logger.info("Scheduler task created")

    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        if self.task:
            self.task.cancel()
            logger.info("Scheduler stopped")

