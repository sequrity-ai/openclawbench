"""Setup utilities for web research benchmark scenario."""

import requests
from typing import Any


class WebSetup:
    """Handles setup for web research benchmarks."""

    def __init__(self):
        """Initialize web setup with test URLs."""
        # Use stable, public URLs for testing
        self.wikipedia_url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
        self.github_repo_url = "https://github.com/anthropics/anthropic-cookbook"
        self.search_topic = "Python web frameworks comparison"

    def prepare_test_urls(self) -> dict[str, Any]:
        """Prepare test URLs and topics.

        Returns:
            Dict with test URLs and expected data
        """
        return {
            "wikipedia_url": self.wikipedia_url,
            "github_repo_url": self.github_repo_url,
            "search_topic": self.search_topic,
            # Expected data for validation
            "wikipedia_expected": {
                "language": "Python",
                "type": "programming language",
                # These are facts from the Python Wikipedia page
                "has_founding_info": True,
            },
            "github_expected": {
                "owner": "anthropics",
                "repo": "anthropic-cookbook",
                "is_github": True,
            },
        }

    def verify_urls_accessible(self) -> tuple[bool, str]:
        """Verify test URLs are accessible.

        Returns:
            Tuple of (success, message)
        """
        try:
            # Check Wikipedia
            resp = requests.head(self.wikipedia_url, timeout=5)
            if resp.status_code >= 400:
                return False, f"Wikipedia URL not accessible: {resp.status_code}"

            # Check GitHub
            resp = requests.head(self.github_repo_url, timeout=5)
            if resp.status_code >= 400:
                return False, f"GitHub URL not accessible: {resp.status_code}"

            return True, "All test URLs accessible"

        except Exception as e:
            return False, f"URL check failed: {str(e)}"
