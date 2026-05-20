import os
import shutil
import git
from dotenv import load_dotenv


load_dotenv()


def is_valid_github_url(url: str) -> tuple[bool, str]:
    """Validate the GitHub URL before attempting to clone."""
    if not url.startswith("https://github.com/"):
        return False, "❌ Please enter a valid GitHub URL starting with https://github.com/"
    parts = url.replace("https://github.com/", "").strip("/").split("/")
    if len(parts) < 2 or not parts[0] or not parts[1]:
        return False, "❌ URL must include both a username and repository name, e.g. https://github.com/username/repo"
    return True, ""


def clone_repo(github_url: str, dest_dir: str = "repos/cloned_repo") -> list:
    # Clean up if folder already exists
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)

    try:
        print("Cloning " + github_url + " ...")
        git.Repo.clone_from(github_url, dest_dir)
        print("Clone successful!")
    except git.exc.GitCommandError as e:
        error_str = str(e).lower()
        if "repository not found" in error_str or "not found" in error_str:
            raise ValueError(
                "❌ Repository not found. Make sure the URL is correct and the repository is **public**. "
                "Private repositories are not supported."
            )
        elif "could not read username" in error_str or "authentication" in error_str or "exit code(128)" in error_str:
            raise ValueError(
                "🔒 This appears to be a **private repository**. "
                "This tool only works with **public** GitHub repositories. "
                "Please enter a public repo URL like https://github.com/username/repo"
            )
        elif "not a git repository" in error_str:
            raise ValueError(
                "❌ The URL does not point to a valid Git repository. Please double-check the URL."
            )
        else:
            raise ValueError(
                "❌ Failed to clone the repository. Please make sure:\n"
                "- The URL is correct\n"
                "- The repository is **public**\n"
                "- The repository exists on GitHub"
            )

    # Collect all .py files, skip hidden folders
    py_files = []
    for root, dirs, files in os.walk(dest_dir):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))

    if not py_files:
        raise ValueError(
            "⚠️ No Python files found in this repository. "
            "This tool only reviews Python (.py) files."
        )

    print("Found " + str(len(py_files)) + " Python file(s).")
    return py_files
