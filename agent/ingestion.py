import os
import shutil
import git
from typing import Tuple
from dotenv import load_dotenv

load_dotenv()


def is_valid_github_url(url: str) -> Tuple[bool, str]:
    if not url.startswith("https://github.com/"):
        return False, "❌ Please enter a valid GitHub URL starting with https://github.com/"
    parts = url.replace("https://github.com/", "").strip("/").split("/")
    if len(parts) < 2 or not parts[0] or not parts[1]:
        return False, "❌ URL must include username and repo name, e.g. https://github.com/username/repo"
    return True, ""


def clone_repo(github_url: str, dest_dir: str = "repos/cloned_repo") -> list:
    if os.path.exists(dest_dir): # remove old clone if exists
        shutil.rmtree(dest_dir)

    try:
        git.Repo.clone_from(github_url, dest_dir)
    except git.exc.GitCommandError as e:
        err = str(e).lower()
        if "could not read username" in err or "exit code(128)" in err or "authentication" in err:
            raise ValueError(
                "🔒 This looks like a **private repository**. "
                "This tool only works with **public** GitHub repos."
            )
        elif "not found" in err:
            raise ValueError(
                "❌ Repository not found. Check the URL and make sure the repo is public."
            )
        else:
            raise ValueError(
                "❌ Could not clone the repo. Make sure the URL is correct and the repo is public."
            )

    source_files = []
    for root, dirs, files in os.walk(dest_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".")] # skip hidden folders
        for file in files:
            if file.endswith(".py") or file.endswith(".java"):
                source_files.append(os.path.join(root, file))

    if not source_files:
        raise ValueError(
            "⚠️ No Python or Java files found in this repo."
        )

    py = sum(1 for f in source_files if f.endswith(".py"))
    java = sum(1 for f in source_files if f.endswith(".java"))
    print("Found " + str(len(source_files)) + " file(s) — Python: " + str(py) + ", Java: " + str(java))
    return source_files
