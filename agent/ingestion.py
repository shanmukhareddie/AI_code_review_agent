import os
import shutil
import git
from dotenv import load_dotenv


load_dotenv()


def clone_repo(github_url: str, dest_dir: str = "repos/cloned_repo") -> list:
    # Clean up if folder already exists
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)

    try:
        print("Cloning " + github_url + " ...")
        git.Repo.clone_from(github_url, dest_dir)
        print("Clone successful!")
    except git.exc.GitCommandError as e:
        raise ValueError("Failed to clone repo: " + str(e))

    # Collect all .py files, skip hidden folders
    py_files = []
    for root, dirs, files in os.walk(dest_dir):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))

    if not py_files:
        raise ValueError("No Python files found in this repository.")

    print("Found " + str(len(py_files)) + " Python file(s).")
    return py_files
