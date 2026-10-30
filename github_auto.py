from github import Github, Auth
from datetime import datetime
from dotenv import load_dotenv
import os
import re
import sys

# Load .env file
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("REPO_NAME")
FILE_PATH = os.getenv("FILE_PATH")
BASE_BRANCH = os.getenv("BASE_BRANCH")
COMMIT_MESSAGE = os.getenv("COMMIT_MESSAGE")
PR_TITLE = os.getenv("PR_TITLE")
PR_BODY = os.getenv("PR_BODY")
ISSUE_TITLE = os.getenv("ISSUE_TITLE")
ISSUE_BODY = os.getenv("ISSUE_BODY")


def validate_config():

    required = {
        "GITHUB_TOKEN": GITHUB_TOKEN,
        "REPO_NAME": REPO_NAME,
        "FILE_PATH": FILE_PATH,
        "BASE_BRANCH": BASE_BRANCH,
        "COMMIT_MESSAGE": COMMIT_MESSAGE,
        "PR_TITLE": PR_TITLE,
        "PR_BODY": PR_BODY,
        "ISSUE_TITLE": ISSUE_TITLE,
        "ISSUE_BODY": ISSUE_BODY
    }

    missing = [
        key for key, value in required.items()
        if not value
    ]

    if missing:
        raise ValueError(
            f"Missing environment variables: {', '.join(missing)}"
        )


def main():

    try:

        validate_config()

        # 1. Connect to GitHub
        auth = Auth.Token(GITHUB_TOKEN)
        github = Github(auth=auth)

        repo = github.get_repo(REPO_NAME)

        print("Connected to GitHub:", repo.full_name)

        # 2. Generate branch name
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        branch_name = f"update-{timestamp}"

        # 3. Get base branch
        base_branch = repo.get_branch(BASE_BRANCH)

        # 4. Create GitHub Issue
        print("\nCreating Issue...")

        issue = repo.create_issue(
            title=ISSUE_TITLE,
            body=ISSUE_BODY
        )

        print("Issue created:", issue.html_url)

        # 5. Create new branch
        print("\nCreating Branch...")

        repo.create_git_ref(
            ref=f"refs/heads/{branch_name}",
            sha=base_branch.commit.sha
        )

        print("Branch created:", branch_name)

        # 6. Get README file
        print("\nReading file...")

        file_content = repo.get_contents(
            FILE_PATH,
            ref=branch_name
        )

        current_content = file_content.decoded_content.decode("utf-8")

        # 7. Update timestamp
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        updated_content, count = re.subn(
            r"(?m)^Timestamp: .*?$",
            f"Timestamp: {current_time}",
            current_content
        )

        if count == 0:
            updated_content = (
                current_content.rstrip()
                + f"\n\nTimestamp: {current_time}\n"
            )

        # 8. Commit changes
        print("\nUpdating README...")

        repo.update_file(
            path=FILE_PATH,
            message=COMMIT_MESSAGE,
            content=updated_content,
            sha=file_content.sha,
            branch=branch_name
        )

        print("Changes committed successfully.")

        # 9. Create Pull Request
        print("\nCreating Pull Request...")

        pr = repo.create_pull(
            title=PR_TITLE,
            body=f"{PR_BODY}\n\nCloses #{issue.number}",
            head=branch_name,
            base=BASE_BRANCH
        )

        print("Pull Request created:", pr.html_url)

        # 10. Automatically merge PR
        print("\nMerging Pull Request...")

        merge_result = pr.merge(
            commit_message=f"Merge {branch_name}"
        )

        if not merge_result.merged:
            print("PR merge failed. Branch will NOT be deleted.")
            return

        print("Pull Request merged successfully!")

        # 11. Close Issue
        print("\nClosing Issue...")

        issue.edit(state="closed")

        print("Issue closed successfully!")

        # 12. Delete feature branch
        print("\nDeleting feature branch...")

        branch_ref = repo.get_git_ref(f"heads/{branch_name}")
        branch_ref.delete()

        print("Branch deleted successfully!")

        # Final result
        print("\n================================")
        print("AUTOMATION COMPLETED SUCCESSFULLY")
        print("================================")

        print("Issue:", issue.html_url)
        print("Pull Request:", pr.html_url)
        print("Branch:", branch_name)

    except Exception as error:

        print("\nAutomation failed:", error)
        sys.exit(1)


if __name__ == "__main__":
    main()