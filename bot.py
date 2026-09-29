import os
import time
import threading
import telebot
from telebot import types

# ----------------- Configuration ----------------- #
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
COOLDOWN_SECONDS = 30  # Cooldown duration per user in groups
AUTO_DELETE_DELAY = 5   # Seconds before deleting warning/prompt messages

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

# In-memory store: {user_id: last_command_timestamp}
user_last_action = {}
lock = threading.Lock()

# ----------------- Anti-Flood Helper ----------------- #
def is_rate_limited(user_id: int, chat_type: str) -> tuple[bool, int]:
    """
    Checks if a user is within cooldown.
    Applied primarily to groups/supergroups.
    """
    if chat_type not in ["group", "supergroup"]:
        return False, 0

    current_time = time.time()
    with lock:
        last_time = user_last_action.get(user_id, 0)
        remaining = int(COOLDOWN_SECONDS - (current_time - last_time))
        if remaining > 0:
            return True, remaining
        user_last_action[user_id] = current_time
        return False, 0

def delayed_delete(chat_id: int, message_ids: list[int], delay: int = AUTO_DELETE_DELAY):
    """Deletes specific messages after a specified delay in a separate thread."""
    def _delete():
        time.sleep(delay)
        for msg_id in message_ids:
            try:
                bot.delete_message(chat_id, msg_id)
            except Exception:
                pass  # Avoid crash if message is already deleted or bot lacks delete permission

    threading.Thread(target=_delete, daemon=True).start()

# ----------------- Command Handlers ----------------- #
@bot.message_handler(commands=["start", "help"])
def send_welcome(message: types.Message):
    limited, remaining = is_rate_limited(message.from_user.id, message.chat.type)
    if limited:
        warn = bot.reply_to(
            message,
            f"Slow down! Please wait {remaining} seconds before using commands again."
        )
        delayed_delete(message.chat.id, [message.message_id, warn.message_id])
        return

    text = (
        "Welcome to Tallentex Bot!\n"
        "Use /getfile to receive the requested resource."
    )
    sent_msg = bot.reply_to(message, text)

    # In groups, clean up messages after some time
    if message.chat.type in ["group", "supergroup"]:
        delayed_delete(message.chat.id, [message.message_id, sent_msg.message_id], delay=10)

@bot.message_handler(commands=["getfile"])
def send_file(message: types.Message):
    chat_type = message.chat.type
    user_id = message.from_user.id

    # Check anti-flood
    limited, remaining = is_rate_limited(user_id, chat_type)
    if limited:
        warn = bot.reply_to(
            message,
            f"Please wait {remaining}s before requesting a file again."
        )
        delayed_delete(message.chat.id, [message.message_id, warn.message_id])
        return

    # Notify user that processing has started
    status_msg = bot.reply_to(message, "Sending your file, please wait...")

    try:
        # Example document dispatch; replace with your target file path or file_id
        file_path = "sample_paper.pdf"
        
        if os.path.exists(file_path):
            with open(file_path, "rb") as doc:
                bot.send_document(
                    message.chat.id,
                    doc,
                    caption="Here is your requested Tallentex file."
                )
        else:
            # Fallback if testing without physical file
            bot.send_message(
                message.chat.id,
                "File could not be found on the server. Please contact an admin."
            )

        # Auto-delete trigger and temporary status messages once sent
        if chat_type in ["group", "supergroup"]:
            delayed_delete(message.chat.id, [message.message_id, status_msg.message_id], delay=3)

    except Exception as e:
        bot.edit_message_text(
            f"An error occurred while sending the file: {e}",
            chat_id=message.chat.id,
            message_id=status_msg.message_id
        )
        if chat_type in ["group", "supergroup"]:
            delayed_delete(message.chat.id, [message.message_id, status_msg.message_id], delay=5)

# ----------------- Periodic Cleanup ----------------- #
def cleanup_cooldown_store():
    """Periodically purges old records to prevent memory growth in large groups."""
    while True:
        time.sleep(300)
        cutoff = time.time() - COOLDOWN_SECONDS
        with lock:
            expired_keys = [uid for uid, ts in user_last_action.items() if ts < cutoff]
            for uid in expired_keys:
                del user_last_action[uid]

threading.Thread(target=cleanup_cooldown_store, daemon=True).start()

# ----------------- Entry Point ----------------- #
if __name__ == "__main__":
    print("Bot is starting...")
    bot.infinity_polling(skip_pending=True)
