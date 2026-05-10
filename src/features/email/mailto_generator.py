"""Generate mailto: URLs for opening the user's default email client."""

import urllib.parse

from shared.models import EmailDraft


class MailtoGenerator:
    """Build ``mailto:`` URLs that pre-fill subject and body."""

    def generate(self, draft: EmailDraft) -> str:
        """Return a mailto URL with encoded subject and body.

        Args:
            draft: The email draft containing subject, body, and optional recipient.

        Returns:
            A ``mailto:`` URL string.
        """
        recipient = draft.recipient or ""
        params = {
            "subject": draft.subject,
            "body": draft.body,
        }
        query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        return f"mailto:{recipient}?{query}"
