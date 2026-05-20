# AI Code Review Agent

A tool that takes any public Python or Java GitHub repository, reads through the code, and gives you structured feedback — flagging bugs, security issues, and style problems, each with a confidence score so you know how much to trust the comment.

---

## What It Does

You paste a GitHub URL. The agent clones the repo, walks through every function and class, sends each one to an LLM, and collects all the review comments into a dashboard. Each comment tells you:

- What the issue is
- How serious it is (critical / warning / suggestion)
- What category it falls under (bug, security, performance, readability, style)
- How confident the agent is (0–100%)
- Which file and function it came from
- Which language the file is written in (Python or Java)

Comments below 50% confidence are separated into a "Verify This" section — because not every LLM output should be trusted blindly.

NOTE: confidence scores depend on the LLM used, so they vary.

---

## Tech Stack

- **GitPython** — clones the repo locally
- **Python `ast` module** — parses Python source files into functions and classes without running the code
- **Regex + brace matching** — parses Java source files to extract classes and methods
- **Groq API (llama-3.3-70b-versatile)** — the LLM that reviews each chunk. Used instead of GPT-4o-mini/Claude because Groq offers a free tier with comparable output quality

---

## Project Structure

```
AI_code_review_agent/
├── agent/
│   ├── __init__.py
│   ├── ingestion.py     # Clones the repo, returns list of .py and .java files
│   ├── parser.py        # Parses Python (AST) and Java (regex) — extracts functions and classes
│   ├── reviewer.py      # Sends each chunk to LLM, returns structured comments
│   └── pipeline.py      # Orchestrates the full flow end to end
├── app.py               # Streamlit dashboard
├── .env                 # API keys (never committed)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## How to Run Locally

**1. Clone this repo**
```bash
git clone https://github.com/shanmukhareddie/AI_code_review_agent.git
cd AI_code_review_agent
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up your API key**

Create a `.env` file in the root folder:
```
GROQ_API_KEY=your_groq_api_key_here
```
Get a free Groq API key at [console.groq.com](https://console.groq.com)

**5. Run the Streamlit dashboard**
```bash
streamlit run app.py
```

---

## Architecture

```
User inputs GitHub URL
         |
         v
  ingestion.py  -->  Clones repo, finds all .py and .java files
         |
         v
   parser.py    -->  Python: AST parsing
                     Java:   Regex + brace-matching
                     Extracts functions/classes as chunks
         |
         v
  reviewer.py   -->  Sends each chunk to Groq LLM, gets back JSON comments
         |
         v
  pipeline.py   -->  Ties everything together, returns flat list of comments
         |
         v
    app.py       -->  Displays comments in Streamlit with filters, confidence scores,
                      and JSON/CSV export
```

---

## Configurable Settings (in the UI)

| Setting | Default | Description |
|---|---|---|
| Max functions/classes to review | 20 | How many chunks are sent to the LLM. Higher = more thorough but slower. |
| Max lines per function/class | 100 | Chunks larger than this are skipped to stay within LLM token limits. |

---

## Limitations

- Supports Python (.py) and Java (.java) repositories
- Functions/classes longer than the configured line limit are skipped to stay within LLM token limits
- The pipeline reviews a maximum of N chunks per run (configurable via slider) to avoid API rate limits
- Uses Groq instead of OpenAI/Claude due to free tier availability
- Private repositories are not supported
