"""Email drafting and mailto: generation feature."""

from .composer import EmailComposer
from .mailto_generator import MailtoGenerator

__all__ = [
    "EmailComposer",
    "MailtoGenerator",
]
