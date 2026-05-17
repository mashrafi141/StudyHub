import json
import logging
import os
import re
import threading

from dotenv import load_dotenv
from keep_alive import keep_alive

import telebot

from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)

# ================= LOAD ENV =================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in .env")

# ================= CONFIG =================
SEMESTER = "Summer 2026"
BATCH = "CSE 22"

ADMIN_IDS = [
    7179006993
]

UPLOAD_STATE = {}

# ================= THREAD LOCK =================
data_lock = threading.Lock()

# ================= LOGGING =================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# ================= BOT =================
bot = telebot.TeleBot(
    BOT_TOKEN,
    threaded=True,
    num_threads=50,
    parse_mode="HTML"
)

# ================= HELPERS =================
def load_data():

    with open("courses.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):

    with data_lock:

        with open("courses.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

def is_admin(user_id):

    return user_id in ADMIN_IDS

def re_search(text, pattern):

    match = re.search(pattern, text)

    if match:
        return match.group(1).strip()

    return None

def main_header():

    return f"""
━━━━━━━━━━━━━━━━━━
🎓 <b>STUDY HUB PRO</b>

📅 Semester: <b>{SEMESTER}</b>
👨‍🎓 Batch: <b>{BATCH}</b>

📚 Available Courses:
• Numerical Methods
• Compiler Design
• Compiler Design Lab
• DBMS
• DBMS Lab

<i>Select your course below</i>
━━━━━━━━━━━━━━━━━━
"""

# ================= REPLY KEYBOARD =================

def main_reply_keyboard(user_id):

    kb = ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    kb.row(
        KeyboardButton("🚀 Start"),
        KeyboardButton("📚 Courses")
    )

    kb.row(
        KeyboardButton("❓ Help"),
        KeyboardButton("👨‍💻 About")
    )

    # ADMIN ONLY
    if is_admin(user_id):

        kb.row(
            KeyboardButton("⚙ Manage")
        )

    return kb


# ================= MENUS =================
def course_menu():

    data = load_data()

    kb = InlineKeyboardMarkup(row_width=2)

    for code, course in data["courses"].items():

        kb.add(
            InlineKeyboardButton(
                text=f"{course['emoji']} {course['title']}",
                callback_data=f"course|{code}"
            )
        )

    return kb

def category_menu(course_code):

    data = load_data()

    course = data["courses"][course_code]

    kb = InlineKeyboardMarkup(row_width=2)

    category_icons = {
        "notes": "📄",
        "books": "📚",
        "lecture_notes": "🧠",
        "videos": "🎥",
        "playlists": "📺"
    }

    for category in course["categories"]:

        icon = category_icons.get(category, "📂")

        kb.add(
            InlineKeyboardButton(
                text=f"{icon} {category.replace('_', ' ').title()}",
                callback_data=f"category|{course_code}|{category}"
            )
        )

    kb.add(

        InlineKeyboardButton(
            "⬅ Back",
            callback_data="back|courses"
        ),

        InlineKeyboardButton(
            "🏠 Home",
            callback_data="home"
        )
    )

    return kb

def resource_menu(course_code, category):

    data = load_data()

    resources = data["courses"][course_code]["categories"][category]

    kb = InlineKeyboardMarkup(row_width=1)

    # ================= EMPTY CATEGORY =================
    if not resources:

        empty_messages = {
            "notes": "📄 No notes uploaded yet.",
            "books": "📚 No books uploaded yet.",
            "lecture_notes": "🧠 No lecture notes available yet.",
            "videos": "🎥 No videos uploaded yet.",
            "playlists": "📺 No playlists added yet."
        }

        msg = empty_messages.get(
            category,
            "😔 Nothing uploaded yet."
        )

        kb.add(

            InlineKeyboardButton(
                "⬅ Back",
                callback_data=f"back|course|{course_code}"
            ),

            InlineKeyboardButton(
                "🏠 Home",
                callback_data="home"
            )
        )

        return kb, f"""
━━━━━━━━━━━━━━━━━━
⚠ <b>No Resources Found</b>

📂 Category:
<b>{category.replace('_', ' ').title()}</b>

{msg}

⏳ Please check again later.
━━━━━━━━━━━━━━━━━━
"""

    # ================= NORMAL RESOURCES =================
    for idx, res in enumerate(resources):

        if category == "videos":
            icon = "🎥"

        elif category == "playlists":
            icon = "📺"

        else:
            icon = "📄"

        kb.add(
            InlineKeyboardButton(
                text=f"{icon} {res['title']}",
                callback_data=f"resource|{course_code}|{category}|{idx}"
            )
        )

    kb.add(

        InlineKeyboardButton(
            "⬅ Back",
            callback_data=f"back|course|{course_code}"
        ),

        InlineKeyboardButton(
            "🏠 Home",
            callback_data="home"
        )
    )

    return kb, f"""
━━━━━━━━━━━━━━━━━━
📂 <b>{category.replace('_', ' ').title()}</b>

📚 Select a resource below
━━━━━━━━━━━━━━━━━━
"""

# ================= START =================
@bot.message_handler(commands=["start"])
def start(message):

    bot.send_message(
        message.chat.id,
        main_header(),
        reply_markup=main_reply_keyboard(message.from_user.id)
    )

    bot.send_message(
        message.chat.id,
        "📚 <b>Select your course below:</b>",
        reply_markup=course_menu()
    )

# ================= REPLY BUTTONS =================
@bot.message_handler(func=lambda m: m.text == "🚀 Start")
def start_button(message):

    bot.send_message(
        message.chat.id,
        main_header(),
        reply_markup=main_reply_keyboard(message.from_user.id)
    )

    bot.send_message(
        message.chat.id,
        "📚 <b>Select your course below:</b>",
        reply_markup=course_menu()
    )

@bot.message_handler(func=lambda m: m.text == "📚 Courses")
def courses_button(message):

    bot.send_message(
        message.chat.id,
        """
━━━━━━━━━━━━━━━━━━
📚 <b>Available Courses</b>

Select your course below
━━━━━━━━━━━━━━━━━━
""",
        reply_markup=course_menu()
    )

@bot.message_handler(func=lambda m: m.text == "❓ Help")
def help_button(message):

    bot.send_message(
        message.chat.id,
        """
━━━━━━━━━━━━━━━━━━
❓ <b>HOW TO USE STUDY HUB</b>

📚 Select a course

📂 Choose category:
• Notes
• Books
• Lecture Notes
• Videos
• Playlists

📥 Tap any resource to access it instantly.

━━━━━━━━━━━━━━━━━━

✨ FEATURES

✅ Organized semester resources
✅ Topic-wise lecture notes
✅ Video tutorials
✅ YouTube playlists
✅ Instant file access

━━━━━━━━━━━━━━━━━━

🚀 Easy • Fast • Clean
━━━━━━━━━━━━━━━━━━
"""
    )

@bot.message_handler(func=lambda m: m.text == "👨‍💻 About")
def about_button(message):

    bot.send_message(
        message.chat.id,
        """
━━━━━━━━━━━━━━━━━━
👨‍💻 <b>ABOUT THIS BOT</b>

🎓 StudyHub Pro

Developed By:
<b>Mashrafi Haque</b>

🏫 CSE Department

📚 Semester Resource Management Bot

━━━━━━━━━━━━━━━━━━

✨ Built for students
⚡ Fast & Organized Experience

━━━━━━━━━━━━━━━━━━
"""
    )

@bot.message_handler(func=lambda m: m.text == "⚙ Manage")
def manage_button(message):

    if not is_admin(message.from_user.id):

        bot.reply_to(
            message,
            "❌ Admin only feature."
        )

        return

    kb = InlineKeyboardMarkup(row_width=2)

    kb.add(

        InlineKeyboardButton(
            "➕ Add Resources",
            callback_data="manage_add"
        ),

        InlineKeyboardButton(
            "🗑 Remove Resources",
            callback_data="manage_remove"
        )
    )

    kb.add(
        InlineKeyboardButton(
            "🏠 Home",
            callback_data="home"
        )
    )

    bot.send_message(
        message.chat.id,
        """
━━━━━━━━━━━━━━━━━━
⚙ <b>ADMIN CONTROL PANEL</b>

Select an option below
━━━━━━━━━━━━━━━━━━
""",
        reply_markup=kb
    )



# ================= ADMIN PANEL =================
@bot.message_handler(commands=["admin"])
def admin_panel(message):

    if not is_admin(message.from_user.id):
        return

    text = """
━━━━━━━━━━━━━━━━━━
⚙ <b>ADMIN PANEL</b>

📤 Upload a file with caption:

/course compiler_design
/category notes
/title Chapter 1 Notes

━━━━━━━━━━━━━━━━━━

🎥 Add Videos:
/addvideo

📺 Add Playlists:
/addplaylist

━━━━━━━━━━━━━━━━━━
"""

    bot.send_message(
        message.chat.id,
        text
    )

# ================= AUTO FILE DETECTION =================
@bot.message_handler(content_types=["document"])
def handle_document(message):

    if not is_admin(message.from_user.id):
        return

    if not message.caption:

        bot.reply_to(
            message,
            """
━━━━━━━━━━━━━━━━━━
⚠ <b>Missing Caption</b>

📄 Please upload file with:

/course
/category
/title

━━━━━━━━━━━━━━━━━━
"""
        )

        return

    caption = message.caption

    try:

        course = re_search(caption, r"/course (.+)")
        category = re_search(caption, r"/category (.+)")
        title = re_search(caption, r"/title (.+)")

    except:

        bot.reply_to(
            message,
            """
━━━━━━━━━━━━━━━━━━
❌ <b>Invalid Caption Format</b>

Example:

/course compiler_design
/category notes
/title Chapter 1

━━━━━━━━━━━━━━━━━━
"""
        )

        return

    data = load_data()

    if not course or course not in data["courses"]:

        bot.reply_to(
            message,
            """
━━━━━━━━━━━━━━━━━━
❌ <b>Course Not Found</b>
━━━━━━━━━━━━━━━━━━
"""
        )

        return

    if not category or category not in data["courses"][course]["categories"]:

        bot.reply_to(
            message,
            """
━━━━━━━━━━━━━━━━━━
❌ <b>Category Not Found</b>
━━━━━━━━━━━━━━━━━━
"""
        )

        return

    resource = {
        "title": title,
        "file_id": message.document.file_id,
        "file_name": message.document.file_name,
        "type": "pdf"
    }

    data["courses"][course]["categories"][category].append(resource)

    save_data(data)

    bot.reply_to(
        message,
        f"""
━━━━━━━━━━━━━━━━━━
✅ <b>Resource Added Successfully</b>

📄 <b>{title}</b>

📚 {category.replace('_', ' ').title()}
🎓 {course.replace('_', ' ').title()}

━━━━━━━━━━━━━━━━━━
"""
    )

# ================= VIDEO =================
@bot.message_handler(commands=["addvideo"])
def add_video(message):

    if not is_admin(message.from_user.id):
        return

    UPLOAD_STATE[message.from_user.id] = {
        "type": "video"
    }

    bot.send_message(
        message.chat.id,
        """
━━━━━━━━━━━━━━━━━━
🎥 <b>Add Video</b>

Send:
course|title|url

━━━━━━━━━━━━━━━━━━
"""
    )

# ================= PLAYLIST =================
@bot.message_handler(commands=["addplaylist"])
def add_playlist(message):

    if not is_admin(message.from_user.id):
        return

    UPLOAD_STATE[message.from_user.id] = {
        "type": "playlist"
    }

    bot.send_message(
        message.chat.id,
        """
━━━━━━━━━━━━━━━━━━
📺 <b>Add Playlist</b>

Send:
course|title|url

━━━━━━━━━━━━━━━━━━
"""
    )

# ================= PROCESS VIDEO/PLAYLIST =================
@bot.message_handler(func=lambda m: m.from_user.id in UPLOAD_STATE)
def process_upload(message):

    state = UPLOAD_STATE.get(message.from_user.id)

    try:
        course, title, url = message.text.split("|")

    except:

        bot.reply_to(
            message,
            """
━━━━━━━━━━━━━━━━━━
❌ Invalid Format

Use:
course|title|url
━━━━━━━━━━━━━━━━━━
"""
        )

        return

    data = load_data()

    if course not in data["courses"]:

        bot.reply_to(
            message,
            """
━━━━━━━━━━━━━━━━━━
❌ Course Not Found
━━━━━━━━━━━━━━━━━━
"""
        )

        return

    if state["type"] == "video":

        data["courses"][course]["categories"]["videos"].append({
            "title": title,
            "url": url
        })

    elif state["type"] == "playlist":

        data["courses"][course]["categories"]["playlists"].append({
            "title": title,
            "url": url
        })

    save_data(data)

    del UPLOAD_STATE[message.from_user.id]

    bot.reply_to(
        message,
        """
━━━━━━━━━━━━━━━━━━
✅ Added Successfully
━━━━━━━━━━━━━━━━━━
"""
    )

# ================= ADMIN MANAGE PANEL =================

@bot.message_handler(commands=["manage"])
def manage_panel(message):

    if not is_admin(message.from_user.id):
        return

    data = load_data()

    kb = InlineKeyboardMarkup(row_width=2)

    for code, course in data["courses"].items():

        kb.add(
            InlineKeyboardButton(
                text=f"{course['emoji']} {course['title']}",
                callback_data=f"manage_course|{code}"
            )
        )

    kb.add(
        InlineKeyboardButton(
            "🏠 Home",
            callback_data="home"
        )
    )

    bot.send_message(
        message.chat.id,
        """
━━━━━━━━━━━━━━━━━━
⚙ <b>ADMIN MANAGEMENT PANEL</b>

📚 Select a course to manage resources
━━━━━━━━━━━━━━━━━━
""",
        reply_markup=kb
    )


# ================= CONFIRM DELETE =================



# ================= CALLBACKS =================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):

    data = call.data.split("|")

    all_data = load_data()
# ================= MANAGE ADD =================
    if data[0] == "manage_add":

        kb = InlineKeyboardMarkup(row_width=1)

        kb.add(

            InlineKeyboardButton(
                "📄 Add Notes",
                callback_data="add_notes"
            ),

            InlineKeyboardButton(
                "📚 Add Books",
                callback_data="add_books"
            ),

            InlineKeyboardButton(
                "🧠 Add Lecture Notes",
                callback_data="add_lecture_notes"
            ),

            InlineKeyboardButton(
                "🎥 Add Video Link",
                callback_data="add_video_link"
            ),

            InlineKeyboardButton(
                "📺 Add Playlist Link",
                callback_data="add_playlist_link"
            )
        )

        kb.add(

            InlineKeyboardButton(
                "⬅ Back",
                callback_data="manage_back"
            ),

            InlineKeyboardButton(
                "🏠 Home",
                callback_data="home"
            )
        )

        bot.edit_message_text(
            """
━━━━━━━━━━━━━━━━━━
➕ <b>ADD RESOURCES</b>

Select resource type
━━━━━━━━━━━━━━━━━━
""",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=kb
        )

    # ================= MANAGE REMOVE =================
    elif data[0] == "manage_remove":

        data_json = load_data()

        kb = InlineKeyboardMarkup(row_width=2)

        for code, course in data_json["courses"].items():

            kb.add(
                InlineKeyboardButton(
                    text=f"{course['emoji']} {course['title']}",
                    callback_data=f"manage_course|{code}"
                )
            )

        kb.add(
            InlineKeyboardButton(
                "🏠 Home",
                callback_data="home"
            )
        )

        bot.edit_message_text(
            """
━━━━━━━━━━━━━━━━━━
🗑 <b>REMOVE RESOURCES</b>

📚 Select a course
━━━━━━━━━━━━━━━━━━
""",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=kb
        )



# ================= MANAGE COURSE =================
    elif data[0] == "manage_course":

        course_code = data[1]

        course = all_data["courses"][course_code]

        kb = InlineKeyboardMarkup(row_width=2)

        category_icons = {
            "notes": "📄",
            "books": "📚",
            "lecture_notes": "🧠",
            "videos": "🎥",
            "playlists": "📺"
        }

        for category in course["categories"]:

            kb.add(
                InlineKeyboardButton(
                    text=f"{category_icons.get(category, '📂')} {category.replace('_', ' ').title()}",
                    callback_data=f"manage_category|{course_code}|{category}"
                )
            )

        kb.add(

            InlineKeyboardButton(
                "⬅ Back",
                callback_data="manage_back"
            ),

            InlineKeyboardButton(
                "🏠 Home",
                callback_data="home"
            )
        )

        bot.edit_message_text(
            f"""
━━━━━━━━━━━━━━━━━━
⚙ <b>{course['title']} Management</b>

📂 Select a category
━━━━━━━━━━━━━━━━━━
""",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=kb
        )

    # ================= MANAGE CATEGORY =================
    elif data[0] == "manage_category":

        course_code = data[1]
        category = data[2]

        resources = all_data["courses"][course_code]["categories"][category]

        kb = InlineKeyboardMarkup(row_width=1)

        if not resources:

            kb.add(

                InlineKeyboardButton(
                    "⬅ Back",
                    callback_data=f"manage_course|{course_code}"
                ),

                InlineKeyboardButton(
                    "🏠 Home",
                    callback_data="home"
                )
            )

            bot.edit_message_text(
                f"""
━━━━━━━━━━━━━━━━━━
⚠ <b>No Resources Found</b>

📂 {category.replace('_', ' ').title()}

━━━━━━━━━━━━━━━━━━
""",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=kb
            )

            return

        for idx, res in enumerate(resources):

            kb.add(
                InlineKeyboardButton(
                    text=f"🗑 {res['title']}",
                    callback_data=f"manage_delete|{course_code}|{category}|{idx}"
                )
            )

        kb.add(

            InlineKeyboardButton(
                "⬅ Back",
                callback_data=f"manage_course|{course_code}"
            ),

            InlineKeyboardButton(
                "🏠 Home",
                callback_data="home"
            )
        )

        bot.edit_message_text(
            f"""
━━━━━━━━━━━━━━━━━━
🗑 <b>Delete Resources</b>

📂 {category.replace('_', ' ').title()}

Select a resource to remove
━━━━━━━━━━━━━━━━━━
""",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=kb
        )

    # ================= MANAGE DELETE =================
    elif data[0] == "manage_delete":

        course_code = data[1]
        category = data[2]
        idx = int(data[3])

        res = all_data["courses"][course_code]["categories"][category][idx]

        kb = InlineKeyboardMarkup(row_width=2)

        kb.add(

            InlineKeyboardButton(
                "✅ Yes Delete",
                callback_data=f"confirm_delete|{course_code}|{category}|{idx}"
            ),

            InlineKeyboardButton(
                "❌ Cancel",
                callback_data=f"manage_category|{course_code}|{category}"
            )
        )

        bot.edit_message_text(
            f"""
━━━━━━━━━━━━━━━━━━
⚠ <b>Confirm Delete</b>

📄 <b>{res['title']}</b>

This action cannot be undone.
━━━━━━━━━━━━━━━━━━
""",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=kb
        )

    # ================= SHOW ADD DOCS =================
    elif data[0] == "show_add_docs":

        bot.edit_message_text(
            """
━━━━━━━━━━━━━━━━━━
📄 <b>UPLOAD NOTES / BOOKS</b>

Upload file with caption:

/course compiler_design
/category notes
/title Chapter 1 Notes

━━━━━━━━━━━━━━━━━━
""",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )

    # ================= SHOW ADD VIDEO =================
    elif data[0] == "show_add_video":

        bot.edit_message_text(
            """
━━━━━━━━━━━━━━━━━━
🎥 <b>ADD VIDEO</b>

Use command:

/addvideo

Then send:

course|title|url

━━━━━━━━━━━━━━━━━━
""",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )

    # ================= SHOW ADD PLAYLIST =================
    elif data[0] == "show_add_playlist":

        bot.edit_message_text(
            """
━━━━━━━━━━━━━━━━━━
📺 <b>ADD PLAYLIST</b>

Use command:

/addplaylist

Then send:

course|title|url

━━━━━━━━━━━━━━━━━━
""",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )

    # ================= MANAGE BACK =================
    elif data[0] == "manage_back":

        kb = InlineKeyboardMarkup(row_width=2)

        kb.add(

            InlineKeyboardButton(
                "➕ Add Resources",
                callback_data="manage_add"
            ),

            InlineKeyboardButton(
                "🗑 Remove Resources",
                callback_data="manage_remove"
            )
        )

        kb.add(
            InlineKeyboardButton(
                "🏠 Home",
                callback_data="home"
            )
        )

        bot.edit_message_text(
            """
━━━━━━━━━━━━━━━━━━
⚙ <b>ADMIN CONTROL PANEL</b>

Select an option below
━━━━━━━━━━━━━━━━━━
""",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=kb
        )

# ================= CONFIRM DELETE =================
    elif data[0] == "confirm_delete":

        course_code = data[1]
        category = data[2]
        idx = int(data[3])

        try:

            deleted_resource = all_data["courses"][course_code]["categories"][category].pop(idx)

            save_data(all_data)

            kb = InlineKeyboardMarkup(row_width=2)

            kb.add(

                InlineKeyboardButton(
                    "⬅ Back",
                    callback_data=f"manage_category|{course_code}|{category}"
                ),

                InlineKeyboardButton(
                    "🏠 Home",
                    callback_data="home"
                )
            )

            bot.edit_message_text(
                f"""
━━━━━━━━━━━━━━━━━━
✅ <b>Resource Deleted Successfully</b>

🗑 <b>{deleted_resource['title']}</b>

━━━━━━━━━━━━━━━━━━
""",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=kb
            )

        except:

            bot.answer_callback_query(
                call.id,
                "❌ Failed to delete resource."
            )


# ================= ADD NOTES =================
    elif data[0] == "add_notes":

        kb = InlineKeyboardMarkup(row_width=2)

        kb.add(

            InlineKeyboardButton(
                "⬅ Back",
                callback_data="manage_add"
            ),

            InlineKeyboardButton(
                "🏠 Home",
                callback_data="home"
            )
        )

        bot.edit_message_text(
            """
━━━━━━━━━━━━━━━━━━
📄 <b>ADD NOTES</b>

Upload file with caption:

/course compiler_design
/category notes
/title Chapter 1 Notes

━━━━━━━━━━━━━━━━━━
""",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=kb
        )

    # ================= ADD BOOKS =================
    elif data[0] == "add_books":

        kb = InlineKeyboardMarkup(row_width=2)

        kb.add(

            InlineKeyboardButton(
                "⬅ Back",
                callback_data="manage_add"
            ),

            InlineKeyboardButton(
                "🏠 Home",
                callback_data="home"
            )
        )

        bot.edit_message_text(
            """
━━━━━━━━━━━━━━━━━━
📚 <b>ADD BOOKS</b>

Upload file with caption:

/course compiler_design
/category books
/title DBMS Book

━━━━━━━━━━━━━━━━━━
""",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=kb
        )

    # ================= ADD LECTURE NOTES =================
    elif data[0] == "add_lecture_notes":

        kb = InlineKeyboardMarkup(row_width=2)

        kb.add(

            InlineKeyboardButton(
                "⬅ Back",
                callback_data="manage_add"
            ),

            InlineKeyboardButton(
                "🏠 Home",
                callback_data="home"
            )
        )

        bot.edit_message_text(
            """
━━━━━━━━━━━━━━━━━━
🧠 <b>ADD LECTURE NOTES</b>

Upload file with caption:

/course compiler_design
/category lecture_notes
/title Syntax Analysis

━━━━━━━━━━━━━━━━━━
""",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=kb
        )

      # ================= ADD VIDEO LINK =================
    elif data[0] == "add_video_link":

        UPLOAD_STATE[call.from_user.id] = {
            "type": "video"
        }

        kb = InlineKeyboardMarkup(row_width=2)

        kb.add(

            InlineKeyboardButton(
                "⬅ Back",
                callback_data="manage_add"
            ),

            InlineKeyboardButton(
                "🏠 Home",
                callback_data="home"
            )
        )

        bot.edit_message_text(
            """
━━━━━━━━━━━━━━━━━━
🎥 <b>ADD VIDEO LINK</b>

Send format:

course|title|url

Example:

compiler_design|Parsing Tutorial|https://youtube.com/...

━━━━━━━━━━━━━━━━━━
""",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=kb
        )

    # ================= ADD PLAYLIST LINK =================
    elif data[0] == "add_playlist_link":

        UPLOAD_STATE[call.from_user.id] = {
            "type": "playlist"
        }

        kb = InlineKeyboardMarkup(row_width=2)

        kb.add(

            InlineKeyboardButton(
                "⬅ Back",
                callback_data="manage_add"
            ),

            InlineKeyboardButton(
                "🏠 Home",
                callback_data="home"
            )
        )

        bot.edit_message_text(
            """
━━━━━━━━━━━━━━━━━━
📺 <b>ADD PLAYLIST LINK</b>

Send format:

course|title|url

Example:

compiler_design|Compiler Playlist|https://youtube.com/playlist?list=...

━━━━━━━━━━━━━━━━━━
""",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=kb
        )


    # ================= HOME =================
    elif data[0] == "home":

        bot.edit_message_text(
            main_header(),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=course_menu()
        )

    # ================= COURSE =================
    elif data[0] == "course":

        course_code = data[1]

        course = all_data["courses"][course_code]

        text = f"""
━━━━━━━━━━━━━━━━━━
{course['emoji']} <b>{course['title']}</b>

📚 Available Resources
━━━━━━━━━━━━━━━━━━
"""

        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=category_menu(course_code)
        )

    # ================= CATEGORY =================
    elif data[0] == "category":

        course_code = data[1]
        category = data[2]

        kb, text = resource_menu(course_code, category)

        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=kb
        )

    # ================= RESOURCE =================
    elif data[0] == "resource":

        course_code = data[1]
        category = data[2]
        idx = int(data[3])

        res = all_data["courses"][course_code]["categories"][category][idx]

        # ================= VIDEOS / PLAYLISTS =================
        if category in ["videos", "playlists"]:

            kb = InlineKeyboardMarkup(row_width=2)

            kb.add(

                InlineKeyboardButton(
                    "▶ Open Link",
                    url=res["url"]
                ),

                InlineKeyboardButton(
                    "🗑 Close",
                    callback_data="delete_popup"
                )
            )

            kb.add(

                InlineKeyboardButton(
                    "⬅ Back",
                    callback_data=f"category|{course_code}|{category}"
                ),

                InlineKeyboardButton(
                    "🏠 Home",
                    callback_data="home"
                )
            )

            bot.send_message(
                call.message.chat.id,
                f"""
━━━━━━━━━━━━━━━━━━
🎬 <b>{res['title']}</b>

🔗 Open resource below
━━━━━━━━━━━━━━━━━━
""",
                reply_markup=kb
            )

        # ================= DOCUMENTS =================
        else:

            kb = InlineKeyboardMarkup(row_width=2)

            kb.add(

                InlineKeyboardButton(
                    "🗑 Close",
                    callback_data="delete_popup"
                ),

                InlineKeyboardButton(
                    "🏠 Home",
                    callback_data="home"
                )
            )

            bot.send_document(
                call.message.chat.id,
                res["file_id"],
                caption=f"""
━━━━━━━━━━━━━━━━━━
📄 <b>{res['title']}</b>

📥 File sent successfully
━━━━━━━━━━━━━━━━━━
""",
                reply_markup=kb
            )

    # ================= DELETE POPUP =================
    elif data[0] == "delete_popup":

        try:

            bot.delete_message(
                call.message.chat.id,
                call.message.message_id
            )

        except:
            pass

    # ================= BACK =================
    elif data[0] == "back":

        if data[1] == "courses":

            bot.edit_message_text(
                main_header(),
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=course_menu()
            )

        elif data[1] == "course":

            course_code = data[2]

            course = all_data["courses"][course_code]

            bot.edit_message_text(
                f"""
━━━━━━━━━━━━━━━━━━
{course['emoji']} <b>{course['title']}</b>

📚 Available Resources
━━━━━━━━━━━━━━━━━━
""",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=category_menu(course_code)
            )

# ================= MAIN =================
if __name__ == "__main__":

    keep_alive()

    print("🚀 StudyHub Pro Running")

    bot.infinity_polling(
        timeout=30,
        long_polling_timeout=30,
        skip_pending=True
    )