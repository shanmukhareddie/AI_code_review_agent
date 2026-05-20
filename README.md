# AI Code Review Agent

Paste a public GitHub repo URL. The agent clones it, reads every function and class, and gives you structured feedback — with severity levels, categories, and confidence scores.

Supports **Python** and **Java** repositories.

Live app: [https://ai-code-review-agents.streamlit.app/](https://ai-code-review-agents.streamlit.app/)
Demo Video: [https://www.loom.com/share/6a8e335b47894d1f9ff6f94cebf8cb80](https://www.loom.com/share/6a8e335b47894d1f9ff6f94cebf8cb80)
---

## What it does

1. You paste a public GitHub repo URL
2. The agent clones the repo and finds all `.py` and `.java` files
3. It extracts every function and class as a separate chunk
4. Each chunk is sent to an LLM (Groq) for review
5. The results are shown in a dashboard with filters, confidence scores, and export options
6. (Bonus) You can post the review directly to a GitHub Pull Request

Each review comment tells you:
- **What the issue is** (e.g. "Division by zero")
- **How serious it is** — Critical / Warning / Suggestion
- **What type of problem** — Bug / Security / Performance / Readability / Style
- **How confident the AI is** — 0 to 100% (higher = more certain)
- **Where it is** — which file, function, and line number
- **Language** — Python or Java

Comments below 50% confidence go into a separate "Verify This" tab so you know not to trust them blindly.
NOTE: Each LLM is may provide different confidences

---

## Tech stack

| Tool | What it does |
|---|---|
| Streamlit | Web dashboard UI |
| GitPython | Clones the GitHub repo |
| Python `ast` module | Parses Python files into functions and classes |
| Regex + brace matching | Parses Java files into methods and classes |
| Groq API (`llama-3.3-70b-versatile`) | LLM that reviews each chunk |
| PyGithub | Posts review comments to GitHub Pull Requests |

Groq is used instead of OpenAI/Claude because it has a free tier with strong output quality.

---

## Project structure

```
AI_code_review_agent/
├── agent/
│   ├── ingestion.py      # Clones the repo, collects .py and .java files
│   ├── parser.py         # Extracts functions and classes from each file
│   ├── reviewer.py       # Sends each chunk to the LLM and gets back comments
│   ├── pipeline.py       # Runs all steps in order
│   └── github_poster.py  # Posts review results to a GitHub Pull Request
├── app.py                # Streamlit UI
├── requirements.txt
├── .env                  # Your API key (never committed)
└── README.md
```

---

## How to run locally

**1. Clone this repo**
```bash
git clone https://github.com/shanmukhareddie/AI_code_review_agent.git
cd AI_code_review_agent
```

**2. Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Add your Groq API key**

Create a `.env` file:
```
GROQ_API_KEY= paste_your_groq_api_key_here
```
Get a free key at [console.groq.com](https://console.groq.com)

**5. Run the app**
```bash
streamlit run app.py
```

---

## How to use

1. Paste a public GitHub repo URL (e.g. `https://github.com/psf/requests`)
2. Adjust the two sliders:
   - **Max functions/classes to review** — how many chunks to send to the LLM
   - **Max lines per function/class** — chunks longer than this are skipped
3. Click **Start Review**
4. Use the filters to focus on what matters (e.g. critical bugs only)
5. Download results as JSON or CSV
6. (Optional) Paste a PR URL + GitHub token to post results directly to a Pull Request

---

## Settings explained

| Setting | Default | What it means |
|---|---|---|
| Max functions/classes to review | 20 | How many chunks get sent to the LLM. Higher = more thorough but slower. |
| Max lines per function/class | 100 | Chunks larger than this are skipped. Higher = bigger functions reviewed. |

---

## How to get a GitHub token (for PR posting)

1. Go to [github.com/settings/tokens](https://github.com/settings/tokens/new?scopes=repo&description=AI+Code+Review+Agent)
2. Check the `repo` checkbox
3. Click **Generate token**
4. Paste it into the app — it is never stored anywhere

---

## Architecture

```
User pastes GitHub URL
        |
        v
ingestion.py   →  clones repo, finds .py and .java files
        |
        v
parser.py      →  Python: uses AST  |  Java: uses regex + brace matching
                   extracts functions and classes as chunks
        |
        v
reviewer.py    →  sends each chunk to Groq LLM, gets JSON comments back
        |
        v
pipeline.py    →  runs all steps, returns flat list of comments
        |
        v
app.py         →  shows results with filters, confidence scores, export
        |
        v
github_poster.py  →  posts review as a comment on a GitHub PR
```

---

## Limitations

- Only public repositories are supported (no authentication)
- Functions/classes longer than the configured line limit are skipped
- Only `.py` and `.java` files are parsed — other languages are ignored
- Java parsing uses regex, not a full AST — very unusual Java syntax may be missed
- The Groq free tier has rate limits — very large repos may hit them
