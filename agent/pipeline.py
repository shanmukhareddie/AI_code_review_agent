from agent.ingestion import clone_repo
from agent.parser import parse_all_files
from agent.reviewer import review_chunk


def run_pipeline(github_url: str, max_chunks: int = 50, max_lines_per_chunk: int = 100):
    print("[1/3] Cloning repo...")
    source_files = clone_repo(github_url)

    print("[2/3] Parsing files...")
    chunks = parse_all_files(source_files, max_lines_per_chunk=max_lines_per_chunk)
    total_found = len(chunks) # save total before slicing
    chunks = chunks[:max_chunks] # limit to avoid too many API calls

    print("[3/3] Reviewing " + str(len(chunks)) + " chunks...")
    all_comments = []
    for i, chunk in enumerate(chunks):
        print("  " + str(i + 1) + "/" + str(len(chunks)) + ": " + chunk["name"])
        comments = review_chunk(chunk)
        all_comments.extend(comments)

    print("Done! Total comments: " + str(len(all_comments)))
    return all_comments, total_found
