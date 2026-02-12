"""
Background task scheduler for NosVers.

Runs periodic tasks:
- WooCommerce stock sync every 30 minutes
- WooCommerce order import every 15 minutes
- Farm health check every hour (logs alerts)
"""
import asyncio
import logging
from datetime import datetime

from app.core.database import async_session
from app.services.woocommerce import woo_service
from app.agents.farm_agent import FarmAgent
from sqlalchemy import select
from app.models.farm import Product

logger = logging.getLogger("nosvers.scheduler")


async def sync_stock_task():
    """Push local stock to WooCommerce."""
    try:
        if not woo_service.is_configured:
            return

        async with async_session() as db:
            result = await db.execute(
                select(Product).where(Product.sku.isnot(None), Product.sku != "")
            )
            products = result.scalars().all()

            for product in products:
                try:
                    await woo_service.update_stock(product.sku, product.stock_qty)
                    logger.info(f"Stock synced: {product.sku} = {product.stock_qty}")
                except Exception as e:
                    logger.error(f"Stock sync failed for {product.sku}: {e}")

    except Exception as e:
        logger.error(f"Stock sync task error: {e}")


async def import_orders_task():
    """Import new WooCommerce orders."""
    try:
        if not woo_service.is_configured:
            return

        async with async_session() as db:
            from app.models.farm import Sale
            orders = await woo_service.get_orders(status="processing")

            for order in orders:
                woo_id = str(order["id"])
                existing = await db.execute(
                    select(Sale).where(Sale.woocommerce_order_id == woo_id)
                )
                if existing.scalar_one_or_none():
                    continue

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
                    product.stock_qty = max(0, product.stock_qty - item.get("quantity", 1))

                await db.commit()
                logger.info(f"Imported WooCommerce order #{woo_id}")

    except Exception as e:
        logger.error(f"Order import task error: {e}")


async def health_check_task():
    """Run farm health analysis and log alerts."""
    try:
        async with async_session() as db:
            agent = FarmAgent(db)
            health = await agent.get_health_score()
            score = health["overall_score"]
            alerts = health.get("alerts", [])

            logger.info(f"Farm health: {score}/100 | Alerts: {len(alerts)}")
            for alert in alerts:
                logger.warning(f"Farm alert: {alert}")

    except Exception as e:
        logger.error(f"Health check task error: {e}")


async def run_scheduler():
    """Main scheduler loop - runs background tasks at intervals."""
    logger.info("NosVers scheduler started")

    while True:
        now = datetime.utcnow()
        minute = now.minute

        try:
            # Every 15 minutes: import orders
            if minute % 15 == 0:
                await import_orders_task()

            # Every 30 minutes: sync stock
            if minute % 30 == 0:
                await sync_stock_task()

            # Every hour: health check
            if minute == 0:
                await health_check_task()

        except Exception as e:
            logger.error(f"Scheduler loop error: {e}")

        # Sleep until next minute
        await asyncio.sleep(60)
