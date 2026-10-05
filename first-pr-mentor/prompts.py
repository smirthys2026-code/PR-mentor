"""Prompt builders. Each returns (system, user) for llm.chat_json."""

MAX_FILE_CHARS = 2500  # per file in the prompt, keeps small local models happy

RULES = (
    "You are a friendly mentor helping a complete beginner make their first open source contribution. "
    "Explain in simple words, with no jargon (briefly explain any term you must use). "
    "Use ONLY the text provided by the user message. Never invent files, functions, or code that are not in it. "
    "Return JSON only, with no markdown fences and no extra text, in exactly this shape:\n"
)


def _issue_text(issue):
    comments = "\n".join(f"- {c['author']}: {c['body']}" for c in issue.get("comments", [])) or "(none)"
    return (
        f"ISSUE #{issue['number']}: {issue['title']}\n"
        f"Labels: {', '.join(issue.get('labels', [])) or '(none)'}\n"
        f"Body:\n{issue['body'][:3000] or '(empty)'}\n"
        f"First comments:\n{comments}\n"
    )


def explain_issue(issue, repo_info):
    system = RULES + (
        '{"simple_explanation": "2-4 plain sentences", "what_success_looks_like": "1-2 sentences", '
        '"difficulty": 3, "estimated_minutes": 45, "beginner_friendly_score": 8}\n'
        "difficulty and beginner_friendly_score are integers from 1 to 10; estimated_minutes is an integer."
    )
    user = (
        f"Repo description: {repo_info.get('description') or '(none)'}\n"
        f"Main language: {repo_info.get('language') or '(unknown)'}\n\n" + _issue_text(issue)
    )
    return system, user


def where_to_change(issue, files):
    """files: list of {"path", "content"} for the top candidate files."""
    system = RULES + (
        '{"files": [{"path": "src/example.py", "reason": "why this file matters", '
        '"what_to_look_for": "what to search for inside it, in simple words"}]}\n'
        "Every path MUST be copied exactly from the candidate list. Pick only the files that really matter (1 to 5)."
    )
    candidates = "\n".join(f.get("path", "") for f in files)
    blocks = "\n\n".join(f"=== {f['path']} ===\n{f['content'][:MAX_FILE_CHARS]}" for f in files)
    user = _issue_text(issue) + f"\nCANDIDATE FILES (only these paths are allowed):\n{candidates}\n\nFILE CONTENTS:\n{blocks}"
    return system, user


def pr_draft(issue, contributing_text):
    system = RULES + (
        '{"title": "Short imperative PR title", "description": "markdown text"}\n'
        "The description must contain these sections in this order: '## What I changed', '## Why', "
        f"'## How I tested', and a last line 'Closes #{issue['number']}'. "
        "The student has not made the change yet, so write the draft from the issue and put short [bracketed placeholders] "
        "where they must fill in specifics. Follow the repo's contributing rules for title style and checklist items if given. "
        "Use \\n for new lines inside the JSON string."
    )
    rules = (contributing_text or "(this repo has no CONTRIBUTING.md)")[:3000]
    return system, _issue_text(issue) + f"\nREPO CONTRIBUTING RULES:\n{rules}"


def contributing_summary(contributing_text):
    system = RULES + (
        '{"bullets": ["rule 1", "rule 2", "rule 3", "rule 4", "rule 5"], "must_do_before_pr": ["thing to do first"]}\n'
        "bullets must contain exactly 5 short strings. must_do_before_pr lists concrete things to do before opening a PR "
        "(may be an empty list if the text names none)."
    )
    return system, f"CONTRIBUTING.md TEXT:\n{contributing_text[:6000]}"
