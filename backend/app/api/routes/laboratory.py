"""
Módulo "Laboratorio" – Cosecha, Productos y Trazabilidad QR (PRD §3.3)
"""
import io

import qrcode
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.farm import Product, Feeding, PrecompostBatch, IBCBed
from app.schemas.farm import ProductCreate, ProductOut

router = APIRouter(prefix="/laboratory", tags=["laboratory"])
settings = get_settings()


@router.post("/products", response_model=ProductOut, status_code=201)
async def create_product(
    body: ProductCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    product = Product(**body.model_dump())
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return product


@router.get("/products", response_model=list[ProductOut])
async def list_products(
    db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
):
    result = await db.execute(select(Product).order_by(Product.created_at.desc()))
    return result.scalars().all()


@router.get("/products/{product_id}/qr")
async def generate_qr(product_id: int, db: AsyncSession = Depends(get_db)):
    """Generate a QR code PNG linking to the public traceability page."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    url = f"{settings.PUBLIC_TRACE_URL}/{product.batch_code}"
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


@router.get("/trace/{batch_code}")
async def public_trace(batch_code: str, db: AsyncSession = Depends(get_db)):
    """
    Public endpoint: scan QR -> see full traceability of a product lot.
    No auth required (public-facing).
    """
    result = await db.execute(
        select(Product).where(Product.batch_code == batch_code)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote no encontrado")

    trace = {
        "batch_code": product.batch_code,
        "product_type": product.type.value,
        "packaging": product.packaging_size,
        "harvest_date": str(product.harvest_date) if product.harvest_date else None,
        "source_ibc": None,
        "feedings": [],
    }

    if product.source_ibc_id:
        ibc_result = await db.execute(
            select(IBCBed).where(IBCBed.id == product.source_ibc_id)
        )
        ibc = ibc_result.scalar_one_or_none()
        if ibc:
            trace["source_ibc"] = {"code": ibc.code, "location": ibc.location}

        feedings_result = await db.execute(
            select(Feeding).where(Feeding.ibc_id == product.source_ibc_id)
            .order_by(Feeding.timestamp.desc())
        )
        for f in feedings_result.scalars().all():
            batch_result = await db.execute(
                select(PrecompostBatch).where(PrecompostBatch.id == f.batch_id)
            )
            batch = batch_result.scalar_one_or_none()
            trace["feedings"].append({
                "date": str(f.timestamp),
                "quantity_kg": f.quantity_kg,
                "precompost_batch": batch.code if batch else None,
                "recipe": batch.recipe_details if batch else None,
            })

    return trace
