import json
import logging
import os
from dotenv import load_dotenv
from keep_alive import keep_alive

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================= LOAD ENV =================
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not found in .env")

# ================= LOGGING =================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# ================= LOAD COURSES JSON =================
with open("courses.json", "r", encoding="utf-8") as f:
    courses = json.load(f)["courses"]

# ================= BOT INIT (10 WORKERS) =================
bot = telebot.TeleBot(
    BOT_TOKEN,
    threaded=True,
    num_threads=10,   # 🔥 10 parallel workers
)

# ================= UI BUILDERS =================
def course_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    buttons = []

    for code, course in courses.items():
        buttons.append(
            InlineKeyboardButton(
                text=f"{code} – {course['title']}",
                callback_data=f"course|{code}"
            )
        )

    kb.add(*buttons)
    return kb


def category_menu(course_code):
    kb = InlineKeyboardMarkup(row_width=1)

    for cat in courses[course_code]["categories"]:
        kb.add(
            InlineKeyboardButton(
                f"📂 {cat}",
                callback_data=f"category|{course_code}|{cat}"
            )
        )

    kb.add(
        InlineKeyboardButton("⬅️ Back", callback_data="back|courses")
    )
    return kb


def resource_menu(course_code, category):
    kb = InlineKeyboardMarkup(row_width=1)

    for idx, res in enumerate(courses[course_code]["categories"][category]):
        icon = "📄" if res["type"] in ("pdf", "docx") else "📊"
        kb.add(
            InlineKeyboardButton(
                f"{icon} {res['title']}",
                callback_data=f"file|{course_code}|{category}|{idx}"
            )
        )

    kb.add(
        InlineKeyboardButton(
            "⬅️ Back",
            callback_data=f"back|category|{course_code}"
        )
    )
    return kb

# ================= COMMAND =================
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "👋 *Welcome to University Resource Bot*\n\n"
        "🎓 Select your course to get lecture notes, slides & books.",
        parse_mode="Markdown",
        reply_markup=course_menu(),
    )

# ================= CALLBACK HANDLER =================
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    data = call.data.split("|")

    # ---- COURSE ----
    if data[0] == "course":
        code = data[1]
        bot.edit_message_text(
            f"📘 *{code} – {courses[code]['title']}*\n\n📂 Select a category:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
            reply_markup=category_menu(code),
        )

    # ---- CATEGORY ----
    elif data[0] == "category":
        code, category = data[1], data[2]
        bot.edit_message_text(
            f"📂 *{category}*\n\n📄 Select a resource:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
            reply_markup=resource_menu(code, category),
        )

    # ---- FILE ----
    elif data[0] == "file":
        code, category, idx = data[1], data[2], int(data[3])
        res = courses[code]["categories"][category][idx]

        bot.answer_callback_query(call.id, "📥 Sending file...")
        bot.send_document(
            call.message.chat.id,
            res["file_id"],
            caption=f"📄 *{res['title']}*",
            parse_mode="Markdown",
        )

    # ---- BACK ----
    elif data[0] == "back":
        if data[1] == "courses":
            bot.edit_message_text(
                "🎓 *Select a course:*",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="Markdown",
                reply_markup=course_menu(),
            )

        elif data[1] == "category":
            code = data[2]
            bot.edit_message_text(
                f"📘 *{code} – {courses[code]['title']}*\n\n📂 Select a category:",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="Markdown",
                reply_markup=category_menu(code),
            )

# ================= MAIN =================
if __name__ == "__main__":
    keep_alive()
    print("🚀 TeleBot running with 10 workers (non-blocking)")
    bot.infinity_polling(skip_pending=True)
