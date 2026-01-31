from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import threading
import schedule
import time

from config import TELEGRAM_TOKEN, OWNER_ID
from security import is_owner
from buffer import (
    add_daily_log,
    add_achievement,
    add_failure,
    read_buffer
)
from github_logger import commit_buffer
from search_engine import search_logs
from export_engine import export_data
from ai_engine import generate_daily_summary


# =====================================================
# SIMPLE IN-MEMORY HISTORY (last messages)
# =====================================================
history = []


# =====================================================
# KEYBOARDS
# =====================================================

def home_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Daily Log", callback_data="daily")],
        [InlineKeyboardButton("🏆 Achievement", callback_data="achievement")],
        [InlineKeyboardButton("⚠️ Failure", callback_data="failure")],
        [InlineKeyboardButton("🔎 Search Logs", callback_data="search")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats")],
        [InlineKeyboardButton("🚀 Commit Now", callback_data="commit")],
    ])


def back_home_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Back to Home", callback_data="home")]
    ])


# =====================================================
# START / HOME
# =====================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Unauthorized.")
        return

    await show_home(update, context)


async def show_home(update, context):
    text = (
        "🧠 *Life Logger*\n\n"
        "Your private life operating system.\n\n"
        "• Log your days\n"
        "• Record achievements\n"
        "• Learn from failures\n"
        "• Search your past\n"
        "• Track consistency\n\n"
        "_Everything you log becomes future intelligence._"
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=home_keyboard()
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=home_keyboard()
        )


# =====================================================
# BUTTON HANDLER
# =====================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_owner(query.from_user.id):
        await query.edit_message_text("❌ Unauthorized.")
        return

    context.user_data.clear()
    action = query.data

    if action == "home":
        await show_home(update, context)

    elif action == "daily":
        context.user_data["state"] = "daily"
        await query.edit_message_text(
            "📝 *Daily Log*\n\nSend anything you want to record.",
            parse_mode="Markdown",
            reply_markup=back_home_keyboard()
        )

    elif action == "achievement":
        context.user_data["state"] = "ach_title"
        await query.edit_message_text(
            "🏆 *Achievement*\n\nSend the TITLE:",
            parse_mode="Markdown",
            reply_markup=back_home_keyboard()
        )

    elif action == "failure":
        context.user_data["state"] = "fail_title"
        await query.edit_message_text(
            "⚠️ *Failure*\n\nSend a short TITLE:",
            parse_mode="Markdown",
            reply_markup=back_home_keyboard()
        )

    elif action == "search":
        context.user_data["state"] = "search"
        await query.edit_message_text(
            "🔎 *Search Logs*\n\nSend a keyword to search your life history.",
            parse_mode="Markdown",
            reply_markup=back_home_keyboard()
        )

    elif action == "stats":
        await send_stats(update, context)

    elif action == "commit":
        count = commit_buffer()
        await query.edit_message_text(
            f"🚀 Commit Complete\n\n✅ {count} entries saved.",
            reply_markup=home_keyboard()
        )


# =====================================================
# MESSAGE HANDLER (STATE MACHINE)
# =====================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return

    text = update.message.text.strip()
    state = context.user_data.get("state")

    history.append(text)
    if len(history) > 5:
        history.pop(0)

    try:
        # DAILY
        if state == "daily":
            add_daily_log(text)
            await update.message.reply_text(
                "✅ Logged.",
                reply_markup=home_keyboard()
            )

        # ACHIEVEMENT FLOW
        elif state == "ach_title":
            context.user_data["title"] = text
            context.user_data["state"] = "ach_desc"
            await update.message.reply_text("Describe it:")

        elif state == "ach_desc":
            context.user_data["desc"] = text
            context.user_data["state"] = "ach_how"
            await update.message.reply_text("How did you achieve it?")

        elif state == "ach_how":
            add_achievement(
                context.user_data["title"],
                context.user_data["desc"],
                text
            )
            await update.message.reply_text(
                "🏆 Achievement saved.",
                reply_markup=home_keyboard()
            )

        # FAILURE FLOW
        elif state == "fail_title":
            context.user_data["title"] = text
            context.user_data["state"] = "fail_reason"
            await update.message.reply_text("What caused it?")

        elif state == "fail_reason":
            context.user_data["reason"] = text
            context.user_data["state"] = "fail_lesson"
            await update.message.reply_text("What did you learn?")

        elif state == "fail_lesson":
            add_failure(
                context.user_data["title"],
                context.user_data["reason"],
                text
            )
            await update.message.reply_text(
                "⚠️ Failure logged.",
                reply_markup=home_keyboard()
            )

        # SEARCH
        elif state == "search":
            results = search_logs(text)
            if not results:
                msg = "No results found."
            else:
                msg = "\n".join(results[:10])

            await update.message.reply_text(
                f"🔎 Results:\n\n{msg}",
                reply_markup=home_keyboard()
            )

        else:
            await update.message.reply_text(
                "Choose an option from the menu 👇",
                reply_markup=home_keyboard()
            )

    except Exception as e:
        await update.message.reply_text(
            "❌ Something went wrong.\nYour data is safe.",
            reply_markup=home_keyboard()
        )
        print(e)


# =====================================================
# STATS
# =====================================================

async def send_stats(update, context):
    buffer_data = read_buffer()
    lines = buffer_data.split("\n") if buffer_data else []

    daily = sum(1 for l in lines if "|| DAILY ||" in l)
    ach = sum(1 for l in lines if "|| ACHIEVEMENT ||" in l)
    fail = sum(1 for l in lines if "|| FAILURE ||" in l)

    text = (
        "📊 *Stats (Buffer)*\n\n"
        f"📝 Daily: {daily}\n"
        f"🏆 Achievements: {ach}\n"
        f"⚠️ Failures: {fail}\n\n"
        "_Auto-commit runs every 6 hours._"
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=home_keyboard()
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=home_keyboard()
        )


# =====================================================
# AUTO COMMIT SCHEDULER
# =====================================================

def scheduler_loop(app):
    def auto_commit():
        count = commit_buffer()
        if count > 0:
            app.bot.send_message(
                chat_id=OWNER_ID,
                text=f"🤖 Auto-Commit Done\n\n✅ {count} logs saved."
            )

    schedule.every(6).hours.do(auto_commit)

    while True:
        schedule.run_pending()
        time.sleep(30)


async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_owner(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text(
            "Usage:\n\n"
            "/export daily\n"
            "/export achievements\n"
            "/export failures\n"
            "/export all"
        )
        return

    category = context.args[0].lower()

    data = export_data(category)

    if not data:
        await update.message.reply_text("Invalid category.")
        return

    # Telegram prefers files for large text
    with open("export.txt", "w", encoding="utf-8") as f:
        f.write(data)

    await update.message.reply_document(
        document=open("export.txt", "rb"),
        filename=f"{category}_export.txt"
    )


# =====================================================
# MAIN
# =====================================================

def main():
    print("🚀 Life Logger starting...")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", send_stats))
    app.add_handler(CommandHandler("search", handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("export", export_command))
    
    threading.Thread(
        target=scheduler_loop,
        args=(app,),
        daemon=True
    ).start()

    print("✅ Bot running.")
    app.run_polling()


if __name__ == "__main__":
    main()