import os
from agent.ingestion import clone_repo
from agent.parser import parse_all_files
from agent.reviewer import review_chunk

def run_pipeline(github_url: str, max_chunks: int = 50) -> list[dict]:
    """
    Full pipeline: clone → parse → review → return all comments.
    max_chunks limits how many functions/classes are sent to the LLM.
    """
    all_comments = []

    # Step 1: Clone
    print(f"\n[1/3] Cloning repository...")
    py_files = clone_repo(github_url)

    # Step 2: Parse
    print(f"\n[2/3] Parsing Python files...")
    chunks = parse_all_files(py_files)

    # Limit chunks to avoid too many API calls
    chunks = chunks[:max_chunks]
    print(f"Reviewing {len(chunks)} chunks (limited to {max_chunks})...")

    # Step 3: Review each chunk
    print(f"\n[3/3] Sending chunks to LLM for review...")
    for i, chunk in enumerate(chunks):
        print(f"  Reviewing {i+1}/{len(chunks)}: {chunk['name']}...")
        comments = review_chunk(chunk)
        all_comments.extend(comments)

    print(f"\nDone! Total comments generated: {len(all_comments)}")
    return all_comments


if __name__ == "__main__":
    comments = run_pipeline("https://github.com/pallets/flask", max_chunks=10)
    for c in comments:
        print(f"\n[{c['severity'].upper()}] {c['issue']} (confidence: {c['confidence']}%)")
        print(f"  File: {c['file']} | Function: {c['function']}")
        print(f"  {c['description'][:100]}...")
