"""GitHub API setup helper for GitHub benchmark scenario."""

import base64
import logging
import requests
from typing import Any

logger = logging.getLogger(__name__)


class GitHubSetup:
    """Handles GitHub API operations for benchmark setup and validation."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: str):
        """Initialize GitHub setup with personal access token.

        Args:
            token: GitHub personal access token with repo scope
        """
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        self.test_issue_numbers: list[int] = []  # Track test issues for cleanup
        self.seeded_files: list[str] = []  # Track seeded file paths for cleanup
        self.seeded_branch: str | None = None  # Track seeded branch for cleanup
        self.seeded_pr_number: int | None = None  # Track seeded PR for cleanup
        self.seeded_release_id: int | None = None  # Track seeded release for cleanup
        self.seeded_tag: str | None = None  # Track seeded tag for cleanup
        self.seeded_issue_numbers: list[int] = []  # Track seed issues for cleanup
        self.seeded_label_name: str | None = None  # Track seed label for cleanup

    def _make_request(
        self, method: str, endpoint: str, json_data: dict[str, Any] | None = None, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make authenticated request to GitHub API.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (e.g., 'repos/owner/repo/issues')
            json_data: JSON body for POST/PATCH requests
            params: Query parameters

        Returns:
            API response as dict

        Raises:
            requests.HTTPError: If API request fails
        """
        url = f"{self.BASE_URL}/{endpoint}"
        response = requests.request(method, url, json=json_data, params=params, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json() if response.content else {}

    def create_test_issue(self, repo_owner: str, repo_name: str, title: str, body: str) -> dict[str, Any]:
        """Create a test issue in a repository.

        Args:
            repo_owner: Repository owner username
            repo_name: Repository name
            title: Issue title
            body: Issue body text

        Returns:
            Issue data dict with 'number', 'url', etc.

        Raises:
            requests.HTTPError: If creation fails
        """
        endpoint = f"repos/{repo_owner}/{repo_name}/issues"
        issue_data = {
            "title": title,
            "body": body,
            "labels": ["benchmark-test"],
        }

        response = self._make_request("POST", endpoint, json_data=issue_data)
        issue_number = response.get("number")

        if issue_number:
            self.test_issue_numbers.append(issue_number)
            logger.info(f"Created test issue #{issue_number}: {title}")

        return response

    def get_repo_info(self, repo_owner: str, repo_name: str) -> dict[str, Any]:
        """Get repository information.

        Args:
            repo_owner: Repository owner username
            repo_name: Repository name

        Returns:
            Repository data dict

        Raises:
            requests.HTTPError: If fetch fails
        """
        endpoint = f"repos/{repo_owner}/{repo_name}"
        response = self._make_request("GET", endpoint)
        logger.debug(f"Fetched repo info for {repo_owner}/{repo_name}")
        return response

    def list_issues(self, repo_owner: str, repo_name: str, state: str = "open", labels: str | None = None) -> list[dict[str, Any]]:
        """List issues in a repository.

        Args:
            repo_owner: Repository owner username
            repo_name: Repository name
            state: Issue state ('open', 'closed', 'all')
            labels: Comma-separated label filter

        Returns:
            List of issue dicts

        Raises:
            requests.HTTPError: If fetch fails
        """
        endpoint = f"repos/{repo_owner}/{repo_name}/issues"
        params = {"state": state}
        if labels:
            params["labels"] = labels

        response = self._make_request("GET", endpoint, params=params)
        logger.info(f"Listed {len(response)} issues for {repo_owner}/{repo_name}")
        return response

    def close_issue(self, repo_owner: str, repo_name: str, issue_number: int) -> dict[str, Any]:
        """Close an issue.

        Args:
            repo_owner: Repository owner username
            repo_name: Repository name
            issue_number: Issue number to close

        Returns:
            Updated issue data

        Raises:
            requests.HTTPError: If update fails
        """
        endpoint = f"repos/{repo_owner}/{repo_name}/issues/{issue_number}"
        response = self._make_request("PATCH", endpoint, json_data={"state": "closed"})
        logger.info(f"Closed issue #{issue_number}")
        return response

    def cleanup_test_issues(self, repo_owner: str, repo_name: str) -> int:
        """Close all test issues created during setup.

        Args:
            repo_owner: Repository owner username
            repo_name: Repository name

        Returns:
            Number of issues closed
        """
        closed_count = 0
        for issue_number in self.test_issue_numbers:
            try:
                self.close_issue(repo_owner, repo_name, issue_number)
                closed_count += 1
            except requests.HTTPError as e:
                logger.warning(f"Failed to close issue #{issue_number}: {e}")

        self.test_issue_numbers.clear()
        logger.info(f"Cleanup complete: closed {closed_count} test issues")
        return closed_count

    def seed_repo_data(self, repo_owner: str, repo_name: str) -> dict[str, Any]:
        """Seed the repository with commits, a PR branch, and a release.

        Creates:
        - 5 files on the default branch (5 commits, with async function content)
        - 1 branch with 1 additional commit (for PR)
        - 1 open PR from that branch
        - 1 release tag (v1.0.0-benchmark)

        Args:
            repo_owner: Repository owner username
            repo_name: Repository name

        Returns:
            Dict with seeded data info
        """
        import time

        seed_info: dict[str, Any] = {}

        # Get default branch
        repo_info = self.get_repo_info(repo_owner, repo_name)
        default_branch = repo_info.get("default_branch", "main")

        # --- Step 1: Create 5 files on main (5 commits) ---
        files = [
            {
                "path": "src/utils.js",
                "message": "Add utility functions",
                "content": (
                    "// Utility functions\n\n"
                    "async function fetchData(url) {\n"
                    "  const response = await fetch(url);\n"
                    "  return response.json();\n"
                    "}\n\n"
                    "async function processItems(items) {\n"
                    "  return items.map(item => item.toString());\n"
                    "}\n\n"
                    "module.exports = { fetchData, processItems };\n"
                ),
            },
            {
                "path": "src/api.js",
                "message": "Add API client module",
                "content": (
                    "// API client\n\n"
                    "async function getUser(id) {\n"
                    "  return fetchData(`/api/users/${id}`);\n"
                    "}\n\n"
                    "async function listPosts() {\n"
                    "  return fetchData('/api/posts');\n"
                    "}\n\n"
                    "module.exports = { getUser, listPosts };\n"
                ),
            },
            {
                "path": "src/index.js",
                "message": "Add main entry point",
                "content": (
                    "const { fetchData } = require('./utils');\n"
                    "const { getUser } = require('./api');\n\n"
                    "async function main() {\n"
                    "  console.log('OpenClaw sandbox project');\n"
                    "}\n\n"
                    "main();\n"
                ),
            },
            {
                "path": "README.md",
                "message": "Add README",
                "content": (
                    "# openclaw-sandbox\n\n"
                    "Benchmark test repository for OpenClaw AI agent.\n\n"
                    "## Features\n"
                    "- Async function utilities\n"
                    "- API client\n"
                    "- Main entry point\n"
                ),
            },
            {
                "path": "package.json",
                "message": "Add package.json",
                "content": (
                    '{\n  "name": "openclaw-sandbox",\n'
                    '  "version": "1.0.0",\n'
                    '  "description": "Benchmark test repo",\n'
                    '  "main": "src/index.js"\n}\n'
                ),
            },
        ]

        for file_info in files:
            content_b64 = base64.b64encode(file_info["content"].encode()).decode()
            endpoint = f"repos/{repo_owner}/{repo_name}/contents/{file_info['path']}"
            try:
                self._make_request("PUT", endpoint, json_data={
                    "message": file_info["message"],
                    "content": content_b64,
                })
                self.seeded_files.append(file_info["path"])
                logger.info(f"Created file {file_info['path']}")
                time.sleep(0.5)  # Avoid rate limiting
            except requests.HTTPError as e:
                logger.warning(f"Failed to create {file_info['path']}: {e}")

        seed_info["files_created"] = len(self.seeded_files)

        # --- Step 2: Get the SHA of the default branch HEAD ---
        try:
            ref_data = self._make_request("GET", f"repos/{repo_owner}/{repo_name}/git/refs/heads/{default_branch}")
            head_sha = ref_data["object"]["sha"]

            # Create feature branch
            branch_name = "feature/benchmark-pr-branch"
            self._make_request("POST", f"repos/{repo_owner}/{repo_name}/git/refs", json_data={
                "ref": f"refs/heads/{branch_name}",
                "sha": head_sha,
            })
            self.seeded_branch = branch_name
            logger.info(f"Created branch {branch_name}")

            # Add a file on the feature branch
            pr_file_content = base64.b64encode(
                "// Feature: improved error handling\nasync function handleError(err) {\n  console.error(err);\n}\n".encode()
            ).decode()
            self._make_request("PUT", f"repos/{repo_owner}/{repo_name}/contents/src/error_handler.js", json_data={
                "message": "Add error handler feature",
                "content": pr_file_content,
                "branch": branch_name,
            })
            self.seeded_files.append("src/error_handler.js (on feature branch)")
            logger.info("Created file on feature branch")

            # --- Step 3: Open a PR ---
            pr_data = self._make_request("POST", f"repos/{repo_owner}/{repo_name}/pulls", json_data={
                "title": "[BENCHMARK] Add error handler feature",
                "body": "This PR adds improved error handling for async functions.",
                "head": branch_name,
                "base": default_branch,
            })
            self.seeded_pr_number = pr_data.get("number")
            seed_info["pr_number"] = self.seeded_pr_number
            logger.info(f"Created PR #{self.seeded_pr_number}")

        except requests.HTTPError as e:
            logger.warning(f"Failed to create branch/PR: {e}")

        # --- Step 4: Create a release ---
        try:
            # Create a lightweight tag via releases API (it creates the tag automatically)
            release_data = self._make_request("POST", f"repos/{repo_owner}/{repo_name}/releases", json_data={
                "tag_name": "v1.0.0-benchmark",
                "target_commitish": default_branch,
                "name": "v1.0.0 - Initial Release",
                "body": "First benchmark release. Includes async utility functions and API client.",
                "draft": False,
                "prerelease": False,
            })
            self.seeded_release_id = release_data.get("id")
            self.seeded_tag = "v1.0.0-benchmark"
            seed_info["release_id"] = self.seeded_release_id
            seed_info["release_tag"] = self.seeded_tag
            logger.info(f"Created release {self.seeded_tag} (id={self.seeded_release_id})")
        except requests.HTTPError as e:
            logger.warning(f"Failed to create release: {e}")

        # --- Step 5: Create benchmark-seed label ---
        try:
            self._make_request("POST", f"repos/{repo_owner}/{repo_name}/labels", json_data={
                "name": "benchmark-seed",
                "color": "0075ca",
                "description": "Seeded by benchmark setup for label listing task",
            })
            self.seeded_label_name = "benchmark-seed"
            seed_info["seeded_label"] = self.seeded_label_name
            logger.info("Created label 'benchmark-seed'")
        except requests.HTTPError as e:
            # Label may already exist from a previous run — that's fine
            logger.warning(f"Failed to create benchmark-seed label (may already exist): {e}")
            self.seeded_label_name = "benchmark-seed"
            seed_info["seeded_label"] = self.seeded_label_name

        # --- Step 6: Seed 3 open issues for T2 (list issues) ---
        seed_issues = [
            {
                "title": "[BENCHMARK SEED] Bug: fetchData returns null on timeout",
                "body": "When the network request times out, fetchData returns null instead of throwing an error.",
                "labels": ["benchmark-seed"],
            },
            {
                "title": "[BENCHMARK SEED] Feature: add retry logic to processItems",
                "body": "processItems should retry failed operations up to 3 times before giving up.",
                "labels": ["benchmark-seed"],
            },
            {
                "title": "[BENCHMARK SEED] Docs: update README with API examples",
                "body": "The README is missing usage examples for the API client module.",
                "labels": ["benchmark-seed"],
            },
        ]
        for issue_data in seed_issues:
            try:
                resp = self._make_request(
                    "POST",
                    f"repos/{repo_owner}/{repo_name}/issues",
                    json_data=issue_data,
                )
                issue_number = resp.get("number")
                if issue_number:
                    self.seeded_issue_numbers.append(issue_number)
                    logger.info(f"Created seed issue #{issue_number}: {issue_data['title']}")
                time.sleep(0.3)
            except requests.HTTPError as e:
                logger.warning(f"Failed to create seed issue '{issue_data['title']}': {e}")

        seed_info["seeded_issue_numbers"] = self.seeded_issue_numbers
        seed_info["seeded_issue_titles"] = [i["title"] for i in seed_issues]

        return seed_info

    def cleanup_seeded_data(self, repo_owner: str, repo_name: str) -> None:
        """Remove all data seeded by seed_repo_data().

        Deletes files on main, the PR branch, the PR (close it), and the release/tag.

        Args:
            repo_owner: Repository owner username
            repo_name: Repository name
        """
        # Close PR first (can't delete a branch with open PR unless we close it)
        if self.seeded_pr_number:
            try:
                self._make_request(
                    "PATCH",
                    f"repos/{repo_owner}/{repo_name}/pulls/{self.seeded_pr_number}",
                    json_data={"state": "closed"},
                )
                logger.info(f"Closed PR #{self.seeded_pr_number}")
            except requests.HTTPError as e:
                logger.warning(f"Failed to close PR #{self.seeded_pr_number}: {e}")
            self.seeded_pr_number = None

        # Delete feature branch
        if self.seeded_branch:
            try:
                self._make_request(
                    "DELETE",
                    f"repos/{repo_owner}/{repo_name}/git/refs/heads/{self.seeded_branch}",
                )
                logger.info(f"Deleted branch {self.seeded_branch}")
            except requests.HTTPError as e:
                logger.warning(f"Failed to delete branch {self.seeded_branch}: {e}")
            self.seeded_branch = None

        # Delete release
        if self.seeded_release_id:
            try:
                self._make_request(
                    "DELETE",
                    f"repos/{repo_owner}/{repo_name}/releases/{self.seeded_release_id}",
                )
                logger.info(f"Deleted release {self.seeded_release_id}")
            except requests.HTTPError as e:
                logger.warning(f"Failed to delete release {self.seeded_release_id}: {e}")
            self.seeded_release_id = None

        # Delete tag
        if self.seeded_tag:
            try:
                self._make_request(
                    "DELETE",
                    f"repos/{repo_owner}/{repo_name}/git/refs/tags/{self.seeded_tag}",
                )
                logger.info(f"Deleted tag {self.seeded_tag}")
            except requests.HTTPError as e:
                logger.warning(f"Failed to delete tag {self.seeded_tag}: {e}")
            self.seeded_tag = None

        # Delete files on main branch (need SHA of each file to delete)
        main_files = [f for f in self.seeded_files if "feature branch" not in f]
        for file_path in main_files:
            try:
                file_data = self._make_request(
                    "GET",
                    f"repos/{repo_owner}/{repo_name}/contents/{file_path}",
                )
                file_sha = file_data.get("sha")
                if file_sha:
                    self._make_request(
                        "DELETE",
                        f"repos/{repo_owner}/{repo_name}/contents/{file_path}",
                        json_data={
                            "message": f"Remove benchmark seed file: {file_path}",
                            "sha": file_sha,
                        },
                    )
                    logger.info(f"Deleted file {file_path}")
            except requests.HTTPError as e:
                logger.warning(f"Failed to delete {file_path}: {e}")

        self.seeded_files.clear()

        # Close seeded issues (T2 seed)
        for issue_number in self.seeded_issue_numbers:
            try:
                self._make_request(
                    "PATCH",
                    f"repos/{repo_owner}/{repo_name}/issues/{issue_number}",
                    json_data={"state": "closed"},
                )
                logger.info(f"Closed seeded issue #{issue_number}")
            except requests.HTTPError as e:
                logger.warning(f"Failed to close seeded issue #{issue_number}: {e}")
        self.seeded_issue_numbers.clear()

        # Delete benchmark-seed label (T6 seed)
        if self.seeded_label_name:
            try:
                self._make_request(
                    "DELETE",
                    f"repos/{repo_owner}/{repo_name}/labels/{self.seeded_label_name}",
                )
                logger.info(f"Deleted label '{self.seeded_label_name}'")
            except requests.HTTPError as e:
                logger.warning(f"Failed to delete label '{self.seeded_label_name}': {e}")
            self.seeded_label_name = None

    def verify_api_access(self, repo_owner: str, repo_name: str) -> bool:
        """Verify GitHub API is accessible with the provided token.

        Args:
            repo_owner: Repository owner username
            repo_name: Repository name to test access

        Returns:
            True if API is accessible, False otherwise
        """
        try:
            self.get_repo_info(repo_owner, repo_name)
            logger.info(f"✓ GitHub API access verified for {repo_owner}/{repo_name}")
            return True
        except requests.HTTPError as e:
            logger.error(f"✗ GitHub API access failed: {e}")
            return False
