"""
Email utility functions for processing and formatting email content
"""
import re
import logging
import html as html_module

logger = logging.getLogger(__name__)


def html_to_text(html_content: str) -> str:
    """
    Convert HTML content to plain text with proper formatting preservation.

    This function:
    - Uses BeautifulSoup for proper HTML parsing
    - Removes script and style elements
    - Preserves line breaks and paragraph structure
    - Cleans up excessive whitespace
    - Handles HTML entities

    Args:
        html_content: HTML string to convert

    Returns:
        Plain text version with preserved formatting
    """
    if not html_content:
        return ""

    # Check if content appears to be HTML
    if not ('<html' in html_content.lower() or '<div' in html_content.lower() or '<p' in html_content.lower()):
        return html_content

    try:
        # Try using BeautifulSoup if available
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style elements
        for script in soup(['script', 'style']):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text
    except ImportError:
        # Fallback: simple regex-based HTML stripping
        logger.warning("BeautifulSoup not available, using regex fallback for HTML stripping")

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_content)

        # Decode HTML entities
        text = html_module.unescape(text)

        # Clean up excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'  +', ' ', text)

        return text.strip()


def add_line_breaks_to_plain_text(text: str) -> str:
    """
    Add line breaks to plain text emails that lost formatting.

    This function adds line breaks at common email patterns:
    - Email signatures ("Sent from my iPhone", "Best regards", etc.)
    - Quoted email headers ("On [date], [person] wrote:")
    - Greetings and closings

    Args:
        text: Plain text string

    Returns:
        Text with added line breaks for better readability
    """
    if not text:
        return text

    # Decode HTML entities first
    text = html_module.unescape(text)

    # Patterns that should have line breaks before them
    patterns_before = [
        r'(Sent from my (iPhone|iPad|Android|BlackBerry|Mobile))',  # Mobile signatures
        r'(On .{10,80}wrote:)',  # Quoted email headers like "On Oct 24, 2025, at 12:43 AM, Carmen wrote:"
        r'(\-{3,})',  # Horizontal lines (---, etc.)
        r'(_{3,})',  # Underscores
        r'(={3,})',  # Equal signs
        r'(From: .+)',  # Email headers
        r'(To: .+)',
        r'(Subject: .+)',
        r'(Date: .+)',
    ]

    # Patterns that should have line breaks after them
    patterns_after = [
        r'(Thanks,)',
        r'(Best regards,)',
        r'(Best,)',
        r'(Sincerely,)',
        r'(Cheers,)',
        r'(Thank you,)',
        r'(Regards,)',
        r'(Sent from my (iPhone|iPad|Android|BlackBerry|Mobile))',
        r'(wrote:)',  # End of quoted email header
        r'(Hi [A-Z][a-z]+,)',  # Greetings like "Hi Carmen,"
        r'(Hello [A-Z][a-z]+,)',
        r'(Dear [A-Z][a-z]+,)',
    ]

    # Add line breaks before patterns
    for pattern in patterns_before:
        text = re.sub(pattern, r'\n\n\1', text)

    # Add line breaks after patterns
    for pattern in patterns_after:
        text = re.sub(pattern, r'\1\n\n', text)

    # Clean up excessive newlines (max 2 consecutive)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Clean up spaces before newlines
    text = re.sub(r' +\n', '\n', text)

    return text.strip()
