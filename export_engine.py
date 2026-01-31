from github import Github
from config import GITHUB_TOKEN, GITHUB_REPO, GITHUB_BRANCH


FILES = {
    "daily": "daily.txt",
    "achievements": "achievements.txt",
    "failures": "failures.txt",
}


def fetch_file_content(file_name):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)

    try:
        file = repo.get_contents(file_name, ref=GITHUB_BRANCH)
        return file.decoded_content.decode()

    except Exception:
        return "No data available yet."


def export_data(category):

    if category == "all":

        combined = ""

        for name in FILES.values():
            combined += f"\n===== {name.upper()} =====\n"
            combined += fetch_file_content(name)

        return combined

    if category in FILES:
        return fetch_file_content(FILES[category])

    return None