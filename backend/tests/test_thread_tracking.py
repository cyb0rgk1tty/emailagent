"""
Integration tests for email thread tracking and duplicate detection
"""
import asyncio
from datetime import datetime


async def test_new_inquiry():
    """Test new inquiry email processing with conversation creation"""
    print("\n" + "=" * 70)
    print("TEST 1: New Inquiry Processing")
    print("=" * 70)

    from tasks.email_tasks import process_email
    from database import get_db_session
    from models.database import Lead, Conversation, EmailMessage
    from sqlalchemy import select, delete

    # Clean up test data
    async with get_db_session() as session:
        await session.execute(delete(EmailMessage).where(EmailMessage.message_id.like('%test-new-inquiry%')))
        await session.execute(delete(Lead).where(Lead.message_id.like('%test-new-inquiry%')))
        await session.execute(delete(Conversation).where(Conversation.initial_message_id.like('%test-new-inquiry%')))
        await session.commit()

    # Test email data
    email_data = {
        'message_id': '<test-new-inquiry-001@example.com>',
        'sender_email': 'john.doe@example.com',
        'sender_name': 'John Doe',
        'subject': 'Probiotic Manufacturing Inquiry',
        'body': 'Hello, I am looking for a manufacturer for probiotic supplements. Can you help?',
        'received_at': datetime.utcnow(),
        'email_headers': {
            'in_reply_to': '',
            'references': '',
            'references_list': [],
            'is_likely_forward': False
        }
    }

    # Process email
    result = process_email(email_data)

    print(f"✓ Process Status: {result['status']}")
    print(f"✓ Classification: {result.get('classification', 'N/A')}")
    print(f"✓ Lead ID: {result.get('lead_id')}")
    print(f"✓ Conversation ID: {result.get('conversation_id')}")
    print(f"✓ Draft ID: {result.get('draft_id')}")

    # Verify conversation was created
    async with get_db_session() as session:
        result_db = await session.execute(
            select(Conversation).where(Conversation.id == result.get('conversation_id'))
        )
        conversation = result_db.scalar_one_or_none()

        result_db = await session.execute(
            select(EmailMessage).where(EmailMessage.conversation_id == result.get('conversation_id'))
        )
        messages = result_db.scalars().all()

        print(f"✓ Conversation created: {conversation is not None}")
        print(f"✓ Email messages in conversation: {len(messages)}")
        print(f"✓ Lead status: {conversation and 'created' or 'failed'}")

    assert result['status'] == 'success'
    assert result['classification'] == 'new_inquiry'
    assert conversation is not None
    assert len(messages) == 1
    print("\n✅ TEST 1 PASSED: New inquiry creates conversation and stores message")
    return result


async def test_reply_detection():
    """Test reply email detection and conversation linking"""
    print("\n" + "=" * 70)
    print("TEST 2: Reply Detection")
    print("=" * 70)

    from tasks.email_tasks import process_email
    from database import get_db_session
    from models.database import Lead, Conversation, EmailMessage
    from sqlalchemy import select, delete

    # Clean up test data
    async with get_db_session() as session:
        await session.execute(delete(EmailMessage).where(EmailMessage.message_id.like('%test-reply%')))
        await session.execute(delete(Lead).where(Lead.message_id.like('%test-reply%')))
        await session.execute(delete(Conversation).where(Conversation.initial_message_id.like('%test-reply%')))
        await session.commit()

    # Create initial email
    initial_email = {
        'message_id': '<test-reply-initial@example.com>',
        'sender_email': 'jane.smith@example.com',
        'sender_name': 'Jane Smith',
        'subject': 'Vitamin D Supplement Inquiry',
        'body': 'Can you manufacture vitamin D supplements?',
        'received_at': datetime.utcnow(),
        'email_headers': {
            'in_reply_to': '',
            'references': '',
            'references_list': [],
            'is_likely_forward': False
        }
    }

    initial_result = process_email(initial_email)
    conversation_id = initial_result.get('conversation_id')

    # Simulate sending our response (create outbound message)
    async with get_db_session() as session:
        outbound_message = EmailMessage(
            message_id='<our-response-001@emailagent.local>',
            conversation_id=conversation_id,
            lead_id=initial_result.get('lead_id'),
            direction='outbound',
            message_type='email',
            email_headers={},
            sender_email='sales@emailagent.com',
            sender_name='Sales Team',
            recipient_email='jane.smith@example.com',
            subject='Re: Vitamin D Supplement Inquiry',
            body='Yes, we can help with that!',
            sent_at=datetime.utcnow()
        )
        session.add(outbound_message)
        await session.commit()

    # Now send a reply
    reply_email = {
        'message_id': '<test-reply-customer-001@example.com>',
        'sender_email': 'jane.smith@example.com',
        'sender_name': 'Jane Smith',
        'subject': 'Re: Vitamin D Supplement Inquiry',
        'body': 'Great! What is your minimum order quantity?',
        'received_at': datetime.utcnow(),
        'email_headers': {
            'in_reply_to': '<our-response-001@emailagent.local>',
            'references': '<test-reply-initial@example.com> <our-response-001@emailagent.local>',
            'references_list': ['<test-reply-initial@example.com>', '<our-response-001@emailagent.local>'],
            'is_likely_forward': False
        }
    }

    reply_result = process_email(reply_email)

    print(f"✓ Process Status: {reply_result['status']}")
    print(f"✓ Classification: {reply_result.get('classification', 'N/A')}")
    print(f"✓ Conversation ID: {reply_result.get('conversation_id')}")

    # Verify reply was added to conversation
    async with get_db_session() as session:
        result_db = await session.execute(
            select(EmailMessage).where(EmailMessage.conversation_id == conversation_id)
        )
        messages = result_db.scalars().all()

        # Check lead status updated
        result_db = await session.execute(
            select(Lead).where(Lead.id == initial_result.get('lead_id'))
        )
        lead = result_db.scalar_one_or_none()

        print(f"✓ Messages in conversation: {len(messages)}")
        print(f"✓ Lead status updated to: {lead.lead_status}")

    assert reply_result['status'] == 'success'
    assert reply_result['classification'] == 'reply_to_us'
    assert len(messages) == 3  # Initial + Our response + Customer reply
    assert lead.lead_status == 'customer_replied'
    print("\n✅ TEST 2 PASSED: Reply detected and linked to conversation")


async def test_duplicate_detection():
    """Test duplicate email detection (forwarded emails)"""
    print("\n" + "=" * 70)
    print("TEST 3: Duplicate Detection")
    print("=" * 70)

    from tasks.email_tasks import process_email
    from database import get_db_session
    from models.database import Lead
    from sqlalchemy import select, delete

    # Clean up test data
    async with get_db_session() as session:
        await session.execute(delete(Lead).where(Lead.message_id.like('%test-duplicate%')))
        await session.commit()

    # Create original email
    original_email = {
        'message_id': '<test-duplicate-original@example.com>',
        'sender_email': 'original@example.com',
        'sender_name': 'Original Sender',
        'subject': 'Unique Collagen Peptide Manufacturing Request',
        'body': 'I need a manufacturer for a very specific type of marine collagen peptides with particular molecular weight distribution.',
        'received_at': datetime.utcnow(),
        'email_headers': {
            'in_reply_to': '',
            'references': '',
            'references_list': [],
            'is_likely_forward': False
        }
    }

    original_result = process_email(original_email)
    print(f"✓ Original email processed: Lead ID {original_result.get('lead_id')}")

    # Create forwarded/duplicate email (same content, different sender)
    duplicate_email = {
        'message_id': '<test-duplicate-forward@example.com>',
        'sender_email': 'forwarded@example.com',
        'sender_name': 'Forwarded Sender',
        'subject': 'Fwd: Unique Collagen Peptide Manufacturing Request',
        'body': 'I need a manufacturer for a very specific type of marine collagen peptides with particular molecular weight distribution.',
        'received_at': datetime.utcnow(),
        'email_headers': {
            'in_reply_to': '',
            'references': '',
            'references_list': [],
            'is_likely_forward': True
        }
    }

    duplicate_result = process_email(duplicate_email)

    print(f"✓ Process Status: {duplicate_result['status']}")
    print(f"✓ Classification: {duplicate_result.get('classification', 'N/A')}")
    print(f"✓ Original Lead ID: {duplicate_result.get('original_lead_id')}")
    print(f"✓ Similarity Score: {duplicate_result.get('similarity_score', 0):.2f}")

    # Verify duplicate was marked
    async with get_db_session() as session:
        result_db = await session.execute(
            select(Lead).where(Lead.message_id == '<test-duplicate-forward@example.com>')
        )
        duplicate_lead = result_db.scalar_one_or_none()

        if duplicate_lead:
            print(f"✓ Duplicate lead marked: {duplicate_lead.is_duplicate}")
            print(f"✓ Duplicate of lead: {duplicate_lead.duplicate_of_lead_id}")

    assert duplicate_result['status'] == 'success'
    assert duplicate_result['classification'] == 'duplicate'
    assert duplicate_lead.is_duplicate is True
    assert duplicate_lead.duplicate_of_lead_id == original_result.get('lead_id')
    print("\n✅ TEST 3 PASSED: Duplicate email detected and linked to original")


async def test_follow_up_inquiry():
    """Test follow-up inquiry from existing contact"""
    print("\n" + "=" * 70)
    print("TEST 4: Follow-up Inquiry Detection")
    print("=" * 70)

    from tasks.email_tasks import process_email
    from database import get_db_session
    from models.database import Lead
    from sqlalchemy import select, delete

    # Clean up test data
    async with get_db_session() as session:
        await session.execute(delete(Lead).where(Lead.message_id.like('%test-followup%')))
        await session.commit()

    # Create initial email
    initial_email = {
        'message_id': '<test-followup-initial@example.com>',
        'sender_email': 'repeat.customer@example.com',
        'sender_name': 'Repeat Customer',
        'subject': 'Probiotic Manufacturing',
        'body': 'I need help with probiotic manufacturing.',
        'received_at': datetime.utcnow(),
        'email_headers': {
            'in_reply_to': '',
            'references': '',
            'references_list': [],
            'is_likely_forward': False
        }
    }

    initial_result = process_email(initial_email)
    print(f"✓ Initial email processed: Lead ID {initial_result.get('lead_id')}")

    # Create follow-up inquiry (same sender, different question)
    followup_email = {
        'message_id': '<test-followup-second@example.com>',
        'sender_email': 'repeat.customer@example.com',
        'sender_name': 'Repeat Customer',
        'subject': 'Fish Oil Supplement Manufacturing',
        'body': 'Now I also need help with fish oil supplement manufacturing.',
        'received_at': datetime.utcnow(),
        'email_headers': {
            'in_reply_to': '',
            'references': '',
            'references_list': [],
            'is_likely_forward': False
        }
    }

    followup_result = process_email(followup_email)

    print(f"✓ Process Status: {followup_result['status']}")
    print(f"✓ Classification: {followup_result.get('classification', 'N/A')}")
    print(f"✓ New Lead ID: {followup_result.get('lead_id')}")
    print(f"✓ Parent Lead ID: {followup_result.get('parent_lead_id')}")

    # Verify follow-up was linked to parent
    async with get_db_session() as session:
        result_db = await session.execute(
            select(Lead).where(Lead.id == followup_result.get('lead_id'))
        )
        followup_lead = result_db.scalar_one_or_none()

        print(f"✓ Follow-up lead parent: {followup_lead.parent_lead_id}")
        print(f"✓ Days since last contact: {followup_result.get('days_since_last_contact', 0)}")

    assert followup_result['status'] == 'success'
    assert followup_result['classification'] == 'follow_up_inquiry'
    assert followup_lead.parent_lead_id == initial_result.get('lead_id')
    print("\n✅ TEST 4 PASSED: Follow-up inquiry linked to original lead")


async def main():
    """Run all integration tests"""
    print("\n" + "=" * 70)
    print("THREAD TRACKING AND DUPLICATE DETECTION INTEGRATION TESTS")
    print("=" * 70)

    try:
        # Test 1: New inquiry
        await test_new_inquiry()

        # Test 2: Reply detection
        await test_reply_detection()

        # Test 3: Duplicate detection
        await test_duplicate_detection()

        # Test 4: Follow-up inquiry
        await test_follow_up_inquiry()

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
