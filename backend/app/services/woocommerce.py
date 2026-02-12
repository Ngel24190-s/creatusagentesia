"""
WooCommerce Sync Service (PRD §3.4)
Bidirectional stock synchronization with WooCommerce.
"""
import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class WooCommerceService:
    """Client for WooCommerce REST API v3."""

    def __init__(self):
        self.base_url = f"{settings.WOOCOMMERCE_URL}/wp-json/wc/v3"
        self.auth = (settings.WOOCOMMERCE_KEY, settings.WOOCOMMERCE_SECRET)

    @property
    def is_configured(self) -> bool:
        return bool(settings.WOOCOMMERCE_URL and settings.WOOCOMMERCE_KEY)

    async def update_stock(self, sku: str, quantity: int) -> dict | None:
        """Push local stock quantity to WooCommerce product by SKU."""
        if not self.is_configured:
            logger.warning("WooCommerce not configured, skipping stock sync")
            return None

        async with httpx.AsyncClient() as client:
            # Find product by SKU
            resp = await client.get(
                f"{self.base_url}/products",
                params={"sku": sku},
                auth=self.auth,
            )
            resp.raise_for_status()
            products = resp.json()
            if not products:
                logger.warning(f"No WooCommerce product found for SKU: {sku}")
                return None

            product_id = products[0]["id"]
            # Update stock
            resp = await client.put(
                f"{self.base_url}/products/{product_id}",
                json={"stock_quantity": quantity, "manage_stock": True},
                auth=self.auth,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_orders(self, status: str = "processing") -> list[dict]:
        """Fetch recent orders from WooCommerce to sync into local sales."""
        if not self.is_configured:
            return []

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/orders",
                params={"status": status, "per_page": 50},
                auth=self.auth,
            )
            resp.raise_for_status()
            return resp.json()


woo_service = WooCommerceService()
