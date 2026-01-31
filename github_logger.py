"""
github_logger.py

SMART LOG ROUTER

Responsibilities:
✔ Read buffered logs
✔ Detect category
✔ Route to correct files
✔ Maintain Markdown + TXT
✔ Use EVENT timestamps (not system time)
✔ Prevent duplicate headers
✔ Prevent data loss
✔ Human-readable Markdown
✔ AI-friendly TXT logs
"""

from github import Github
from config import GITHUB_TOKEN, GITHUB_REPO, GITHUB_BRANCH
from buffer import read_buffer, clear_buffer
from datetime import datetime


# -----------------------------------------
# FILE ROUTING MAP
# -----------------------------------------

FILE_MAP = {
    "DAILY": ("daily.md", "daily.txt"),
    "ACHIEVEMENT": ("achievements.md", "achievements.txt"),
    "FAILURE": ("failures.md", "failures.txt"),
}


# -----------------------------------------
# TIME FORMATTER (HUMAN FRIENDLY)
# -----------------------------------------

def human_time(iso_timestamp: str):
    """
    Converts ISO timestamp into beautiful human-readable time.

    Example:
    Saturday, 31 January 2026 | 04:42 PM
    """

    dt = datetime.fromisoformat(iso_timestamp)

    readable = dt.strftime("%A, %d %B %Y | %I:%M %p")
    header = dt.strftime("## 📅 %d %B %Y (%A)")

    return header, readable


# -----------------------------------------
# MARKDOWN FORMATTER
# -----------------------------------------

def format_markdown(category, timestamp, message):
    """
    Converts raw log into human-readable markdown.
    ALWAYS uses the event timestamp.
    """

    date_header, readable_time = human_time(timestamp)

    if category == "DAILY":

        md_line = (
            f"🕒 **{readable_time}**\n"
            f"- {message}\n\n"
        )

    elif category == "ACHIEVEMENT":

        md_line = (
            f"🏆 **Achievement — {readable_time}**\n\n"
            f"{message}\n\n"
        )

    elif category == "FAILURE":

        md_line = (
            f"⚠️ **Failure — {readable_time}**\n\n"
            f"{message}\n\n"
        )

    else:

        md_line = (
            f"🕒 **{readable_time}**\n"
            f"- {message}\n\n"
        )

    return date_header, md_line


# -----------------------------------------
# SAFE FILE WRITER
# -----------------------------------------

def update_file(repo, file_path, content, commit_msg):
    """
    Safely updates OR creates a GitHub file.
    """

    try:

        file = repo.get_contents(file_path, ref=GITHUB_BRANCH)

        existing = file.decoded_content.decode()

        updated = existing + content

        repo.update_file(
            path=file_path,
            message=commit_msg,
            content=updated,
            sha=file.sha,
            branch=GITHUB_BRANCH
        )

        return existing

    except Exception:
        # File doesn't exist yet

        repo.create_file(
            path=file_path,
            message=commit_msg,
            content=content,
            branch=GITHUB_BRANCH
        )

        return ""


# -----------------------------------------
# MAIN COMMIT ENGINE
# -----------------------------------------

def commit_buffer():

    content = read_buffer()

    if not content.strip():
        print("🟡 No logs to commit.")
        return 0

    try:

        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)

        lines = content.strip().split("\n")

        # Group logs by category
        grouped_logs = {
            "DAILY": [],
            "ACHIEVEMENT": [],
            "FAILURE": [],
        }

        # ---------------------------------
        # PARSE BUFFER
        # ---------------------------------

        for line in lines:

            try:
                timestamp, category, message = line.split(" || ", 2)

                if category not in grouped_logs:
                    print("⚠️ Unknown category:", category)
                    continue

                grouped_logs[category].append((timestamp, message))

            except ValueError:
                print("⚠️ Skipping malformed log:", line)

        total_entries = 0

        # ---------------------------------
        # PROCESS EACH CATEGORY
        # ---------------------------------

        for category, logs in grouped_logs.items():

            if not logs:
                continue

            md_file, txt_file = FILE_MAP[category]

            md_content = ""
            txt_content = ""

            # Read existing markdown once
            try:
                file = repo.get_contents(md_file, ref=GITHUB_BRANCH)
                existing_md = file.decoded_content.decode()
            except Exception:
                existing_md = ""

            for timestamp, message in logs:

                date_header, md_line = format_markdown(
                    category,
                    timestamp,
                    message
                )

                # Prevent duplicate headers
                if (
                    date_header not in existing_md
                    and date_header not in md_content
                ):
                    md_content += f"\n\n{date_header}\n\n"

                md_content += md_line

                # AI-friendly TXT (DO NOT beautify)
                txt_content += f"{timestamp} || {category} || {message}\n"

            entry_count = len(logs)
            total_entries += entry_count

            commit_time = datetime.now().strftime("%H:%M")

            md_commit_msg = (
                f"log({category.lower()}): "
                f"{entry_count} entries @ {commit_time}"
            )

            txt_commit_msg = (
                f"raw({category.lower()}): "
                f"{entry_count} entries @ {commit_time}"
            )

            update_file(repo, md_file, md_content, md_commit_msg)
            update_file(repo, txt_file, txt_content, txt_commit_msg)

        # ---------------------------------
        # CLEAR BUFFER ONLY AFTER SUCCESS
        # ---------------------------------

        clear_buffer()

        print(f"✅ Smart commit successful. ({total_entries} entries)")

        return total_entries

    except Exception as e:

        print("❌ GitHub commit failed.")
        print(e)

        return 0