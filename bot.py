import os
import time
import threading
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.getenv("BOT_TOKEN", "8901421905:AAECwHE3UYN3YeQLVCh8x7nikV-zWFkxMq8")

bot = telebot.TeleBot(BOT_TOKEN)

BASE_RAW_URL = "https://raw.githubusercontent.com/meoponly/tallentex-resource-vault/main/"

VAULT = {
    "2026": [
        {"title": "Sample Paper", "file": "SP-2026.pdf"}
    ],
    "2025": [
        {"title": "Question Paper", "file": "QP-2025.pdf"}
    ],
    "2024": [
        {"title": "Question Paper", "file": "QP-2024.pdf"}
    ],
    "2023": [
        {"title": "Question Paper", "file": "QP-2023.pdf"}
    ],
    "2022": [
        {"title": "Question Paper", "file": "QP-2022.pdf"}
    ],
    "2021": [
        {"title": "Question Paper", "file": "QP-2021.pdf"}
    ],
    "2019": [
        {"title": "Paper 1", "file": "QP-2019-Paper1.pdf"},
        {"title": "Paper 2", "file": "QP-2019-Paper2.pdf"},
        {"title": "Paper 3", "file": "QP-2019-Paper3.pdf"}
    ],
    "2018": [
        {"title": "Paper 1", "file": "QP-2018-Paper1.pdf"},
        {"title": "Paper 2", "file": "QP-2018-Paper2.pdf"},
        {"title": "Paper 3", "file": "QP-2018-Paper3.pdf"}
    ],
    "2017": [
        {"title": "Paper 1", "file": "QP-2017-Paper1.pdf"},
        {"title": "Paper 2", "file": "QP-2017-Paper2.pdf"}
    ],
    "2016": [
        {"title": "Paper 1", "file": "QP-2016-Paper1.pdf"},
        {"title": "Paper 2", "file": "QP-2016-Paper2.pdf"}
    ],
    "2015": [
        {"title": "Paper 1", "file": "QP-2015-Paper1.pdf"},
        {"title": "Paper 2", "file": "QP-2015-Paper2.pdf"}
    ]
}

def auto_delete_after_delay(chat_id, message_ids, delay=300):
    def _delete():
        time.sleep(delay)
        for msg_id in message_ids:
            try:
                bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except Exception:
                pass

    threading.Thread(target=_delete, daemon=True).start()

def create_year_keyboard():
    keyboard = InlineKeyboardMarkup()

    # Featured top row: 2026 Sample Paper
    keyboard.row(InlineKeyboardButton(text="🎯 2026 Sample Paper", callback_data="yr_2026"))

    # Symmetrical 2x5 grid for older years
    previous_years = ["2025", "2024", "2023", "2022", "2021", "2019", "2018", "2017", "2016", "2015"]
    for i in range(0, len(previous_years), 2):
        y1 = previous_years[i]
        y2 = previous_years[i + 1]
        keyboard.row(
            InlineKeyboardButton(text=f"{y1}", callback_data=f"yr_{y1}"),
            InlineKeyboardButton(text=f"{y2}", callback_data=f"yr_{y2}")
        )

    keyboard.row(InlineKeyboardButton(text="Developer: @meoponly", url="https://t.me/meoponly"))
    return keyboard

def get_menu_text():
    return (
        "📚 *TALLENTEX Question Paper Vault*\n\n"
        "Select an exam year below to receive the PDF in your DM:"
    )

def build_caption(year, paper_title, filename):
    return (
        f"📄 *TALLENTEX {year}*\n"
        f"📝 *Paper / Set:* {paper_title}\n"
        f"📁 *File:* `{filename}`"
    )

def deliver_pdf(call, filename, caption):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    doc_url = BASE_RAW_URL + filename
    is_group = (chat_id != user_id)

    # Acknowledge the callback silently so button stops spinning
    bot.answer_callback_query(call.id)

    try:
        bot.send_document(
            chat_id=user_id,
            document=doc_url,
            caption=caption,
            parse_mode="Markdown"
        )
        if is_group:
            confirm_msg = bot.send_message(
                chat_id=chat_id,
                text=f"✅ Sent `{filename}` to your DM!",
                parse_mode="Markdown"
            )
            auto_delete_after_delay(chat_id, [confirm_msg.message_id], delay=10)
    except Exception:
        # If user blocked/never started the bot or download failed, silently ignore
        pass

@bot.message_handler(commands=['pyq', 'tallentex', 'start'])
def handle_start_command(message):
    is_group = (message.chat.type in ['group', 'supergroup'])
    
    sent_msg = bot.reply_to(
        message, 
        get_menu_text(), 
        parse_mode="Markdown", 
        reply_markup=create_year_keyboard()
    )

    if is_group:
        auto_delete_after_delay(
            chat_id=message.chat.id, 
            message_ids=[message.message_id, sent_msg.message_id], 
            delay=300
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("yr_"))
def handle_year_choice(call):
    year = call.data.split("_")[1]
    papers = VAULT.get(year, [])

    if not papers:
        bot.answer_callback_query(call.id)
        return

    # Single-paper years (2021-2026)
    if len(papers) == 1:
        paper = papers[0]
        caption = build_caption(year, paper["title"], paper["file"])
        deliver_pdf(call, paper["file"], caption)
        return

    # Multi-paper years (2015-2019)
    bot.answer_callback_query(call.id)
    kb = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton(
            text=f"{p['title']}",
            callback_data=f"doc_{year}_{idx}"
        )
        for idx, p in enumerate(papers)
    ]
    kb.add(*buttons)
    kb.row(InlineKeyboardButton(text="⬅️ Back to Years", callback_data="back_years"))

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=(
            f"📂 *TALLENTEX {year}*\n\n"
            f"This year has multiple papers. Select one:"
        ),
        parse_mode="Markdown",
        reply_markup=kb
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("doc_"))
def handle_document_choice(call):
    _, year, idx_str = call.data.split("_")
    idx = int(idx_str)
    paper = VAULT[year][idx]
    caption = build_caption(year, paper["title"], paper["file"])

    deliver_pdf(call, paper["file"], caption)

@bot.callback_query_handler(func=lambda call: call.data == "back_years")
def handle_back_button(call):
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=get_menu_text(),
        parse_mode="Markdown",
        reply_markup=create_year_keyboard()
    )

if __name__ == "__main__":
    print("Tallentex Vault Bot is running...")
    bot.infinity_polling()
