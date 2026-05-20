import os
import json
from groq import Groq
from dotenv import load_dotenv


load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = (
    "You are an expert Python code reviewer. Analyze the given code and return a JSON object "
    "with a key 'comments' containing an array of review comments.\n\n"
    "Each comment must have exactly these fields:\n"
    "- 'issue': short title (string, max 10 words)\n"
    "- 'description': detailed explanation of the problem and how to fix it (string)\n"
    "- 'severity': exactly one of ['critical', 'warning', 'suggestion']\n"
    "- 'category': exactly one of ['security', 'performance', 'readability', 'bug', 'style']\n"
    "- 'confidence': integer between 0 and 100\n"
    "- 'line': approximate line number as integer (or null if unknown)\n\n"
    "Rules:\n"
    "- Only report real issues. If the code is clean, return an empty array.\n"
    "- Do NOT hallucinate issues that don't exist.\n"
    "- confidence reflects how certain you are: 90+ = very sure, 50-89 = likely, below 50 = uncertain.\n"
    "- Return ONLY valid JSON. No markdown, no explanation outside the JSON.\n\n"
    'Example: {"comments": [{"issue": "Division by zero", "description": "No check for b=0", '
    '"severity": "critical", "category": "bug", "confidence": 95, "line": 2}]}'
)


def review_chunk(chunk: dict) -> list:
    """
    Sends a single code chunk to the LLM and returns structured review comments.
    """
    user_message = (
        "Review this Python " + chunk["type"] +
        " named '" + chunk["name"] +
        "' from file '" + chunk["file"] +
        "' (starting at line " + str(chunk["line"]) + "):\n\n" +
        chunk["source"]
    )

    try:
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

        # Attach metadata to each comment
        for comment in comments:
            comment["file"] = chunk["file"]
            comment["function"] = chunk["name"]
            comment["chunk_type"] = chunk["type"]

        return comments

    except json.JSONDecodeError as e:
        print("JSON parse error for " + chunk["name"] + ": " + str(e))
        return []
    except Exception as e:
        print("LLM error for " + chunk["name"] + ": " + str(e))
        return []


if __name__ == "__main__":
    test_chunk = {
        "name": "divide",
        "type": "function",
        "file": "math_utils.py",
        "line": 1,
        "source": "def divide(a, b):\n    return a / b"
    }
    results = review_chunk(test_chunk)
    for r in results:
        print(r)
