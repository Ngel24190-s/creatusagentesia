"""WooCommerce sync routes - bidirectional stock & order sync."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.farm import Product, Sale
from app.services.woocommerce import woo_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/woo", tags=["woocommerce"])


@router.post("/sync-stock")
async def sync_stock_to_woo(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Push all local product stock to WooCommerce."""
    if not woo_service.is_configured:
        raise HTTPException(400, "WooCommerce no esta configurado. Configura WOOCOMMERCE_URL/KEY/SECRET en .env")

    result = await db.execute(select(Product).where(Product.sku.isnot(None), Product.sku != ""))
    products = result.scalars().all()

    synced = []
    errors = []
    for product in products:
        try:
            resp = await woo_service.update_stock(product.sku, product.stock_qty)
            if resp:
                synced.append({"sku": product.sku, "stock": product.stock_qty})
            else:
                errors.append({"sku": product.sku, "error": "Producto no encontrado en WooCommerce"})
        except Exception as e:
            errors.append({"sku": product.sku, "error": str(e)})

    return {"synced": synced, "errors": errors, "total_synced": len(synced)}


@router.post("/import-orders")
async def import_woo_orders(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Import pending WooCommerce orders as local sales."""
    if not woo_service.is_configured:
        raise HTTPException(400, "WooCommerce no esta configurado")

    orders = await woo_service.get_orders(status="processing")

    imported = []
    skipped = []
    for order in orders:
        woo_id = str(order["id"])

        # Check if already imported
        existing = await db.execute(
            select(Sale).where(Sale.woocommerce_order_id == woo_id)
        )
        if existing.scalar_one_or_none():
            skipped.append(woo_id)
            continue

        # Try to match products by SKU
        for item in order.get("line_items", []):
            sku = item.get("sku")
            if not sku:
                continue

            product_result = await db.execute(
                select(Product).where(Product.sku == sku)
            )
            product = product_result.scalar_one_or_none()
            if not product:
                continue

            sale = Sale(
                product_id=product.id,
                source="WEB",
                quantity=item.get("quantity", 1),
                amount_eur=float(item.get("total", 0)),
                woocommerce_order_id=woo_id,
            )
            db.add(sale)

            # Deduct stock
            product.stock_qty = max(0, product.stock_qty - item.get("quantity", 1))
            imported.append({"order_id": woo_id, "sku": sku, "qty": item.get("quantity", 1)})

    await db.commit()
    return {"imported": imported, "skipped": skipped, "total_imported": len(imported)}
