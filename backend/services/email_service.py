"""
Email service for IMAP monitoring and SMTP sending
Handles email fetching, parsing, and sending
"""
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import parseaddr
from typing import List, Dict, Optional
from datetime import datetime
import logging

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailService:
    """Service for email operations (IMAP fetch and SMTP send)"""

    def __init__(self):
        """Initialize email service"""
        self.imap_host = settings.EMAIL_IMAP_HOST
        self.imap_port = settings.EMAIL_IMAP_PORT
        self.smtp_host = settings.EMAIL_SMTP_HOST
        self.smtp_port = settings.EMAIL_SMTP_PORT
        self.email_address = settings.EMAIL_ADDRESS
        self.email_password = settings.EMAIL_PASSWORD

        logger.info(f"Initialized EmailService for {self.email_address}")

    async def fetch_new_emails(
        self,
        limit: int = 50,
        folder: str = 'INBOX',
        mark_as_seen: bool = False,
        since_days: int = 7
    ) -> List[Dict]:
        """Fetch emails from IMAP server using date-based filtering

        Args:
            limit: Maximum number of emails to fetch
            folder: IMAP folder to check
            mark_as_seen: Mark emails as read after fetching
            since_days: Fetch emails from last N days (default: 7)

        Returns:
            List of email data dictionaries
        """
        if not self.imap_host or not self.email_address:
            logger.warning("Email credentials not configured")
            return []

        try:
            # Connect to IMAP server
            if self.imap_port == 993:
                mail = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            else:
                mail = imaplib.IMAP4(self.imap_host, self.imap_port)

            # Login
            mail.login(self.email_address, self.email_password)

            # Select folder
            mail.select(folder)

            # Calculate date cutoff for filtering
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=since_days)
            date_str = cutoff_date.strftime('%d-%b-%Y')

            # Search for emails since cutoff date (checks ALL emails, not just UNSEEN)
            # This ensures we capture emails even if they've been marked as read
            search_criteria = f'SINCE {date_str}'
            logger.info(f"Searching for emails since {date_str}")
            status, messages = mail.search(None, search_criteria)

            if status != 'OK':
                logger.error("Failed to search emails")
                mail.logout()
                return []

            # Get message IDs
            message_ids = messages[0].split()

            if not message_ids:
                logger.info("No new emails found")
                mail.logout()
                return []

            # Limit number of emails
            message_ids = message_ids[-limit:]  # Get most recent

            emails = []

            for msg_id in message_ids:
                try:
                    # Fetch email
                    status, msg_data = mail.fetch(msg_id, '(RFC822)')

                    if status != 'OK':
                        continue

                    # Parse email
                    raw_email = msg_data[0][1]
                    email_message = email.message_from_bytes(raw_email)

                    # Extract data
                    email_data = self._parse_email(email_message)

                    if email_data:
                        emails.append(email_data)

                    # Mark as seen if requested
                    if mark_as_seen:
                        mail.store(msg_id, '+FLAGS', '\\Seen')

                except Exception as e:
                    logger.error(f"Error parsing email {msg_id}: {e}")

            mail.logout()

            logger.info(f"Fetched {len(emails)} new emails")
            return emails

        except Exception as e:
            logger.error(f"Error fetching emails: {e}", exc_info=True)
            return []

    def _parse_email(self, email_message) -> Optional[Dict]:
        """Parse email message into structured data

        Args:
            email_message: Email message object

        Returns:
            Email data dictionary
        """
        try:
            # Get sender
            from_header = email_message.get('From', '')
            sender_name, sender_email = parseaddr(from_header)

            if not sender_email:
                logger.warning("Email missing sender address")
                return None

            # Get subject
            subject = email_message.get('Subject', '')
            if subject:
                # Decode if needed
                from email.header import decode_header
                decoded = decode_header(subject)
                subject = ''.join(
                    str(text, encoding or 'utf-8') if isinstance(text, bytes) else str(text)
                    for text, encoding in decoded
                )

            # Get message ID
            message_id = email_message.get('Message-ID', '')

            # Get date
            date_str = email_message.get('Date', '')
            received_at = None
            if date_str:
                from email.utils import parsedate_to_datetime
                try:
                    received_at = parsedate_to_datetime(date_str)
                except:
                    received_at = datetime.utcnow()
            else:
                received_at = datetime.utcnow()

            # Get body
            body = self._get_email_body(email_message)

            if not body:
                logger.warning(f"Email {message_id} has no body")
                return None

            # Parse email headers for thread tracking
            email_headers = self._parse_email_headers(email_message)

            email_data = {
                'message_id': message_id,
                'sender_email': sender_email.lower(),
                'sender_name': sender_name or sender_email,
                'subject': subject,
                'body': body,
                'received_at': received_at,
                'email_headers': email_headers
            }

            return email_data

        except Exception as e:
            logger.error(f"Error parsing email: {e}")
            return None

    def _parse_email_headers(self, email_message) -> Dict:
        """Parse email headers for thread tracking (RFC 5322)

        Args:
            email_message: Email message object

        Returns:
            Dictionary of email headers
        """
        headers = {}

        try:
            # Thread tracking headers
            headers['in_reply_to'] = email_message.get('In-Reply-To', '').strip()
            headers['references'] = email_message.get('References', '').strip()

            # Parse References header into list
            if headers['references']:
                # References can be space or newline separated list of message IDs
                refs_list = headers['references'].replace('\n', ' ').replace('\r', '').split()
                headers['references_list'] = refs_list
            else:
                headers['references_list'] = []

            # Microsoft-specific thread index
            headers['thread_index'] = email_message.get('Thread-Index', '').strip()

            # Additional useful headers
            headers['reply_to'] = email_message.get('Reply-To', '').strip()
            headers['cc'] = email_message.get('Cc', '').strip()
            headers['bcc'] = email_message.get('Bcc', '').strip()

            # Check if email is likely a forward
            subject = email_message.get('Subject', '')
            headers['is_likely_forward'] = any(
                subject.lower().startswith(prefix)
                for prefix in ['fwd:', 'fw:', 'forward:']
            )

            logger.debug(f"Parsed headers: in_reply_to={headers['in_reply_to']}, "
                        f"references_count={len(headers['references_list'])}")

            return headers

        except Exception as e:
            logger.error(f"Error parsing email headers: {e}")
            return {}

    def _get_email_body(self, email_message) -> str:
        """Extract email body text

        Args:
            email_message: Email message object

        Returns:
            Email body text
        """
        body = ""

        if email_message.is_multipart():
            # Iterate through email parts
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                # Skip attachments
                if "attachment" in content_disposition:
                    continue

                # Get text/plain content
                if content_type == "text/plain":
                    try:
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        body = payload.decode(charset, errors='ignore')
                        break
                    except:
                        pass

                # Fallback to text/html
                elif content_type == "text/html" and not body:
                    try:
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        html_body = payload.decode(charset, errors='ignore')

                        # Simple HTML to text conversion
                        import re
                        text_body = re.sub('<[^<]+?>', '', html_body)
                        body = text_body
                    except:
                        pass
        else:
            # Not multipart - get content directly
            try:
                payload = email_message.get_payload(decode=True)
                charset = email_message.get_content_charset() or 'utf-8'
                body = payload.decode(charset, errors='ignore')
            except:
                body = str(email_message.get_payload())

        return body.strip()

    async def send_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        body: str,
        in_reply_to: str = None
    ) -> bool:
        """Send email via SMTP

        Args:
            to_email: Recipient email address
            to_name: Recipient name
            subject: Email subject
            body: Email body
            in_reply_to: Message ID to reply to

        Returns:
            True if sent successfully
        """
        if not self.smtp_host or not self.email_address:
            logger.warning("SMTP credentials not configured")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.email_address}"
            msg['To'] = f"{to_name} <{to_email}>"
            msg['Subject'] = subject

            # Add CC recipients (always include these team members)
            cc_recipients = settings.EMAIL_CC_RECIPIENTS
            if cc_recipients:
                msg['Cc'] = cc_recipients
                logger.info(f"Adding CC recipients: {cc_recipients}")

            if in_reply_to:
                msg['In-Reply-To'] = in_reply_to
                msg['References'] = in_reply_to

            # Add body
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)

            # Connect and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.send_message(msg)

            logger.info(f"Sent email to {to_email} (CC: {cc_recipients}): {subject}")
            return True

        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}", exc_info=True)
            return False

    async def test_connection(self) -> Dict[str, bool]:
        """Test IMAP and SMTP connections

        Returns:
            Dictionary with connection test results
        """
        results = {
            'imap': False,
            'smtp': False
        }

        # Test IMAP
        try:
            if self.imap_port == 993:
                mail = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            else:
                mail = imaplib.IMAP4(self.imap_host, self.imap_port)

            mail.login(self.email_address, self.email_password)
            mail.logout()

            results['imap'] = True
            logger.info("✅ IMAP connection successful")

        except Exception as e:
            logger.error(f"❌ IMAP connection failed: {e}")

        # Test SMTP
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)

            results['smtp'] = True
            logger.info("✅ SMTP connection successful")

        except Exception as e:
            logger.error(f"❌ SMTP connection failed: {e}")

        return results


# Singleton instance
_service = None

def get_email_service() -> EmailService:
    """Get singleton email service instance"""
    global _service
    if _service is None:
        _service = EmailService()
    return _service
