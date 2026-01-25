import json
import logging
import os
from dotenv import load_dotenv
from keep_alive import keep_alive


from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ================= LOAD ENV =================
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not found in .env")

# ================= LOGGING =================
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# ================= LOAD COURSES JSON =================
with open("courses.json", "r", encoding="utf-8") as f:
    courses = json.load(f)["courses"]

# ================= UI BUILDERS =================
def course_menu():
    keyboard = []
    row = []
    for i, (code, course) in enumerate(courses.items(), start=1):
        row.append(
            InlineKeyboardButton(
                text=f"{code} – {course['title']}",
                callback_data=f"course|{code}",
            )
        )
        if i % 2 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def category_menu(course_code):
    keyboard = [
        [InlineKeyboardButton(f"📂 {cat}", callback_data=f"category|{course_code}|{cat}")]
        for cat in courses[course_code]["categories"]
    ]
    keyboard.append(
        [InlineKeyboardButton("⬅️ Back", callback_data="back|courses")]
    )
    return InlineKeyboardMarkup(keyboard)


def resource_menu(course_code, category):
    keyboard = []
    for idx, res in enumerate(courses[course_code]["categories"][category]):
        icon = "📄" if res["type"] in ["pdf", "docx"] else "📊"
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{icon} {res['title']}",
                    callback_data=f"file|{course_code}|{category}|{idx}",
                )
            ]
        )

    keyboard.append(
        [InlineKeyboardButton("⬅️ Back", callback_data=f"back|category|{course_code}")]
    )
    return InlineKeyboardMarkup(keyboard)

# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Welcome to University Resource Bot*\n\n"
        "🎓 Select your course to get lecture notes, slides & books.",
        parse_mode="Markdown",
        reply_markup=course_menu(),
    )

# ================= CALLBACK HANDLER =================
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("|")

    # ---- COURSE ----
    if data[0] == "course":
        code = data[1]
        await query.edit_message_text(
            f"📘 *{code} – {courses[code]['title']}*\n\n"
            f"📂 Select a category:",
            parse_mode="Markdown",
            reply_markup=category_menu(code),
        )

    # ---- CATEGORY ----
    elif data[0] == "category":
        code, category = data[1], data[2]
        await query.edit_message_text(
            f"📂 *{category}*\n\n📄 Select a resource:",
            parse_mode="Markdown",
            reply_markup=resource_menu(code, category),
        )

    # ---- FILE ----
    elif data[0] == "file":
        code, category, idx = data[1], data[2], int(data[3])
        res = courses[code]["categories"][category][idx]

        await query.answer("📥 Sending file...")
        await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=res["file_id"],
            caption=f"📄 *{res['title']}*",
            parse_mode="Markdown",
        )

    # ---- BACK ----
    elif data[0] == "back":
        if data[1] == "courses":
            await query.edit_message_text(
                "🎓 *Select a course:*",
                parse_mode="Markdown",
                reply_markup=course_menu(),
            )

        elif data[1] == "category":
            code = data[2]
            await query.edit_message_text(
                f"📘 *{code} – {courses[code]['title']}*\n\n"
                f"📂 Select a category:",
                parse_mode="Markdown",
                reply_markup=category_menu(code),
            )

# ================= MAIN =================
def main():
    keep_alive()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("🚀 Async Telegram Resource Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()

