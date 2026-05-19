# AI Code Review Agent

A tool that takes any public Python GitHub repository, reads through the code, and gives you structured feedback — flagging bugs, security issues, and style problems, each with a confidence score so you know how much to trust the comment.

---

## What It Does

You paste a GitHub URL. The agent clones the repo, walks through every Python function and class, sends each one to an LLM, and collects all the review comments into a dashboard. Each comment tells you:

- What the issue is
- How serious it is (critical / warning / suggestion)
- What category it falls under (bug, security, performance, readability, style)
- How confident the agent is (0–100%)
- Which file and function it came from

Comments below 50% confidence are separated into a "Verify This" section — because not every LLM output should be trusted blindly.

---

## Tech Stack

- **GitPython** — clones the repo locally
- **Python ast module** — parses source files into functions and classes without running the code
- **Groq API (llama-3.3-70b-versatile)** — the LLM that reviews each chunk. Used instead of GPT-4o-mini/Claude because Groq offers a free tier with comparable output quality


---

## Project Structure

```
AI_code_review_agent/
├── agent/
│   ├── __init__.py
│   ├── ingestion.py     # Clones the repo, returns list of .py files
│   ├── parser.py        # AST parsing — extracts functions and classes
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

---

## Architecture

```
User inputs GitHub URL
         |
         v
  ingestion.py  -->  Clones repo, finds all .py files
         |
         v
   parser.py    -->  AST parses each file, extracts functions/classes as chunks
         |
         v
  reviewer.py   -->  Sends each chunk to Groq LLM, gets back JSON comments
         |
         v
  pipeline.py   -->  Ties everything together, returns flat list of comments
         |
         v
    app.py       -->  Displays comments in Streamlit with filters + confidence scores
```

---

##Limitations

- Only supports Python repositories — files in other languages are skipped
- Functions longer than 100 lines are skipped for now to stay within LLM token limits
- The pipeline reviews a maximum of 50 chunks per run to avoid API rate limits
- Uses Groq instead of OpenAI/Claude due to free tier availability
- Private repositories are not supported

---

