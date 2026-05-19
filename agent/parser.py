import ast
import os

def parse_python_file(filepath: str) -> list[dict]:
    """
    Parses a Python file using AST and extracts functions and classes.
    Returns a list of dicts with name, type, source code, and line number.
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
    except Exception as e:
        print(f"Could not read {filepath}: {e}")
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        print(f"Syntax error in {filepath}: {e}")
        return []

    chunks = []
    lines = source.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            node_type = "class" if isinstance(node, ast.ClassDef) else "function"

            # Extract source lines for this node
            start = node.lineno - 1
            end = node.end_lineno
            node_source = "\n".join(lines[start:end])

            # Skip very large chunks (over 100 lines) to avoid token limits
            if (end - start) > 100:
                print(f"Skipping {node.name} in {filepath} — too large ({end - start} lines)")
                continue

            chunks.append({
                "name": node.name,
                "type": node_type,
                "source": node_source,
                "line": node.lineno,
                "file": filepath
            })

    return chunks


def parse_all_files(py_files: list[str]) -> list[dict]:
    """
    Runs parse_python_file on all files and returns combined results.
    """
    all_chunks = []
    for filepath in py_files:
        chunks = parse_python_file(filepath)
        all_chunks.extend(chunks)
    
    print(f"Total chunks extracted: {len(all_chunks)}")
    return all_chunks

if __name__ == "__main__":
    from ingestion import clone_repo
    files = clone_repo("https://github.com/pallets/flask")
    chunks = parse_all_files(files)
    # Print first 3 chunks
    for chunk in chunks[:3]:
        print(f"\n--- {chunk['type'].upper()}: {chunk['name']} (line {chunk['line']}) ---")
        print(chunk['source'][:200])
