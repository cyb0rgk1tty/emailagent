# Email Thread Tracking & Duplicate Detection Implementation

## Summary

Successfully implemented comprehensive email thread tracking, duplicate detection, and conversation management for the supplement manufacturing lead intelligence system.

## What Was Implemented

### 1. Database Schema Enhancements

**New Tables:**
- **`conversations`**: Groups related emails into threads
  - Tracks thread subject, participants, message IDs
  - Timestamps for start and last activity

- **`email_messages`**: Stores all email messages (inbound + outbound)
  - Direction tracking (inbound/outbound)
  - Full email headers (RFC 5322)
  - Links to conversations and leads
  - Tracks sent drafts

**Updated `leads` Table:**
- `conversation_id`: Links lead to its conversation thread
- `parent_lead_id`: Links follow-up inquiries to original lead
- `is_duplicate`: Flags duplicate/forwarded emails
- `duplicate_of_lead_id`: References original lead for duplicates
- `lead_status`: Lifecycle state (new, responded, customer_replied, conversation_active, closed)

**Migration Applied:**
```
backend/alembic/versions/20251022_1726_c6accb3b838c_add_conversation_and_email_message_.py
```

### 2. Email Header Parsing (`services/email_service.py`)

Enhanced email parsing to extract:
- `In-Reply-To`: Identifies email this is replying to
- `References`: Full conversation chain
- `Thread-Index`: Microsoft-specific threading
- `Reply-To`, `CC`, `BCC`: Additional routing info
- Forward detection: Checks for "Fwd:", "Fw:" subject prefixes

### 3. Email Classification System (`services/email_classifier.py`)

Intelligent email classifier that categorizes incoming emails as:

**NEW_INQUIRY**
- First contact from a sender
- Creates new conversation and lead
- Generates draft response

**REPLY_TO_US**
- Customer replies to our sent emails
- Detected via `In-Reply-To` header matching our outbound messages
- Adds to existing conversation, updates lead status to "customer_replied"
- NO draft generated (requires human review)

**DUPLICATE**
- Forwarded/duplicate content from different sender
- Uses semantic similarity (embeddings + cosine similarity)
- Threshold: 0.85 similarity score
- Marks as duplicate, links to original lead
- NO draft generated

**FOLLOW_UP_INQUIRY**
- New inquiry from existing contact (same email address)
- Creates new lead but links to parent via `parent_lead_id`
- Shares or continues conversation thread
- Generates new draft response

**Classification Logic:**
1. Check reply headers → REPLY_TO_US
2. Check content similarity → DUPLICATE
3. Check sender history → FOLLOW_UP_INQUIRY
4. Default → NEW_INQUIRY

### 4. Enhanced Email Processing Pipeline (`tasks/email_tasks.py`)

Completely refactored email processing:

```python
classify_email() →
  ├─ NEW_INQUIRY     → extract → create conversation → save lead → save message → generate draft
  ├─ REPLY_TO_US     → save message → update conversation → update lead status
  ├─ DUPLICATE       → save lead (marked as duplicate) → link to original
  └─ FOLLOW_UP       → extract → link to parent → create/update conversation → save message → generate draft
```

**Key Features:**
- All emails stored in `email_messages` table for full audit trail
- Conversations track all messages chronologically
- Lead status updates reflect lifecycle (new → responded → customer_replied)
- Outbound messages (sent drafts) also recorded in conversation

### 5. Conversation API Endpoints (`api/conversations.py`)

**Endpoints:**
- `GET /api/conversations/{id}` - Get conversation with all messages
- `GET /api/conversations/lead/{lead_id}` - Get conversation for a lead
- `GET /api/conversations/lead/{lead_id}/timeline` - Chronological event timeline
- `GET /api/conversations` - List all conversations (with pagination)
- `GET /api/conversations/sender/{email}` - All conversations for a sender
- `GET /api/conversations/{id}/related-leads` - All leads in a conversation

**Timeline Includes:**
- Lead creation events
- Inbound/outbound email messages
- Draft creation, review, approval, sending
- All timestamped and sorted chronologically

### 6. Pydantic Schemas (`models/schemas.py`)

**New Schemas:**
- `ConversationResponse`: Conversation data
- `EmailMessageResponse`: Individual message data
- `ConversationWithMessages`: Conversation + all messages
- `ConversationTimeline`: Timeline view with events

**Updated Schemas:**
- `LeadExtracted`: Added conversation_id, parent_lead_id, is_duplicate, duplicate_of_lead_id, lead_status

## How It Works

### Scenario 1: New Customer Inquiry
```
1. Email arrives → Classified as NEW_INQUIRY
2. Create Conversation (thread_subject, participants, message IDs)
3. Create Lead (conversation_id set)
4. Store EmailMessage (direction='inbound')
5. Generate draft response
6. Update Lead.lead_status = 'responded'
```

### Scenario 2: Customer Replies to Our Email
```
1. Email arrives with In-Reply-To: <our-message-id>
2. Classifier checks EmailMessage table for outbound messages
3. Finds match → Classified as REPLY_TO_US
4. Store EmailMessage in existing conversation
5. Update Conversation.last_message_id, last_activity_at
6. Update Lead.lead_status = 'customer_replied'
7. NO draft generated (human review needed)
```

### Scenario 3: Forwarded/Duplicate Email
```
1. Email arrives from different sender
2. Classifier generates embedding for email body
3. Compare with recent leads (last 30 days)
4. Cosine similarity >= 0.85 → Classified as DUPLICATE
5. Create Lead with is_duplicate=True, duplicate_of_lead_id set
6. Lead.lead_status = 'closed'
7. NO draft generated
```

### Scenario 4: Follow-up from Existing Customer
```
1. Email arrives from known sender (sender_email match)
2. Content similarity < 0.85 (different inquiry)
3. Classified as FOLLOW_UP_INQUIRY
4. Create Lead with parent_lead_id pointing to original
5. Continue existing conversation or create new one
6. Store EmailMessage
7. Generate draft response for new inquiry
```

## Configuration

**Duplicate Detection Threshold:**
```python
# services/email_classifier.py
EmailClassifier(similarity_threshold=0.85)
```

**Lookback Windows:**
- Duplicate detection: 30 days
- Follow-up detection: 90 days

## API Usage Examples

### Get Conversation for a Lead
```bash
GET /api/conversations/lead/123
```

Response:
```json
{
  "conversation": {
    "id": 1,
    "thread_subject": "Probiotic Manufacturing Inquiry",
    "participants": ["john.doe@example.com"],
    "started_at": "2025-10-22T10:00:00Z",
    "last_activity_at": "2025-10-22T15:30:00Z"
  },
  "messages": [
    {
      "id": 1,
      "direction": "inbound",
      "sender_email": "john.doe@example.com",
      "subject": "Probiotic Manufacturing Inquiry",
      "body": "...",
      "received_at": "2025-10-22T10:00:00Z"
    },
    {
      "id": 2,
      "direction": "outbound",
      "sender_email": "sales@emailagent.com",
      "subject": "Re: Probiotic Manufacturing Inquiry",
      "body": "...",
      "sent_at": "2025-10-22T11:00:00Z",
      "is_draft_sent": true
    }
  ],
  "total_messages": 2,
  "lead_info": {
    "id": 123,
    "sender_email": "john.doe@example.com",
    "lead_status": "responded",
    "lead_quality_score": 8,
    "response_priority": "high"
  }
}
```

### Get Timeline
```bash
GET /api/conversations/lead/123/timeline
```

Response shows chronological events: lead creation, emails sent/received, drafts created/approved/sent.

## Database Queries

### Find all replies from customers
```sql
SELECT * FROM leads WHERE lead_status = 'customer_replied';
```

### Find all duplicates
```sql
SELECT l1.*, l2.sender_email AS original_sender
FROM leads l1
JOIN leads l2 ON l1.duplicate_of_lead_id = l2.id
WHERE l1.is_duplicate = TRUE;
```

### Get full conversation thread
```sql
SELECT em.*, l.sender_email, l.lead_quality_score
FROM email_messages em
LEFT JOIN leads l ON em.lead_id = l.id
WHERE em.conversation_id = 1
ORDER BY em.created_at;
```

### Find follow-up inquiries
```sql
SELECT l1.*, l2.subject AS original_subject
FROM leads l1
JOIN leads l2 ON l1.parent_lead_id = l2.id
WHERE l1.parent_lead_id IS NOT NULL;
```

## Benefits

1. **No Duplicate Processing**: Saves API costs, prevents customer confusion
2. **Full Conversation Context**: See entire email thread in one place
3. **Reply Detection**: Know when customers respond, route to sales team
4. **Customer History**: Track all interactions with each contact
5. **Analytics**: Measure response rates, conversation length, customer engagement
6. **Audit Trail**: Complete record of all email communications

## Testing

Integration tests created in `/backend/tests/test_thread_tracking.py` covering:
- ✅ New inquiry processing with conversation creation
- ✅ Reply detection and conversation linking
- ✅ Duplicate detection via semantic similarity
- ✅ Follow-up inquiry detection and parent linking

Note: Tests use async architecture and should be run via Celery workers for production validation.

## Files Modified/Created

**New Files:**
- `backend/services/email_classifier.py`
- `backend/api/conversations.py`
- `backend/tests/test_thread_tracking.py`
- `backend/alembic/versions/20251022_1726_c6accb3b838c_*.py`

**Modified Files:**
- `backend/models/database.py` (added Conversation, EmailMessage, updated Lead)
- `backend/models/schemas.py` (added conversation schemas)
- `backend/services/email_service.py` (header parsing)
- `backend/tasks/email_tasks.py` (classification routing)
- `backend/main.py` (registered conversation router)

## Next Steps (Future Enhancements)

1. **Sentiment Analysis**: Detect customer tone in replies
2. **Auto-Response for Simple Replies**: "Thank you" messages don't need new drafts
3. **Thread Merging**: Combine related conversations from same customer
4. **Email Search**: Full-text search across all messages in conversations
5. **Performance Metrics**: Track average response time, thread length
6. **Smart Notifications**: Alert sales team when high-priority leads reply

## Monitoring

Check classification distribution:
```bash
docker compose logs celery-worker | grep "Email classified as"
```

Monitor duplicate detection:
```bash
docker compose logs celery-worker | grep "Found duplicate"
```

## Troubleshooting

**Issue**: Replies not being detected
- Check `email_headers` in `email_messages` table
- Verify outbound messages have correct `message_id`
- Check that `In-Reply-To` header is being parsed

**Issue**: Too many duplicates being flagged
- Lower `similarity_threshold` in EmailClassifier
- Check embedding quality

**Issue**: Follow-ups not linking to parent
- Verify sender email matching (case-insensitive)
- Check lookback window (default 90 days)

---

**Status**: ✅ COMPLETE
**Version**: 2.1.0
**Date**: 2025-10-22
