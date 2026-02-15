"""GitHub API setup helper for GitHub benchmark scenario."""

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
