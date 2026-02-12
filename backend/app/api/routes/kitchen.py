"""
Módulo "Cocina" – Gestión de Insumos y Precompostaje (PRD §3.1)
"""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.farm import RawMaterial, PrecompostBatch, PrecompostStatus
from app.schemas.farm import (
    RawMaterialCreate, RawMaterialOut,
    PrecompostBatchCreate, PrecompostBatchOut,
)

router = APIRouter(prefix="/kitchen", tags=["kitchen"])

MATURITY_DAYS = 21  # Ciclo térmico de maduración


# --- Raw Materials ---

@router.post("/raw-materials", response_model=RawMaterialOut, status_code=201)
async def create_raw_material(
    body: RawMaterialCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    item = RawMaterial(**body.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


@router.get("/raw-materials", response_model=list[RawMaterialOut])
async def list_raw_materials(
    db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
):
    result = await db.execute(
        select(RawMaterial).order_by(RawMaterial.date_received.desc())
    )
    return result.scalars().all()


# --- Precompost Batches ---

@router.post("/batches", response_model=PrecompostBatchOut, status_code=201)
async def create_batch(
    body: PrecompostBatchCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    batch = PrecompostBatch(
        **body.model_dump(),
        maturity_date=body.creation_date + timedelta(days=MATURITY_DAYS),
    )
    db.add(batch)
    await db.flush()
    await db.refresh(batch)
    return batch


@router.get("/batches", response_model=list[PrecompostBatchOut])
async def list_batches(
    status_filter: PrecompostStatus | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    query = select(PrecompostBatch).order_by(PrecompostBatch.creation_date.desc())
    if status_filter:
        query = query.where(PrecompostBatch.status == status_filter)
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/batches/{batch_id}/status", response_model=PrecompostBatchOut)
async def update_batch_status(
    batch_id: int,
    new_status: PrecompostStatus,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(
        select(PrecompostBatch).where(PrecompostBatch.id == batch_id)
    )
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    batch.status = new_status
    await db.flush()
    await db.refresh(batch)
    return batch
