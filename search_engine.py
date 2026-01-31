from github import Github
from config import GITHUB_TOKEN, GITHUB_REPO, GITHUB_BRANCH


FILES_TO_SEARCH = [
    "daily.txt",
    "achievements.txt",
    "failures.txt",
]


def search_logs(keyword, limit=10):

    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)

    keyword = keyword.lower()

    matches = []

    for file_name in FILES_TO_SEARCH:

        try:
            file = repo.get_contents(file_name, ref=GITHUB_BRANCH)
            content = file.decoded_content.decode()

            lines = content.split("\n")

            for line in lines:
                if keyword in line.lower():
                    matches.append(line)

        except Exception:
            continue

    matches.reverse()

    return matches[:limit]