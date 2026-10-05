# PR-mentor# 🌱 First-PR Mentor
First-PR Mentor
From "I want to contribute" to your first PR.
Show Image Show Image Show Image Show Image
Built for Hacktoberfest Hack Day Chennai (VIT Chennai), Best Open-Source AI Project track.
Show Image
The problem
Millions of students want to contribute to open source, but most never make a first pull request because:
They don't know where to start. Which project? Which issue?
They can't understand the code. Even a "good first issue" can feel like reading another language.
They fear making mistakes. Forks, branches, commits, PR templates... one wrong step feels public and permanent.
Existing tools only list "good first issues". They stop right where the hard part begins.
The solution
First-PR Mentor finds issues that match your skills, explains the issue and the code in simple words, shows which files to open, summarizes the repo's rules, and walks you step by step to a real pull request, with a ready-to-paste PR title and description.
Open-weight AI
The AI is the heart of First-PR Mentor, and it runs on open-weight models, so no paid API is needed.
Default model: Llama 3.1 8B, run locally through Ollama.
What the model does: explains the issue in plain words (with difficulty, time and beginner scores), picks the most relevant files, summarizes the repo's CONTRIBUTING.md into five rules, and drafts the PR title and description.
Safe by design: the model may only choose files from the repo's real file tree, so it cannot invent paths.
Bring your own model: any OpenAI-compatible endpoint works (Ollama, Groq, OpenRouter, ...). It is switched with three environment variables, LLM_BASE_URL, LLM_API_KEY and LLM_MODEL. No code changes needed.
The whole project is open source under the MIT license.
Features
🔎 Skill-matched issue finder: ranks fresh, unassigned "good first issue"s by your skills, repo popularity, recent activity, and how small the issue is
💡 Plain-language explanation with difficulty, time estimate and beginner-friendliness score
📊 Issue snapshot: a radar chart and score list that show at a glance how approachable an issue is
📂 "Where to look": likely files with reasons (never invented: paths must come from the repo's real file tree)
📜 Repo rules in 5 bullets from CONTRIBUTING.md
🧭 PR Coach: checklist from fork to pull request with copy-paste commands, a progress ring and bar, and steps that turn green when done
✍️ Auto-drafted PR title and description following the repo's rules
🎬 Demo mode: runs entirely offline from sample data, so demos never break
🔌 Any LLM: local Ollama or a hosted API, switched with environment variables
Screenshots
Understand an issue	PR Coach
Show Image	Show Image
How it works

Pick your skills
GitHub search: good firstissues
Rank and show issue cards
Use this issue
Fetch issue, repo info, filetree, CONTRIBUTING.md
Find relevant files bykeywords
Open-weight LLM: explainissue, where to change, reporules, PR draft
PR Coach: fork, clone,branch, change, test,commit, push, PR
Your first pull request 🎉
Tech stack
Python 3.10+, Streamlit UI
GitHub REST API via requests
LLM via the OpenAI-compatible openai client, defaulting to Llama 3.1 8B on Ollama
python-dotenv for secrets
Setup
bash
# 1. Clone
git clone https://github.com/<your-username>/first-pr-mentor.git
cd first-pr-mentor

# 2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
cp .env.example .env             # Windows: copy .env.example .env
# then edit .env: add your GITHUB_TOKEN (optional but recommended)

# 5. Run
streamlit run app.py
Local open-weight LLM (free): install Ollama, run ollama pull llama3.1:8b, and keep the defaults in .env.example. Hosted LLM (optional): set LLM_BASE_URL, LLM_API_KEY and LLM_MODEL to your provider's values.
Secrets live only in .env (which is git-ignored). The app never prints or logs tokens.
Usage
Find an Issue: choose your skills, click Find issues, then Use this issue.
Understand an Issue: click Analyze to get the explanation, snapshot, files to look at, and repo rules.
PR Coach: enter your GitHub username and tick off each step until your PR is open.
No setup yet? Tick Demo mode in the sidebar, or click Try an example, to see everything with sample data.
Project structure
app.py             Streamlit UI (three tabs)
coach.py           Step-by-step PR plan
github_client.py   GitHub API client and issue ranking
llm.py             OpenAI-compatible LLM client
prompts.py         Prompts for the open-weight model
demo_data.json     Sample data for Demo mode
.streamlit/        Theme settings
docs/              Screenshots
Demo
Video: (add your demo video link here)
Roadmap
 Search by topic and project size, not just language
 Look inside file contents (not only paths) to find relevant code
 Check your fork's progress automatically via the GitHub API
 Review your diff before you open the PR
 Multi-language explanations
Contributing
We're beginner-friendly! See CONTRIBUTING.md.
Team
Naveenkumar M, Smirthy S, Lakshitha A, Jai Krishna V
License
MIT

