# Contributing to First-PR Mentor

Thanks for helping! This project exists to make first contributions easier, so we try to practice what we preach.

## Quick start

1. Fork the repo and clone your fork.
2. Follow the setup steps in the [README](README.md). Tip: use **Demo mode** to work without any API keys.
3. Create a branch: `git checkout -b fix-issue-<number>-<short-slug>`
4. Make a small, focused change and run `streamlit run app.py` to check it.
5. Commit, push, and open a pull request that says what you changed and why. Add `Closes #<issue number>`.

## Good first issue ideas

1. **Add more skills to the picker.** Add `c#`, `ruby` and `php` to the `SKILLS` list in `app.py` and check that the search still works.
2. **Show repo description on issue cards.** `get_repo_info` already returns it; display it under the title in the "Find an Issue" tab.
3. **Add a "Copy all commands" block** in the PR Coach tab that joins every step's command into a single code block.

## Guidelines

- Keep the code simple and briefly commented. No unnecessary abstractions.
- Never commit secrets. `.env` is git-ignored; only edit `.env.example`.
- Be kind. Everyone here was a beginner once.
