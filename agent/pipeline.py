import os
from agent.ingestion import clone_repo
from agent.parser import parse_all_files
from agent.reviewer import review_chunk


def run_pipeline(github_url: str, max_chunks: int = 50) -> list:
    """
    Full pipeline: clone -> parse -> review -> return all comments.
    """
    all_comments = []

    # Step 1: Clone
    print("[1/3] Cloning repository...")
    py_files = clone_repo(github_url)

    # Step 2: Parse
    print("[2/3] Parsing Python files...")
    chunks = parse_all_files(py_files)

    # Limit chunks to avoid too many API calls
    chunks = chunks[:max_chunks]
    print("Reviewing " + str(len(chunks)) + " chunks (limited to " + str(max_chunks) + ")...")

    # Step 3: Review each chunk
    print("[3/3] Sending chunks to LLM for review...")
    for i, chunk in enumerate(chunks):
        print("  Reviewing " + str(i + 1) + "/" + str(len(chunks)) + ": " + chunk["name"] + "...")
        comments = review_chunk(chunk)
        all_comments.extend(comments)

    print("Done! Total comments generated: " + str(len(all_comments)))
    return all_comments
