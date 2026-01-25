import json
import logging
import os
import asyncio
from dotenv import load_dotenv
from keep_alive import keep_alive

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import Command

# ================= LOAD ENV =================
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not found")

# ================= LOGGING =================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# ================= LOAD COURSES =================
with open("courses.json", "r", encoding="utf-8") as f:
    courses = json.load(f)["courses"]

# ================= BOT INIT =================
bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# ================= UI BUILDERS =================
def course_menu():
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    row = []

    for i, (code, course) in enumerate(courses.items(), start=1):
        row.append(
            InlineKeyboardButton(
                text=f"{code} – {course['title']}",
                callback_data=f"course|{code}",
            )
        )
        if i % 2 == 0:
            kb.inline_keyboard.append(row)
            row = []

    if row:
        kb.inline_keyboard.append(row)

    return kb


def category_menu(course_code):
    kb = InlineKeyboardMarkup(inline_keyboard=[])

    for cat in courses[course_code]["categories"]:
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"📂 {cat}",
                callback_data=f"category|{course_code}|{cat}",
            )
        ])

    kb.inline_keyboard.append([
        InlineKeyboardButton("⬅️ Back", callback_data="back|courses")
    ])
    return kb


def resource_menu(course_code, category):
    kb = InlineKeyboardMarkup(inline_keyboard=[])

    for idx, res in enumerate(courses[course_code]["categories"][category]):
        icon = "📄" if res["type"] in ("pdf", "docx") else "📊"
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{icon} {res['title']}",
                callback_data=f"file|{course_code}|{category}|{idx}",
            )
        ])

    kb.inline_keyboard.append([
        InlineKeyboardButton(
            "⬅️ Back",
            callback_data=f"back|category|{course_code}",
        )
    ])
    return kb

# ================= COMMAND =================
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "👋 *Welcome to University Resource Bot*\n\n"
        "🎓 Select your course to get lecture notes, slides & books.",
        parse_mode="Markdown",
        reply_markup=course_menu(),
    )

# ================= CALLBACK =================
@dp.callback_query(F.data)
async def callbacks(call: CallbackQuery):
    data = call.data.split("|")

    # ---- COURSE ----
    if data[0] == "course":
        code = data[1]
        await call.message.edit_text(
            f"📘 *{code} – {courses[code]['title']}*\n\n📂 Select a category:",
            parse_mode="Markdown",
            reply_markup=category_menu(code),
        )

    # ---- CATEGORY ----
    elif data[0] == "category":
        code, category = data[1], data[2]
        await call.message.edit_text(
            f"📂 *{category}*\n\n📄 Select a resource:",
            parse_mode="Markdown",
            reply_markup=resource_menu(code, category),
        )

    # ---- FILE ----
    elif data[0] == "file":
        code, category, idx = data[1], data[2], int(data[3])
        res = courses[code]["categories"][category][idx]

        await call.answer("📥 Sending file...")
        await bot.send_document(
            call.message.chat.id,
            res["file_id"],
            caption=f"📄 *{res['title']}*",
            parse_mode="Markdown",
        )

    # ---- BACK ----
    elif data[0] == "back":
        if data[1] == "courses":
            await call.message.edit_text(
                "🎓 *Select a course:*",
                parse_mode="Markdown",
                reply_markup=course_menu(),
            )
        elif data[1] == "category":
            code = data[2]
            await call.message.edit_text(
                f"📘 *{code} – {courses[code]['title']}*\n\n📂 Select a category:",
                parse_mode="Markdown",
                reply_markup=category_menu(code),
            )

# ================= MAIN =================
async def main():
    keep_alive()
    print("🚀 FULL ASYNC aiogram bot running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
