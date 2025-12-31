"""
API endpoints for conversation management
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime

from database import get_db
from models.database import Conversation, EmailMessage, Lead, Draft
from models.schemas import (
    ConversationResponse,
    EmailMessageResponse,
    ConversationWithMessages,
    ConversationTimeline,
    LeadExtracted
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get conversation with all messages"""

    # Get conversation
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get all messages in conversation
    result = await db.execute(
        select(EmailMessage)
        .where(EmailMessage.conversation_id == conversation_id)
        .order_by(EmailMessage.created_at.asc())
    )
    messages = result.scalars().all()

    # Get lead info
    result = await db.execute(
        select(Lead)
        .where(Lead.conversation_id == conversation_id)
        .order_by(Lead.created_at.asc())
        .limit(1)
    )
    lead = result.scalar_one_or_none()

    lead_info = None
    if lead:
        lead_info = {
            'id': lead.id,
            'sender_email': lead.sender_email,
            'sender_name': lead.sender_name,
            'lead_status': lead.lead_status,
            'lead_quality_score': lead.lead_quality_score,
            'response_priority': lead.response_priority
        }

    return {
        'conversation': ConversationResponse.model_validate(conversation),
        'messages': [EmailMessageResponse.model_validate(msg) for msg in messages],
        'total_messages': len(messages),
        'lead_info': lead_info
    }


@router.get("/lead/{lead_id}", response_model=ConversationWithMessages)
async def get_conversation_by_lead(
    lead_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get conversation for a specific lead"""

    # Get lead
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id)
    )
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if not lead.conversation_id:
        raise HTTPException(status_code=404, detail="Lead has no associated conversation")

    # Reuse the main get_conversation endpoint logic
    return await get_conversation(lead.conversation_id, db)


@router.get("/lead/{lead_id}/timeline", response_model=ConversationTimeline)
async def get_lead_timeline(
    lead_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get chronological timeline of all interactions for a lead"""

    # Get lead
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id)
    )
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    timeline = []

    # Add lead creation event
    timeline.append({
        'type': 'lead_created',
        'timestamp': lead.created_at,
        'data': {
            'lead_id': lead.id,
            'sender_email': lead.sender_email,
            'subject': lead.subject,
            'lead_quality_score': lead.lead_quality_score,
            'response_priority': lead.response_priority,
            'lead_status': lead.lead_status
        }
    })

    # Add email messages if conversation exists
    if lead.conversation_id:
        result = await db.execute(
            select(EmailMessage)
            .where(EmailMessage.conversation_id == lead.conversation_id)
            .order_by(EmailMessage.created_at.asc())
        )
        messages = result.scalars().all()

        for msg in messages:
            timeline.append({
                'type': f'email_{msg.direction}',
                'timestamp': msg.received_at or msg.sent_at or msg.created_at,
                'data': {
                    'message_id': msg.message_id,
                    'sender_email': msg.sender_email,
                    'recipient_email': msg.recipient_email,
                    'subject': msg.subject,
                    'direction': msg.direction,
                    'is_draft_sent': msg.is_draft_sent,
                    'body_preview': msg.body[:200] if msg.body else None
                }
            })

    # Add draft events
    result = await db.execute(
        select(Draft)
        .where(Draft.lead_id == lead_id)
        .order_by(Draft.created_at.asc())
    )
    drafts = result.scalars().all()

    for draft in drafts:
        # Draft created
        timeline.append({
            'type': 'draft_created',
            'timestamp': draft.created_at,
            'data': {
                'draft_id': draft.id,
                'subject_line': draft.subject_line,
                'status': draft.status,
                'confidence_score': draft.confidence_score
            }
        })

        # Draft reviewed
        if draft.reviewed_at:
            timeline.append({
                'type': 'draft_reviewed',
                'timestamp': draft.reviewed_at,
                'data': {
                    'draft_id': draft.id,
                    'reviewed_by': draft.reviewed_by,
                    'approval_feedback': draft.approval_feedback
                }
            })

        # Draft approved
        if draft.approved_at:
            timeline.append({
                'type': 'draft_approved',
                'timestamp': draft.approved_at,
                'data': {
                    'draft_id': draft.id
                }
            })

        # Draft sent
        if draft.sent_at:
            timeline.append({
                'type': 'draft_sent',
                'timestamp': draft.sent_at,
                'data': {
                    'draft_id': draft.id
                }
            })

    # Sort timeline by timestamp
    timeline.sort(key=lambda x: x['timestamp'])

    return {
        'conversation_id': lead.conversation_id,
        'lead_id': lead.id,
        'thread_subject': lead.subject or '',
        'timeline': timeline,
        'started_at': lead.created_at,
        'last_activity_at': lead.updated_at
    }


@router.get("", response_model=List[ConversationResponse])
async def list_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    active_only: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """List all conversations"""

    query = select(Conversation).order_by(Conversation.last_activity_at.desc())

    # Optional: filter for active conversations (recent activity)
    if active_only:
        from datetime import timedelta, timezone
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        query = query.where(Conversation.last_activity_at >= cutoff_date)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    conversations = result.scalars().all()

    return [ConversationResponse.model_validate(conv) for conv in conversations]


@router.get("/sender/{sender_email}", response_model=List[ConversationResponse])
async def get_conversations_by_sender(
    sender_email: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all conversations for a specific sender email"""

    # Find leads from this sender
    result = await db.execute(
        select(Lead.conversation_id)
        .where(and_(
            Lead.sender_email == sender_email.lower(),
            Lead.conversation_id.isnot(None)
        ))
        .distinct()
    )
    conversation_ids = [row[0] for row in result.all()]

    if not conversation_ids:
        return []

    # Get conversations
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id.in_(conversation_ids))
        .order_by(Conversation.last_activity_at.desc())
    )
    conversations = result.scalars().all()

    return [ConversationResponse.model_validate(conv) for conv in conversations]


@router.get("/{conversation_id}/related-leads", response_model=List[LeadExtracted])
async def get_conversation_related_leads(
    conversation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all leads associated with a conversation"""

    # Verify conversation exists
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get all leads in this conversation
    result = await db.execute(
        select(Lead)
        .where(Lead.conversation_id == conversation_id)
        .order_by(Lead.created_at.asc())
    )
    leads = result.scalars().all()

    return [LeadExtracted.model_validate(lead) for lead in leads]
