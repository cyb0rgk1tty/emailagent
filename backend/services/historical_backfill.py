"""
Historical Email Backfill Service
Fetches and processes historical "Contact Form:" emails with your manual responses
Uses IMAP server-side filtering for efficiency
"""
import imaplib
import email
from email.utils import parseaddr, parsedate_to_datetime
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging
import re

from config import get_settings
from database import get_db_session
from models.database import Lead, Conversation, EmailMessage, HistoricalResponseExample
from agents import get_extraction_agent
from rag.embeddings import get_embedding_generator

logger = logging.getLogger(__name__)
settings = get_settings()


class HistoricalBackfillService:
    """Service for backfilling historical emails and responses"""

    def __init__(self):
        """Initialize historical backfill service"""
        self.historical_email = settings.HISTORICAL_EMAIL_ADDRESS
        self.historical_password = settings.HISTORICAL_EMAIL_PASSWORD
        self.historical_imap_host = settings.HISTORICAL_IMAP_HOST
        self.historical_imap_port = settings.HISTORICAL_IMAP_PORT
        self.subject_filter = settings.BACKFILL_SUBJECT_FILTER
        self.lookback_days = settings.BACKFILL_LOOKBACK_DAYS
        self.embedder = get_embedding_generator()

        logger.info(f"Initialized HistoricalBackfillService for {self.historical_email}")

    async def fetch_contact_form_emails(
        self,
        folder: str = 'INBOX',
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Fetch ONLY emails matching subject filter using IMAP search.
        Server-side filtering for efficiency.

        Args:
            folder: IMAP folder to search
            limit: Optional limit on number of emails to fetch

        Returns:
            List of email data dictionaries
        """
        if not self.historical_imap_host or not self.historical_email:
            logger.error("Historical email credentials not configured")
            return []

        try:
            # Connect to IMAP server
            if self.historical_imap_port == 993:
                mail = imaplib.IMAP4_SSL(self.historical_imap_host, self.historical_imap_port)
            else:
                mail = imaplib.IMAP4(self.historical_imap_host, self.historical_imap_port)

            # Login
            mail.login(self.historical_email, self.historical_password)
            logger.info("✅ Connected to historical inbox")

            # Select folder
            mail.select(folder)

            # Build IMAP search criteria (server-side filtering)
            date_cutoff = (datetime.now() - timedelta(days=self.lookback_days)).strftime("%d-%b-%Y")

            # IMAP search: Subject contains filter AND since date
            search_criteria = f'(SUBJECT "{self.subject_filter}" SINCE {date_cutoff})'

            logger.info(f"Searching with criteria: {search_criteria}")

            status, messages = mail.search(None, search_criteria)

            if status != 'OK':
                logger.error("Failed to search emails")
                mail.logout()
                return []

            # Get message IDs
            message_ids = messages[0].split()

            if not message_ids:
                logger.info(f"No emails found matching '{self.subject_filter}'")
                mail.logout()
                return []

            logger.info(f"Found {len(message_ids)} emails matching filter")

            # Apply limit if specified
            if limit:
                message_ids = message_ids[:limit]
                logger.info(f"Limited to {limit} emails")

            emails = []

            # Fetch emails
            for msg_id in message_ids:
                try:
                    # Fetch full email
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

                except Exception as e:
                    logger.error(f"Error parsing email {msg_id}: {e}")

            mail.logout()

            logger.info(f"✅ Fetched {len(emails)} emails from historical inbox")
            return emails

        except Exception as e:
            logger.error(f"Error fetching historical emails: {e}", exc_info=True)
            return []

    def _parse_email(self, email_message) -> Optional[Dict]:
        """
        Parse email message into structured data

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
        """
        Parse email headers for thread tracking (RFC 5322)

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
                refs_list = headers['references'].replace('\n', ' ').replace('\r', '').split()
                headers['references_list'] = refs_list
            else:
                headers['references_list'] = []

            # Check if email is likely a reply
            subject = email_message.get('Subject', '')
            headers['is_likely_reply'] = any(
                subject.lower().startswith(prefix)
                for prefix in ['re:', 'reply:']
            )

            return headers

        except Exception as e:
            logger.error(f"Error parsing email headers: {e}")
            return {}

    def _get_email_body(self, email_message) -> str:
        """
        Extract email body text

        Args:
            email_message: Email message object

        Returns:
            Email body text
        """
        body = ""

        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                if "attachment" in content_disposition:
                    continue

                if content_type == "text/plain":
                    try:
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        body = payload.decode(charset, errors='ignore')
                        break
                    except:
                        pass

                elif content_type == "text/html" and not body:
                    try:
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        html_body = payload.decode(charset, errors='ignore')
                        text_body = re.sub('<[^<]+?>', '', html_body)
                        body = text_body
                    except:
                        pass
        else:
            try:
                payload = email_message.get_payload(decode=True)
                charset = email_message.get_content_charset() or 'utf-8'
                body = payload.decode(charset, errors='ignore')
            except:
                body = str(email_message.get_payload())

        return body.strip()

    def separate_inquiries_and_responses(
        self,
        emails: List[Dict]
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Separate emails into inquiries and responses

        Args:
            emails: List of email dictionaries

        Returns:
            Tuple of (inquiries, responses)
        """
        inquiries = []
        responses = []

        for email_data in emails:
            subject = email_data.get('subject', '')
            sender = email_data.get('sender_email', '')

            # Responses: From your email AND subject starts with "Re:"
            if (sender.lower() == self.historical_email.lower() and
                    subject.lower().startswith('re:')):
                responses.append(email_data)
            # Inquiries: Subject starts with "Contact Form:"
            elif subject.startswith(self.subject_filter):
                inquiries.append(email_data)

        logger.info(f"Separated into {len(inquiries)} inquiries and {len(responses)} responses")

        return inquiries, responses

    def match_responses_to_inquiries(
        self,
        inquiries: List[Dict],
        responses: List[Dict]
    ) -> List[Tuple[Dict, Dict]]:
        """
        Match responses to their original inquiries using email threading

        Args:
            inquiries: List of inquiry email dictionaries
            responses: List of response email dictionaries

        Returns:
            List of (inquiry, response) tuples
        """
        matches = []

        # Build inquiry lookup by message_id
        inquiry_by_message_id = {
            email_data['message_id']: email_data
            for email_data in inquiries
        }

        for response in responses:
            headers = response.get('email_headers', {})
            in_reply_to = headers.get('in_reply_to', '')
            references_list = headers.get('references_list', [])

            # Try In-Reply-To first
            if in_reply_to and in_reply_to in inquiry_by_message_id:
                inquiry = inquiry_by_message_id[in_reply_to]
                matches.append((inquiry, response))
                logger.debug(f"Matched response via In-Reply-To: {inquiry['subject'][:50]}")
                continue

            # Try References
            matched = False
            for ref_id in references_list:
                if ref_id in inquiry_by_message_id:
                    inquiry = inquiry_by_message_id[ref_id]
                    matches.append((inquiry, response))
                    logger.debug(f"Matched response via References: {inquiry['subject'][:50]}")
                    matched = True
                    break

            if matched:
                continue

            # Fallback: Time-based + subject matching
            response_subject = response.get('subject', '').lower().replace('re:', '').strip()
            response_date = response.get('received_at')

            for inquiry in inquiries:
                inquiry_subject = inquiry.get('subject', '').replace(self.subject_filter, '').strip()
                inquiry_date = inquiry.get('received_at')

                # Check if subjects match (loosely)
                if inquiry_subject.lower() in response_subject:
                    # Check if response is within 90 days of inquiry
                    if inquiry_date and response_date:
                        time_diff = abs((response_date - inquiry_date).days)
                        if time_diff <= 90:
                            matches.append((inquiry, response))
                            logger.debug(f"Matched response via fallback: {inquiry['subject'][:50]}")
                            break

        logger.info(f"✅ Matched {len(matches)} inquiry-response pairs")

        return matches

    async def process_matched_pair(
        self,
        inquiry: Dict,
        response: Dict
    ) -> Optional[int]:
        """
        Process a matched inquiry-response pair and store in database

        Args:
            inquiry: Inquiry email data
            response: Response email data

        Returns:
            Lead ID if successful
        """
        try:
            # Extract lead data from inquiry
            extraction_agent = get_extraction_agent()
            extracted_data = await extraction_agent.extract_from_email(inquiry)

            if not extracted_data:
                logger.error(f"Failed to extract data from inquiry {inquiry['message_id']}")
                return None

            async with get_db_session() as session:
                # Check if lead already exists
                from sqlalchemy import select
                result = await session.execute(
                    select(Lead).where(Lead.message_id == inquiry['message_id'])
                )
                existing_lead = result.scalar_one_or_none()

                if existing_lead:
                    logger.info(f"Lead already exists for {inquiry['message_id']}, skipping")
                    return existing_lead.id

                # Create conversation
                conversation = Conversation(
                    thread_subject=inquiry.get('subject', ''),
                    participants=[inquiry.get('sender_email')],
                    initial_message_id=inquiry['message_id'],
                    last_message_id=response['message_id'],
                    started_at=inquiry.get('received_at') or datetime.utcnow(),
                    last_activity_at=response.get('received_at') or datetime.utcnow()
                )
                session.add(conversation)
                await session.flush()

                conversation_id = conversation.id

                # Create lead (marked as historical)
                lead = Lead(
                    message_id=inquiry['message_id'],
                    conversation_id=conversation_id,
                    is_historical=True,
                    source_type='historical_backfill',
                    lead_status='responded',
                    sender_email=inquiry.get('sender_email'),
                    sender_name=inquiry.get('sender_name'),
                    subject=inquiry.get('subject'),
                    body=inquiry.get('body'),
                    received_at=inquiry.get('received_at') or datetime.utcnow(),
                    processed_at=datetime.utcnow(),

                    # Extracted data
                    product_type=extracted_data.get('product_type'),
                    specific_ingredients=extracted_data.get('specific_ingredients'),
                    delivery_format=extracted_data.get('delivery_format'),
                    certifications_requested=extracted_data.get('certifications_requested'),
                    estimated_quantity=extracted_data.get('estimated_quantity'),
                    timeline_urgency=extracted_data.get('timeline_urgency'),
                    budget_indicator=extracted_data.get('budget_indicator'),
                    experience_level=extracted_data.get('experience_level'),
                    distribution_channel=extracted_data.get('distribution_channel'),
                    has_existing_brand=extracted_data.get('has_existing_brand'),
                    lead_quality_score=extracted_data.get('lead_quality_score'),
                    response_priority=extracted_data.get('response_priority'),
                    specific_questions=extracted_data.get('specific_questions'),
                    geographic_region=extracted_data.get('geographic_region'),
                    extraction_confidence=extracted_data.get('extraction_confidence'),

                    # Human response
                    human_response_body=response.get('body'),
                    human_response_date=response.get('received_at')
                )
                session.add(lead)
                await session.flush()

                lead_id = lead.id

                # Create inquiry email message
                inquiry_message = EmailMessage(
                    message_id=inquiry['message_id'],
                    conversation_id=conversation_id,
                    lead_id=lead_id,
                    direction='inbound',
                    message_type='email',
                    email_headers=inquiry.get('email_headers', {}),
                    sender_email=inquiry.get('sender_email'),
                    sender_name=inquiry.get('sender_name'),
                    subject=inquiry.get('subject'),
                    body=inquiry.get('body'),
                    received_at=inquiry.get('received_at') or datetime.utcnow()
                )
                session.add(inquiry_message)

                # Create response email message
                response_message = EmailMessage(
                    message_id=response['message_id'],
                    conversation_id=conversation_id,
                    lead_id=lead_id,
                    direction='outbound',
                    message_type='email',
                    email_headers=response.get('email_headers', {}),
                    sender_email=response.get('sender_email'),
                    sender_name=response.get('sender_name'),
                    subject=response.get('subject'),
                    body=response.get('body'),
                    sent_at=response.get('received_at') or datetime.utcnow()
                )
                session.add(response_message)

                # Generate embedding for response
                response_embedding = await self.embedder.generate_embedding(
                    response.get('body', '')[:1000]  # Limit to 1000 chars
                )

                # Analyze response characteristics
                response_metadata = self._analyze_response_characteristics(response.get('body', ''))

                # Create historical response example
                historical_example = HistoricalResponseExample(
                    inquiry_lead_id=lead_id,
                    inquiry_subject=inquiry.get('subject'),
                    inquiry_body=inquiry.get('body'),
                    inquiry_sender_email=inquiry.get('sender_email'),
                    response_body=response.get('body'),
                    response_subject=response.get('subject'),
                    response_date=response.get('received_at'),
                    embedding=response_embedding,
                    response_metadata=response_metadata,
                    is_active=True
                )
                session.add(historical_example)

                await session.commit()

                logger.info(f"✅ Processed historical pair: lead_id={lead_id}")

                return lead_id

        except Exception as e:
            logger.error(f"Error processing matched pair: {e}", exc_info=True)
            return None

    def _analyze_response_characteristics(self, response_body: str) -> Dict:
        """
        Analyze characteristics of a response for metadata

        Args:
            response_body: Response email body

        Returns:
            Metadata dictionary
        """
        try:
            # Basic analysis
            words = response_body.split()
            sentences = response_body.split('.')
            paragraphs = response_body.split('\n\n')

            # Count questions
            question_count = response_body.count('?')

            # Check for common CTAs
            has_call_cta = any(phrase in response_body.lower() for phrase in [
                'call', 'phone', 'speak', 'discuss'
            ])
            has_email_cta = any(phrase in response_body.lower() for phrase in [
                'reply', 'let me know', 'send', 'email'
            ])

            metadata = {
                'word_count': len(words),
                'sentence_count': len(sentences),
                'paragraph_count': len(paragraphs),
                'question_count': question_count,
                'has_call_cta': has_call_cta,
                'has_email_cta': has_email_cta,
                'length_category': 'short' if len(words) < 100 else 'medium' if len(words) < 200 else 'long'
            }

            return metadata

        except Exception as e:
            logger.error(f"Error analyzing response characteristics: {e}")
            return {}

    async def backfill_historical_emails(
        self,
        limit: Optional[int] = None,
        folder: str = 'INBOX'
    ) -> Dict:
        """
        Main backfill process: fetch, match, and store historical emails

        Args:
            limit: Optional limit on number of emails to process
            folder: IMAP folder to search (ignored - searches both INBOX and Sent)

        Returns:
            Summary dictionary
        """
        logger.info("🚀 Starting historical email backfill...")

        try:
            # Step 1: Fetch emails from BOTH INBOX and Sent folders
            logger.info("Fetching emails from INBOX...")
            inbox_emails = await self.fetch_contact_form_emails(folder='INBOX', limit=limit)

            logger.info("Fetching emails from Sent folder...")
            sent_emails = await self.fetch_contact_form_emails(folder='Sent', limit=limit)

            # Combine all emails
            all_emails = (inbox_emails or []) + (sent_emails or [])

            if not all_emails:
                return {'status': 'error', 'message': 'No emails found'}

            logger.info(f"Total emails fetched: {len(all_emails)} (INBOX: {len(inbox_emails or [])}, Sent: {len(sent_emails or [])})")

            # Step 2: Separate inquiries and responses
            inquiries, responses = self.separate_inquiries_and_responses(all_emails)

            # Step 3: Match responses to inquiries
            matches = self.match_responses_to_inquiries(inquiries, responses)

            if not matches:
                return {
                    'status': 'warning',
                    'message': 'No matches found',
                    'emails_fetched': len(emails),
                    'inquiries': len(inquiries),
                    'responses': len(responses)
                }

            # Step 4: Process matched pairs
            processed_count = 0
            failed_count = 0

            for inquiry, response in matches:
                lead_id = await self.process_matched_pair(inquiry, response)
                if lead_id:
                    processed_count += 1
                else:
                    failed_count += 1

            logger.info(f"🎉 Backfill complete: {processed_count} processed, {failed_count} failed")

            return {
                'status': 'success',
                'emails_fetched': len(all_emails),
                'inquiries_found': len(inquiries),
                'responses_found': len(responses),
                'matches_found': len(matches),
                'processed': processed_count,
                'failed': failed_count
            }

        except Exception as e:
            logger.error(f"Error during backfill: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}


# Singleton instance
_service = None


def get_historical_backfill_service() -> HistoricalBackfillService:
    """Get singleton historical backfill service instance"""
    global _service
    if _service is None:
        _service = HistoricalBackfillService()
    return _service
