import json
import os
import pathlib
import subprocess
import sys
from typing import List


def print_lines(prefix: str, lines: List[str]):
    for index, line in enumerate(lines):
        print(f"{prefix} {index}: {line}")


def run_command(command, ignore_error=False):
    try:
        process = subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as cpe:
        if ignore_error:
            return str(cpe), False
        print("Error running git command:")
        print(f"Command: {cpe.cmd}")
        if cpe.stderr is not None:
            print_lines("stderr", cpe.stderr.split("\n"))
        print(str(cpe))
        sys.exit(1)

    return process.stdout, True


def git_info():
    output, _ = run_command(
        ["git", "show", "--format=%H%n%h%n%an%n%at%n%cn%n%ct%n%d", "--name-status"]
    )

    [
        commit_hash,
        commit_hash_abbreviated,
        author_name,
        author_date,
        committer_name,
        committer_date,
        *_,
    ] = output.split("\n")
    return {
        "commit_hash": commit_hash,
        "commit_hash_abbreviated": commit_hash_abbreviated,
        "author_name": author_name,
        "author_date": int(author_date) * 1000,
        "committer_name": committer_name,
        "committer_date": int(committer_date) * 1000,
    }


def git_url():
    output, _ = run_command(["git", "config", "--get", "remote.origin.url"])
    url = output.rstrip("\n")
    if url.endswith(".git"):
        url = url[0:-4]
    return url


def git_branch():
    output, _ = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    return output.rstrip("\n")


def git_tag(commit_hash):
    result, success = run_command(
        ["git", "describe", "--exact-match", "--tags", commit_hash], ignore_error=True
    )
    if success:
        return result
    else:
        return None


def git_config():
    output, _ = run_command(
        ["git", "config", "--global", "--add", "safe.directory", "*"]
    )
    return output.rstrip("\n")


def save_info(info, dest):
    pathlib.Path(dest).mkdir(exist_ok=True)
    with open(os.path.join(dest, "git-info.json"), "w", encoding="utf-8") as fout:
        json.dump(info, fout, indent=4)


def service_path(path: str) -> str:
    return os.path.join(os.path.dirname(__file__), "../..", path)


def main():
    dest = service_path("build")

    git_config()
    info = git_info()
    url = git_url()
    info["url"] = url

    branch = git_branch()
    tag = git_tag(info["commit_hash"])

    info["branch"] = branch
    info["tag"] = tag

    save_info(info, dest)

    sys.exit(0)


main()
