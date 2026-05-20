import ast
import os
import re
from typing import List, Dict


def parse_python_file(filepath: str, max_lines: int = 100) -> List[Dict]:
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
    except Exception as e:
        print("Could not read " + filepath + ": " + str(e))
        return []

    try:
        tree = ast.parse(source) # parse the file into an AST tree
    except SyntaxError:
        return [] # skip files with syntax errors

    chunks = []
    lines = source.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            kind = "class" if isinstance(node, ast.ClassDef) else "function"
            start = node.lineno - 1
            end = node.end_lineno
            block = "\n".join(lines[start:end])

            if (end - start) > max_lines: # skip blocks that are too long
                print("Skipping " + node.name + " — too large (" + str(end - start) + " lines)")
                continue

            chunks.append({
                "name": node.name,
                "type": kind,
                "source": block,
                "line": node.lineno,
                "file": filepath,
                "language": "python"
            })

    return chunks


def parse_java_file(filepath: str, max_lines: int = 100) -> List[Dict]:
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
    except Exception as e:
        print("Could not read " + filepath + ": " + str(e))
        return []

    chunks = []

    # patterns to find class and method declarations
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

    def extract_block(src, start_pos): # extract code block by matching braces
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

    def get_line_num(src, pos): # get line number from character position
        return src[:pos].count("\n") + 1

    for match in class_pattern.finditer(source):
        name = match.group(1)
        block = extract_block(source, match.start())
        line_count = block.count("\n")
        if line_count > max_lines:
            print("Skipping class " + name + " — too large (" + str(line_count) + " lines)")
            continue
        if block:
            chunks.append({"name": name, "type": "class", "source": block,
                           "line": get_line_num(source, match.start()), "file": filepath, "language": "java"})

    for match in method_pattern.finditer(source):
        name = match.group(1)
        if name in ("if", "for", "while", "switch", "catch", "try"): # skip keywords
            continue
        block = extract_block(source, match.start())
        line_count = block.count("\n")
        if line_count > max_lines:
            print("Skipping method " + name + " — too large (" + str(line_count) + " lines)")
            continue
        if block:
            chunks.append({"name": name, "type": "function", "source": block,
                           "line": get_line_num(source, match.start()), "file": filepath, "language": "java"})

    return chunks


def parse_all_files(files: List[str], max_lines_per_chunk: int = 100) -> List[Dict]:
    all_chunks = []
    for filepath in files:
        if filepath.endswith(".py"):
            chunks = parse_python_file(filepath, max_lines=max_lines_per_chunk)
        elif filepath.endswith(".java"):
            chunks = parse_java_file(filepath, max_lines=max_lines_per_chunk)
        else:
            continue
        all_chunks.extend(chunks)

    py = sum(1 for c in all_chunks if c.get("language") == "python")
    java = sum(1 for c in all_chunks if c.get("language") == "java")
    print("Total chunks: " + str(len(all_chunks)) + " (Python: " + str(py) + ", Java: " + str(java) + ")")
    return all_chunks
