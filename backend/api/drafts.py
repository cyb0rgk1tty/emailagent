"""
Drafts API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from datetime import datetime

from database import get_db
from models.database import Draft, Lead
from models.schemas import DraftCreate, DraftResponse, DraftUpdate, DraftApproval

router = APIRouter()


@router.get("/", response_model=List[DraftResponse])
async def get_drafts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all drafts with optional filtering"""
    query = select(Draft).order_by(desc(Draft.created_at))

    if status:
        query = query.where(Draft.status == status)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    drafts = result.scalars().all()
    return drafts


@router.get("/pending", response_model=List[DraftResponse])
async def get_pending_drafts(
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get pending drafts for approval"""
    query = (
        select(Draft)
        .where(Draft.status == 'pending')
        .order_by(desc(Draft.created_at))
        .limit(limit)
    )

    result = await db.execute(query)
    drafts = result.scalars().all()
    return drafts


@router.get("/{draft_id}", response_model=DraftResponse)
async def get_draft(draft_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific draft by ID"""
    result = await db.execute(select(Draft).where(Draft.id == draft_id))
    draft = result.scalar_one_or_none()

    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    return draft


@router.post("/", response_model=DraftResponse)
async def create_draft(draft: DraftCreate, db: AsyncSession = Depends(get_db)):
    """Create a new draft"""
    # Verify lead exists
    lead_result = await db.execute(select(Lead).where(Lead.id == draft.lead_id))
    if not lead_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Lead not found")

    db_draft = Draft(**draft.model_dump())
    db.add(db_draft)
    await db.commit()
    await db.refresh(db_draft)
    return db_draft


@router.put("/{draft_id}", response_model=DraftResponse)
async def update_draft(
    draft_id: int,
    draft_update: DraftUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a draft"""
    result = await db.execute(select(Draft).where(Draft.id == draft_id))
    draft = result.scalar_one_or_none()

    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    # Update fields
    for field, value in draft_update.model_dump(exclude_unset=True).items():
        setattr(draft, field, value)

    await db.commit()
    await db.refresh(draft)
    return draft


@router.post("/{draft_id}/approve", response_model=DraftResponse)
async def approve_draft(
    draft_id: int,
    approval: DraftApproval,
    db: AsyncSession = Depends(get_db)
):
    """Approve, reject, or edit a draft"""
    result = await db.execute(select(Draft).where(Draft.id == draft_id))
    draft = result.scalar_one_or_none()

    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    draft.reviewed_by = approval.reviewed_by or "system"
    draft.reviewed_at = datetime.utcnow()

    if approval.action == "approve":
        draft.status = "approved"
        draft.approved_at = datetime.utcnow()

        # Queue email sending task
        from tasks.email_tasks import send_approved_draft
        await db.commit()
        send_approved_draft.delay(draft_id)

    elif approval.action == "reject":
        draft.status = "rejected"
        draft.approval_feedback = approval.feedback

    elif approval.action == "edit":
        draft.status = "edited"
        if approval.edited_content:
            draft.draft_content = approval.edited_content
        if approval.edited_subject:
            draft.subject_line = approval.edited_subject
        draft.edit_summary = approval.feedback

    elif approval.action == "save":
        # Keep status as pending, just save any edits
        if approval.edited_content:
            draft.draft_content = approval.edited_content
        if approval.edited_subject:
            draft.subject_line = approval.edited_subject

    # Save customer sentiment feedback if provided
    if hasattr(approval, 'customer_sentiment') and approval.customer_sentiment:
        draft.customer_sentiment = approval.customer_sentiment
        draft.customer_replied = True

    await db.commit()
    await db.refresh(draft)
    return draft


@router.get("/stats/count")
async def get_drafts_count(db: AsyncSession = Depends(get_db)):
    """Get drafts count by status"""
    total_result = await db.execute(select(func.count(Draft.id)))
    total = total_result.scalar()

    pending_result = await db.execute(
        select(func.count(Draft.id)).where(Draft.status == 'pending')
    )
    pending = pending_result.scalar()

    return {
        "total_drafts": total,
        "pending_drafts": pending
    }
