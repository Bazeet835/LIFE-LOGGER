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
# MARKDOWN FORMATTER
# -----------------------------------------

def format_markdown(category, timestamp, message):
    """
    Converts raw log into human-readable markdown.
    Uses the LOG timestamp — never datetime.now()
    """

    date_obj = datetime.fromisoformat(timestamp)
    date_header = date_obj.strftime("## 📅 %B %d, %Y")

    if category == "DAILY":
        md_line = f"- {timestamp} | {message}\n"

    elif category == "ACHIEVEMENT":
        md_line = f"🏆 **{timestamp}**\n\n{message}\n\n"

    elif category == "FAILURE":
        md_line = f"⚠️ **{timestamp}**\n\n{message}\n\n"

    else:
        md_line = f"- {timestamp} | {message}\n"

    return date_header, md_line


# -----------------------------------------
# SAFE FILE WRITER
# -----------------------------------------

def update_file(repo, file_path, content, commit_msg):
    """
    Safely updates OR creates a GitHub file.
    Returns existing content for header checks.
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
        return 0   # return count for bot notification

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

        for line in lines:

            try:
                timestamp, category, message = line.split(" || ", 2)
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

            # Get existing markdown ONCE
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

        # 🔥 CLEAR ONLY AFTER SUCCESS
        clear_buffer()

        print(f"✅ Smart commit successful. ({total_entries} entries)")

        return total_entries

    except Exception as e:

        print("❌ GitHub commit failed.")
        print(e)

        return 0