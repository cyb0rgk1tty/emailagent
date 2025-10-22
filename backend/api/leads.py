"""
Leads API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from datetime import datetime

from database import get_db
from models.database import Lead
from models.schemas import LeadCreate, LeadExtracted, LeadUpdate

router = APIRouter()


@router.get("/", response_model=List[LeadExtracted])
async def get_leads(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    product_type: Optional[str] = None,
    priority: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all leads with optional filtering"""
    query = select(Lead).order_by(desc(Lead.received_at))

    # Apply filters
    if product_type:
        query = query.where(Lead.product_type.contains([product_type]))
    if priority:
        query = query.where(Lead.response_priority == priority)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    leads = result.scalars().all()
    return leads


@router.get("/{lead_id}", response_model=LeadExtracted)
async def get_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific lead by ID"""
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return lead


@router.post("/", response_model=LeadExtracted)
async def create_lead(lead: LeadCreate, db: AsyncSession = Depends(get_db)):
    """Create a new lead"""
    db_lead = Lead(**lead.model_dump())
    db.add(db_lead)
    await db.commit()
    await db.refresh(db_lead)
    return db_lead


@router.put("/{lead_id}", response_model=LeadExtracted)
async def update_lead(
    lead_id: int,
    lead_update: LeadUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a lead"""
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Update fields
    for field, value in lead_update.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)

    await db.commit()
    await db.refresh(lead)
    return lead


@router.get("/stats/count")
async def get_leads_count(db: AsyncSession = Depends(get_db)):
    """Get total leads count"""
    result = await db.execute(select(func.count(Lead.id)))
    count = result.scalar()
    return {"total_leads": count}
