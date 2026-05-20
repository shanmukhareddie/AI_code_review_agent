import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = (
    "You are an expert code reviewer for Python and Java. "
    "Analyze the given code and return a JSON object with a key 'comments' containing an array of review comments.\n\n"
    "Each comment must have exactly these fields:\n"
    "- 'issue': short title (max 10 words)\n"
    "- 'description': detailed explanation and how to fix it\n"
    "- 'severity': one of ['critical', 'warning', 'suggestion']\n"
    "- 'category': one of ['security', 'performance', 'readability', 'bug', 'style']\n"
    "- 'confidence': integer 0-100 (how sure you are this is a real issue)\n"
    "- 'line': approximate line number as integer or null\n\n"
    "Rules:\n"
    "- Only report real issues. If the code is clean, return an empty array.\n"
    "- Do NOT make up issues that do not exist.\n"
    "- Return ONLY valid JSON. No markdown, no text outside the JSON.\n\n"
    'Example: {"comments": [{"issue": "Division by zero", "description": "No check for b=0", '
    '"severity": "critical", "category": "bug", "confidence": 95, "line": 2}]}'
)


def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY") # read key from env
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. "
            "Add it in Streamlit Cloud under Settings -> Secrets as: GROQ_API_KEY = 'your-key'"
        )
    return Groq(api_key=api_key)


def review_chunk(chunk: dict) -> list:
    language = chunk.get("language", "code")
    user_message = (
        "Review this " + language + " " + chunk["type"] +
        " named '" + chunk["name"] + "' from file '" + chunk["file"] +
        "' (line " + str(chunk["line"]) + "):\n\n" + chunk["source"]
    )

    try:
        client = get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )

        raw = response.choices[0].message.content
        parsed = json.loads(raw)
        comments = parsed.get("comments", [])

        for comment in comments: # attach file/function info to each comment
            comment["file"] = chunk["file"]
            comment["function"] = chunk["name"]
            comment["language"] = language

        return comments

    except RuntimeError:
        raise # let API key errors bubble up to the UI
    except json.JSONDecodeError:
        return [] # skip if LLM returned invalid JSON
    except Exception as e:
        print("LLM error for " + chunk["name"] + ": " + str(e))
        return []
