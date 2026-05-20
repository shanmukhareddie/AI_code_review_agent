import ast
import os
import re
from typing import List, Dict


# ── Python Parser ────────────────────────────────────────────────────────────

def parse_python_file(filepath: str) -> List[Dict]:
    """
    Parses a Python file using AST and extracts functions and classes.
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
    except Exception as e:
        print("Could not read " + filepath + ": " + str(e))
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        print("Syntax error in " + filepath + ": " + str(e))
        return []

    chunks = []
    lines = source.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            node_type = "class" if isinstance(node, ast.ClassDef) else "function"
            start = node.lineno - 1
            end = node.end_lineno
            node_source = "\n".join(lines[start:end])

            if (end - start) > 100:
                print("Skipping " + node.name + " in " + filepath + " — too large (" + str(end - start) + " lines)")
                continue

            chunks.append({
                "name": node.name,
                "type": node_type,
                "source": node_source,
                "line": node.lineno,
                "file": filepath,
                "language": "python"
            })

    return chunks


# ── Java Parser ──────────────────────────────────────────────────────────────

def parse_java_file(filepath: str) -> List[Dict]:
    """
    Parses a Java file using regex to extract classes and methods.
    Since Python has no built-in Java AST, we use brace-matching to
    extract the full body of each class and method.
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
    except Exception as e:
        print("Could not read " + filepath + ": " + str(e))
        return []

    lines = source.splitlines()
    chunks = []

    # Regex patterns for Java class and method declarations
    class_pattern = re.compile(
        r'^\s*(?:public|private|protected)?\s*(?:abstract|final|static)?\s*'
        r'class\s+(\w+)\s*(?:extends\s+\w+)?\s*(?:implements\s+[\w,\s]+)?\s*\{',
        re.MULTILINE
    )
    method_pattern = re.compile(
        r'^\s*(?:public|private|protected|static|final|abstract|synchronized|native|\s)+'
        r'[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{',
        re.MULTILINE
    )

    def extract_block(src: str, start_pos: int) -> str:
        """
        Given the position of the opening brace, extract the full block
        by counting matching braces.
        """
        brace_pos = src.find("{", start_pos)
        if brace_pos == -1:
            return ""
        depth = 0
        for i in range(brace_pos, len(src)):
            if src[i] == "{":
                depth += 1
            elif src[i] == "}":
                depth -= 1
                if depth == 0:
                    return src[start_pos:i + 1]
        return src[start_pos:]

    def get_line_number(src: str, pos: int) -> int:
        return src[:pos].count("\n") + 1

    # Extract classes
    for match in class_pattern.finditer(source):
        name = match.group(1)
        block = extract_block(source, match.start())
        line_num = get_line_number(source, match.start())
        line_count = block.count("\n")

        if line_count > 100:
            print("Skipping class " + name + " in " + filepath + " — too large (" + str(line_count) + " lines)")
            continue

        if block:
            chunks.append({
                "name": name,
                "type": "class",
                "source": block,
                "line": line_num,
                "file": filepath,
                "language": "java"
            })

    # Extract methods
    for match in method_pattern.finditer(source):
        name = match.group(1)
        # Skip constructor-like matches and common false positives
        if name in ("if", "for", "while", "switch", "catch", "try"):
            continue
        block = extract_block(source, match.start())
        line_num = get_line_number(source, match.start())
        line_count = block.count("\n")

        if line_count > 100:
            print("Skipping method " + name + " in " + filepath + " — too large (" + str(line_count) + " lines)")
            continue

        if block:
            chunks.append({
                "name": name,
                "type": "function",
                "source": block,
                "line": line_num,
                "file": filepath,
                "language": "java"
            })

    return chunks


# ── Combined Parser ──────────────────────────────────────────────────────────

def parse_all_files(files: List[str]) -> List[Dict]:
    """
    Runs the correct parser for each file based on extension.
    Supports .py and .java files.
    """
    all_chunks = []
    for filepath in files:
        if filepath.endswith(".py"):
            chunks = parse_python_file(filepath)
        elif filepath.endswith(".java"):
            chunks = parse_java_file(filepath)
        else:
            continue
        all_chunks.extend(chunks)

    py_count   = sum(1 for c in all_chunks if c.get("language") == "python")
    java_count = sum(1 for c in all_chunks if c.get("language") == "java")
    print("Total chunks extracted: " + str(len(all_chunks)) +
          " (Python: " + str(py_count) + ", Java: " + str(java_count) + ")")
    return all_chunks


if __name__ == "__main__":
    from ingestion import clone_repo
    files = clone_repo("https://github.com/pallets/flask")
    chunks = parse_all_files(files)
    for chunk in chunks[:3]:
        print("\n--- " + chunk["type"].upper() + ": " + chunk["name"] + " (line " + str(chunk["line"]) + ") [" + chunk["language"] + "] ---")
        print(chunk["source"][:200])
