"""
buffer.py

Acts as TEMPORARY MEMORY before committing to GitHub.

Supports THREE channels:

✔ daily
✔ achievement
✔ failure

Design Goal:
- Safe
- Structured
- AI-friendly
"""

import os
from datetime import datetime
from config import BUFFER_FILE


# Ensure buffer exists
if not os.path.exists(BUFFER_FILE):
    open(BUFFER_FILE, "w", encoding="utf-8").close()


def build_log_line(category: str, message: str):
    """
    Creates a structured log entry.

    Format (AI friendly):
    ISO_TIMESTAMP || CATEGORY || MESSAGE
    """

    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    return f"{timestamp} || {category} || {message}\n"


def add_daily_log(message: str):
    """Adds a normal daily entry."""

    if not message.strip():
        return

    log_line = build_log_line("DAILY", message)

    with open(BUFFER_FILE, "a", encoding="utf-8") as file:
        file.write(log_line)


def add_achievement(title: str, description: str, how: str):
    """
    Adds a rich achievement entry.

    Stored in one line for AI parsing.
    """

    combined = f"{title} >> {description} >> HOW:{how}"

    log_line = build_log_line("ACHIEVEMENT", combined)

    with open(BUFFER_FILE, "a", encoding="utf-8") as file:
        file.write(log_line)


def add_failure(title: str, reason: str, lesson: str):
    """
    Logs failures with learning data.
    This becomes EXTREMELY valuable later.
    """

    combined = f"{title} >> {reason} >> LESSON:{lesson}"

    log_line = build_log_line("FAILURE", combined)

    with open(BUFFER_FILE, "a", encoding="utf-8") as file:
        file.write(log_line)


def read_buffer():
    try:
        with open(BUFFER_FILE, "r", encoding="utf-8") as file:
            return file.read()

    except FileNotFoundError:
        return ""


def clear_buffer():
    """Clears buffer AFTER successful commit."""
    open(BUFFER_FILE, "w", encoding="utf-8").close()