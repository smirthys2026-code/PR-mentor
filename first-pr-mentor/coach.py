"""PR Coach: ordered, beginner-friendly steps from fork to pull request."""
import re


def make_slug(title, max_words=4):
    words = re.findall(r"[a-z0-9]+", title.lower())
    return "-".join(words[:max_words]) or "change"


def generate_steps(owner, repo, issue_number, issue_title, default_branch, github_username):
    """Return a list of {title, explanation, command, link, link_label}."""
    user = (github_username or "").strip() or "YOUR-USERNAME"
    branch = f"fix-issue-{issue_number}-{make_slug(issue_title)}"
    safe_title = re.sub(r'["`$\\]', "", issue_title).strip()  # keeps the commit command safe to paste
    return [
        {
            "title": "Fork the repository",
            "explanation": "A fork is your own copy of the project on GitHub, where you're allowed to make changes.",
            "command": None,
            "link": f"https://github.com/{owner}/{repo}/fork",
            "link_label": "Open the fork page",
        },
        {
            "title": "Clone your fork",
            "explanation": "This downloads your copy to your computer; the last line links the original project as 'upstream'.",
            "command": f"git clone https://github.com/{user}/{repo}.git\ncd {repo}\ngit remote add upstream https://github.com/{owner}/{repo}.git",
        },
        {
            "title": "Create a branch",
            "explanation": "A branch keeps your work separate from the main code, so mistakes are easy to undo.",
            "command": f"git checkout -b {branch}",
        },
        {
            "title": "Make the change",
            "explanation": "Open the files from the 'Where to look' card, make the smallest change that solves the issue, and save.",
            "command": None,
        },
        {
            "title": "Run the tests (if the project has any)",
            "explanation": "Tests check that nothing broke; use the test command from the repo rules, or skip if there are none.",
            "command": None,
        },
        {
            "title": "Commit your change",
            "explanation": "A commit saves a snapshot of your work with a short message describing it.",
            "command": f'git add .\ngit commit -m "Fix #{issue_number}: {safe_title}"',
        },
        {
            "title": "Push your branch",
            "explanation": "This uploads your branch to your fork on GitHub.",
            "command": f"git push origin {branch}",
        },
        {
            "title": "Open the pull request",
            "explanation": "A pull request asks the maintainers to review your change. Paste the draft below into the form.",
            "command": None,
            "link": f"https://github.com/{owner}/{repo}/compare/{default_branch}...{user}:{branch}?expand=1",
            "link_label": "Open the pull request page",
        },
    ]
