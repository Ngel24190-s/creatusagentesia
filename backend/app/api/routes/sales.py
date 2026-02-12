"""
Módulo "Dinero" – Ventas y Dashboard Financiero (PRD §3.4)
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.farm import Sale, Product, IBCBed, PrecompostBatch, PrecompostStatus
from app.schemas.farm import SaleCreate, SaleOut, DashboardOut

router = APIRouter(prefix="/sales", tags=["sales"])


@router.post("/", response_model=SaleOut, status_code=201)
async def create_sale(
    body: SaleCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    # Verify product exists and has stock
    result = await db.execute(select(Product).where(Product.id == body.product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    if product.stock_qty < body.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock insuficiente. Disponible: {product.stock_qty}",
        )

    product.stock_qty -= body.quantity

    sale = Sale(**body.model_dump())
    db.add(sale)
    await db.flush()
    await db.refresh(sale)
    return sale


@router.get("/", response_model=list[SaleOut])
async def list_sales(
    db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
):
    result = await db.execute(select(Sale).order_by(Sale.date.desc()))
    return result.scalars().all()


@router.get("/dashboard", response_model=DashboardOut)
async def dashboard(
    db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
):
    now = datetime.now(timezone.utc)

    # Monthly revenue
    revenue_result = await db.execute(
        select(func.coalesce(func.sum(Sale.amount_eur), 0.0)).where(
            extract("year", Sale.date) == now.year,
            extract("month", Sale.date) == now.month,
        )
    )
    total_revenue = float(revenue_result.scalar())

    # Counts
    ibc_count = (await db.execute(select(func.count(IBCBed.id)))).scalar()
    stock_count = (await db.execute(
        select(func.coalesce(func.sum(Product.stock_qty), 0))
    )).scalar()
    pending_batches = (await db.execute(
        select(func.count(PrecompostBatch.id)).where(
            PrecompostBatch.status == PrecompostStatus.FERMENTING
        )
    )).scalar()

    target = 1800.0
    return DashboardOut(
        total_revenue_eur=total_revenue,
        monthly_target_eur=target,
        progress_pct=round((total_revenue / target) * 100, 1) if target > 0 else 0,
        total_ibc_beds=ibc_count,
        total_products_in_stock=int(stock_count),
        pending_precompost_batches=pending_batches,
    )
