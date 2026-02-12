"""
Módulo "Producción" – Gestión de Camas IBC y Alimentación (PRD §3.2)
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.farm import IBCBed, Feeding
from app.schemas.farm import (
    IBCBedCreate, IBCBedOut,
    FeedingCreate, FeedingOut,
)

router = APIRouter(prefix="/production", tags=["production"])

FEEDING_ALERT_DAYS = 3


@router.post("/ibc", response_model=IBCBedOut, status_code=201)
async def create_ibc(
    body: IBCBedCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    ibc = IBCBed(**body.model_dump())
    db.add(ibc)
    await db.flush()
    await db.refresh(ibc)
    return ibc


@router.get("/ibc", response_model=list[IBCBedOut])
async def list_ibcs(
    db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
):
    result = await db.execute(select(IBCBed).order_by(IBCBed.code))
    return result.scalars().all()


@router.post("/feedings", response_model=FeedingOut, status_code=201)
async def create_feeding(
    body: FeedingCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    feeding = Feeding(**body.model_dump())
    db.add(feeding)
    await db.flush()
    await db.refresh(feeding)
    return feeding


@router.get("/feedings", response_model=list[FeedingOut])
async def list_feedings(
    ibc_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    query = select(Feeding).order_by(Feeding.timestamp.desc())
    if ibc_id:
        query = query.where(Feeding.ibc_id == ibc_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/alerts/hungry-ibcs", response_model=list[IBCBedOut])
async def get_hungry_ibcs(
    db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
):
    """IBCs that haven't been fed in the last 3 days (PRD §3.2 alerts)."""
    threshold = datetime.now(timezone.utc) - timedelta(days=FEEDING_ALERT_DAYS)

    # Subquery: IBCs with recent feedings
    fed_recently = (
        select(Feeding.ibc_id)
        .where(Feeding.timestamp >= threshold)
        .distinct()
        .subquery()
    )

    result = await db.execute(
        select(IBCBed).where(IBCBed.id.notin_(select(fed_recently.c.ibc_id)))
    )
    return result.scalars().all()
