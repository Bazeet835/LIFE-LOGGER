from datetime import datetime
from github import Github
from config import GITHUB_TOKEN, GITHUB_REPO, GITHUB_BRANCH


def generate_daily_summary():

    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)

    today = datetime.now().strftime("%Y-%m-%d")

    counts = {
        "daily": 0,
        "achievements": 0,
        "failures": 0
    }

    files = {
        "daily": "daily.txt",
        "achievements": "achievements.txt",
        "failures": "failures.txt"
    }

    for key, file_name in files.items():

        try:
            file = repo.get_contents(file_name, ref=GITHUB_BRANCH)
            lines = file.decoded_content.decode().split("\n")

            for line in lines:
                if today in line:
                    counts[key] += 1

        except:
            pass

    total = sum(counts.values())

    if total == 0:
        return "No logs today. Every great system starts with consistency 🙂"

    summary = f"""
🧠 Daily Intelligence Report

📅 {today}

📝 Daily Logs: {counts['daily']}
🏆 Achievements: {counts['achievements']}
⚠️ Failures: {counts['failures']}

Total Events: {total}

Keep showing up. Consistency compounds.
"""

    return summary