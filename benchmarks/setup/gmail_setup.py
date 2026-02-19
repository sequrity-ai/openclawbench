"""Gmail API setup helper for email benchmark scenario."""

import base64
import logging
import time
from email.mime.text import MIMEText
from typing import Any

import requests

logger = logging.getLogger(__name__)


class GmailSetup:
    """Handles Gmail API operations for benchmark setup and validation."""

    BASE_URL = "https://gmail.googleapis.com/gmail/v1/users/me"
    TOKEN_URL = "https://oauth2.googleapis.com/token"

    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        """Initialize Gmail setup with OAuth2 credentials.

        Args:
            client_id: Google OAuth2 client ID
            client_secret: Google OAuth2 client secret
            refresh_token: OAuth2 refresh token for accessing Gmail
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token: str | None = None
        self.token_expiry: float = 0.0  # Unix timestamp when token expires
        self.test_email_ids: list[str] = []  # Track test emails for cleanup

    def _get_access_token(self) -> str:
        """Get a valid access token using the refresh token.

        Returns:
            Access token string

        Raises:
            requests.HTTPError: If token refresh fails
        """
        # Re-fetch if no token or if token expires within the next 60 seconds
        if self.access_token and time.time() < self.token_expiry - 60:
            return self.access_token

        # Request new access token using refresh token
        response = requests.post(
            self.TOKEN_URL,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=30,
        )
        response.raise_for_status()

        token_data = response.json()
        self.access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)
        self.token_expiry = time.time() + expires_in
        logger.debug(f"Refreshed Gmail API access token (expires in {expires_in}s)")
        return self.access_token

    def _make_request(
        self, method: str, endpoint: str, json_data: dict[str, Any] | None = None, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make authenticated request to Gmail API.

        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint (e.g., 'messages', 'messages/send')
            json_data: JSON body for POST requests
            params: Query parameters

        Returns:
            API response as dict

        Raises:
            requests.HTTPError: If API request fails
        """
        url = f"{self.BASE_URL}/{endpoint}"

        # Get access token
        access_token = self._get_access_token()

        # Make request with Bearer token
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.request(method, url, json=json_data, params=params, headers=headers, timeout=30)
        response.raise_for_status()

        return response.json() if response.content else {}

    def send_test_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_address: str | None = None,
        from_display_name: str | None = None,
    ) -> str:
        """Send a test email via Gmail API.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body text
            from_address: Sender email address (defaults to the authenticated account)
            from_display_name: Optional display name or address shown in the From header.
                When provided without from_address, the display name is embedded in the
                From header so the recipient can see it (e.g. "support@example.com").
                This is used by Task 5 to simulate an email that appears to come from
                support@example.com even though it is sent via the benchmark account.

        Returns:
            Email ID of sent message

        Raises:
            requests.HTTPError: If send fails
        """
        # Create MIME message
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        if from_address:
            message["from"] = from_address
        elif from_display_name:
            # Embed display name in the From header without changing the actual sender
            message["from"] = from_display_name

        # Encode message in base64url format
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        # Send via API
        response = self._make_request(
            "POST",
            "messages/send",
            json_data={"raw": raw_message},
        )

        email_id = response.get("id")
        if email_id:
            self.test_email_ids.append(email_id)
            logger.info(f"Sent test email: {subject} (ID: {email_id})")

        return email_id

    def search_emails(self, query: str, max_results: int = 10) -> list[dict[str, Any]]:
        """Search for emails matching query.

        Args:
            query: Gmail search query (e.g., 'from:sender@example.com subject:test')
            max_results: Maximum number of results to return

        Returns:
            List of email metadata dicts with 'id' and 'threadId'

        Raises:
            requests.HTTPError: If search fails
        """
        response = self._make_request(
            "GET",
            "messages",
            params={"q": query, "maxResults": max_results},
        )

        messages = response.get("messages", [])
        logger.info(f"Search '{query}' found {len(messages)} emails")
        return messages

    def get_email(self, email_id: str) -> dict[str, Any]:
        """Get full email details by ID.

        Args:
            email_id: Gmail message ID

        Returns:
            Full email object with headers, body, etc.

        Raises:
            requests.HTTPError: If fetch fails
        """
        response = self._make_request("GET", f"messages/{email_id}", params={"format": "full"})

        logger.debug(f"Fetched email ID: {email_id}")
        return response

    def delete_email(self, email_id: str) -> None:
        """Delete an email by ID.

        Args:
            email_id: Gmail message ID

        Raises:
            requests.HTTPError: If delete fails
        """
        self._make_request("DELETE", f"messages/{email_id}")
        logger.info(f"Deleted email ID: {email_id}")

    def cleanup_test_emails(self) -> int:
        """Delete all test emails created during setup.

        Note: This attempts to delete emails from the benchmark's sent folder.
        Emails in the bot's inbox cannot be deleted with the benchmark's OAuth token
        and must be cleaned up manually or by the bot.

        Returns:
            Number of emails deleted
        """
        deleted_count = 0
        for email_id in self.test_email_ids:
            try:
                self.delete_email(email_id)
                deleted_count += 1
            except requests.HTTPError as e:
                logger.warning(f"Failed to delete email {email_id}: {e}")

        self.test_email_ids.clear()
        logger.info(f"Cleanup complete: deleted {deleted_count} test emails")
        return deleted_count

    def list_labels(self) -> list[dict]:
        """List all Gmail labels.

        Returns:
            List of label dicts with 'id' and 'name' fields
        """
        response = self._make_request("GET", "labels")
        return response.get("labels", [])

    def delete_label(self, label_id: str) -> None:
        """Delete a Gmail label by ID.

        Args:
            label_id: Gmail label ID

        Raises:
            requests.HTTPError: If delete fails
        """
        url = f"{self.BASE_URL}/labels/{label_id}"
        access_token = self._get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.request("DELETE", url, headers=headers, timeout=30)
        response.raise_for_status()
        logger.info(f"Deleted label ID: {label_id}")

    def delete_label_by_name(self, label_name: str) -> bool:
        """Delete a Gmail label by name if it exists.

        Args:
            label_name: Display name of the label to delete

        Returns:
            True if label was found and deleted, False if it didn't exist
        """
        labels = self.list_labels()
        for label in labels:
            if label.get("name", "").lower() == label_name.lower():
                self.delete_label(label["id"])
                logger.info(f"Deleted label '{label_name}'")
                return True
        logger.debug(f"Label '{label_name}' not found — nothing to delete")
        return False

    def verify_api_access(self) -> bool:
        """Verify Gmail API is accessible with the provided API key.

        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # Try to list messages (should work even if empty)
            self._make_request("GET", "messages", params={"maxResults": 1})
            logger.info("✓ Gmail API access verified")
            return True
        except requests.HTTPError as e:
            logger.error(f"✗ Gmail API access failed: {e}")
            return False
