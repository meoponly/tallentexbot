import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.getenv("BOT_TOKEN", "8901421905:AAECwHE3UYN3YeQLVCh8x7nikV-zWFkxMq8")

bot = telebot.TeleBot(BOT_TOKEN)
BOT_USERNAME = bot.get_me().username

BASE_RAW_URL = "https://raw.githubusercontent.com/meoponly/tallentex-resource-vault/main/"

VAULT = {
    "2015": [
        {"title": "Paper 1", "file": "QP-2015-Paper1.pdf"},
        {"title": "Paper 2", "file": "QP-2015-Paper2.pdf"}
    ],
    "2016": [
        {"title": "Paper 1", "file": "QP-2016-Paper1.pdf"},
        {"title": "Paper 2", "file": "QP-2016-Paper2.pdf"}
    ],
    "2017": [
        {"title": "Paper 1", "file": "QP-2017-Paper1.pdf"},
        {"title": "Paper 2", "file": "QP-2017-Paper2.pdf"}
    ],
    "2018": [
        {"title": "Paper 1", "file": "QP-2018-Paper1.pdf"},
        {"title": "Paper 2", "file": "QP-2018-Paper2.pdf"},
        {"title": "Paper 3", "file": "QP-2018-Paper3.pdf"}
    ],
    "2019": [
        {"title": "Paper 1", "file": "QP-2019-Paper1.pdf"},
        {"title": "Paper 2", "file": "QP-2019-Paper2.pdf"},
        {"title": "Paper 3", "file": "QP-2019-Paper3.pdf"}
    ],
    "2021": [
        {"title": "Question Paper", "file": "QP-2021.pdf"}
    ],
    "2022": [
        {"title": "Question Paper", "file": "QP-2022.pdf"}
    ],
    "2023": [
        {"title": "Question Paper", "file": "QP-2023.pdf"}
    ],
    "2024": [
        {"title": "Question Paper", "file": "QP-2024.pdf"}
    ],
    "2025": [
        {"title": "Question Paper", "file": "QP-2025.pdf"}
    ],
    "2026": [
        {"title": "Sample Paper", "file": "SP-2026.pdf"}
    ]
}

def create_year_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=3)
    buttons = [
        InlineKeyboardButton(
            text="Sample 2026" if y == "2026" else f"📅 {y}",
            callback_data=f"yr_{y}"
        )
        for y in sorted(VAULT.keys(), reverse=True)
    ]
    keyboard.add(*buttons)
    return keyboard

def build_caption(year, paper_title, filename):
    return (
        f"📄 *TALLENTEX {year}*\n"
        f"📝 *Paper / Set:* {paper_title}\n"
        f"📁 *File:* `{filename}`\n\n"
        f"—\n"
        f"Made by @meoponly"
    )

def send_pdf_to_user(user_id, chat_id, filename, caption):
    doc_url = BASE_RAW_URL + filename
    is_group = (chat_id != user_id)

    try:
        bot.send_document(
            chat_id=user_id,
            document=doc_url,
            caption=caption,
            parse_mode="Markdown"
        )
        if is_group:
            bot.send_message(
                chat_id=chat_id,
                text=f"✅ Sent `{filename}` to your DM! Please check your private chat.",
                parse_mode="Markdown"
            )
    except telebot.apihelper.ApiTelegramException as e:
        if "bot can't initiate conversation" in str(e) or e.error_code == 403:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton(text="📩 Click here to Start Bot in DM", url=f"https://t.me/{BOT_USERNAME}?start=ready"))
            bot.send_message(
                chat_id=chat_id,
                text="⚠️ I cannot send you a DM because you haven't started me in private yet.\n\nClick the button below to start the bot, then request your paper again:",
                reply_markup=kb
            )
        else:
            bot.send_message(chat_id=chat_id, text=f"❌ Error sending file: {e}")

@bot.message_handler(commands=['pyq', 'tallentex', 'start'])
def handle_start_command(message):
    text = (
        "📚 *TALLENTEX Question Paper Vault*\n\n"
        "Select the year you want to view:"
    )
    bot.reply_to(message, text, parse_mode="Markdown", reply_markup=create_year_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("yr_"))
def handle_year_choice(call):
    year = call.data.split("_")[1]
    papers = VAULT.get(year, [])

    if not papers:
        bot.answer_callback_query(call.id, "No papers found for this year.", show_alert=True)
        return

    if len(papers) == 1:
        bot.answer_callback_query(call.id, text=f"Sending {year} paper to your DM...")
        paper = papers[0]
        caption = build_caption(year, paper["title"], paper["file"])
        send_pdf_to_user(
            user_id=call.from_user.id,
            chat_id=call.message.chat.id,
            filename=paper["file"],
            caption=caption
        )
        return

    bot.answer_callback_query(call.id)
    kb = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton(
            text=f"📄 {p['title']}",
            callback_data=f"doc_{year}_{idx}"
        )
        for idx, p in enumerate(papers)
    ]
    kb.add(*buttons)
    kb.add(InlineKeyboardButton(text="⬅️ Back to Years", callback_data="back_years"))

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"📂 *TALLENTEX {year}* has multiple papers. Select one:",
        parse_mode="Markdown",
        reply_markup=kb
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("doc_"))
def handle_document_choice(call):
    _, year, idx_str = call.data.split("_")
    idx = int(idx_str)
    paper = VAULT[year][idx]

    bot.answer_callback_query(call.id, text=f"Sending {paper['title']} to your DM...")
    caption = build_caption(year, paper["title"], paper["file"])

    send_pdf_to_user(
        user_id=call.from_user.id,
        chat_id=call.message.chat.id,
        filename=paper["file"],
        caption=caption
    )

@bot.callback_query_handler(func=lambda call: call.data == "back_years")
def handle_back_button(call):
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="📚 *TALLENTEX Question Paper Vault*\n\nSelect the year you want to view:",
        parse_mode="Markdown",
        reply_markup=create_year_keyboard()
    )

if __name__ == "__main__":
    print("Tallentex Vault Bot is running...")
    bot.infinity_polling()
