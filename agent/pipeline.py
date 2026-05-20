import os
from agent.ingestion import clone_repo
from agent.parser import parse_all_files
from agent.reviewer import review_chunk


def run_pipeline(github_url: str, max_chunks: int = 50, max_lines_per_chunk: int = 100) -> list:
    """
    Full pipeline: clone -> parse -> review -> return all comments.
    """
    all_comments = []


    print("[1/3] Cloning repository...")
    source_files = clone_repo(github_url)


    print("[2/3] Parsing source files (Python + Java)...")
    chunks = parse_all_files(source_files, max_lines_per_chunk=max_lines_per_chunk)

    # Limit chunks to avoid too many API calls
    total_found = len(chunks)
    chunks = chunks[:max_chunks]
    print(
        "Reviewing " + str(len(chunks)) + " chunks "
        "(found " + str(total_found) + ", limited to " + str(max_chunks) + ")..."
    )

    print("[3/3] Sending chunks to LLM for review...")
    for i, chunk in enumerate(chunks):
        print("  Reviewing " + str(i + 1) + "/" + str(len(chunks)) + ": " + chunk["name"] + "...")
        comments = review_chunk(chunk)
        all_comments.extend(comments)

    print("Done! Total comments generated: " + str(len(all_comments)))
    return all_comments, total_found
