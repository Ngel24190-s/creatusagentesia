"""WordPress REST API client for NosVers."""

import time
import requests
from requests.auth import HTTPBasicAuth
from agents.config_loader import load_config
from agents.logger import get_logger

logger = get_logger("wp_client")


class WPClient:
    """Client for WordPress REST API and WooCommerce."""

    def __init__(self, config: dict = None):
        if config is None:
            config = load_config()
        wp = config["wordpress"]
        self.base_url = wp["site_url"].rstrip("/")
        self.api_url = f"{self.base_url}/wp-json"
        self.auth = HTTPBasicAuth(wp["api_user"], wp["api_password"])
        self.litespeed_purge = wp.get("litespeed_purge", False)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({
            "User-Agent": "NosVers-AgentEcosystem/1.0",
            "Accept": "application/json",
        })

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an API request with retry logic."""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        retries = 3
        for attempt in range(retries):
            try:
                resp = self.session.request(method, url, timeout=30, **kwargs)
                resp.raise_for_status()
                return resp
            except requests.exceptions.ConnectionError as e:
                if attempt < retries - 1:
                    wait = 2 ** (attempt + 1)
                    logger.warning(f"Connection error (attempt {attempt + 1}), retrying in {wait}s: {e}")
                    time.sleep(wait)
                else:
                    logger.error(f"Connection failed after {retries} attempts: {e}")
                    raise
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error {resp.status_code} for {url}: {e}")
                raise

    def _get_all_paginated(self, endpoint: str, params: dict = None) -> list:
        """Fetch all items from a paginated WP REST API endpoint."""
        if params is None:
            params = {}
        params.setdefault("per_page", 100)
        params["page"] = 1
        all_items = []

        while True:
            resp = self._request("GET", endpoint, params=params)
            items = resp.json()
            if not items:
                break
            all_items.extend(items)
            total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
            if params["page"] >= total_pages:
                break
            params["page"] += 1

        return all_items

    # --- Pages ---

    def get_pages(self) -> list:
        """Fetch all published WordPress pages."""
        logger.info("Fetching all WordPress pages...")
        pages = self._get_all_paginated("wp/v2/pages", {"status": "publish"})
        logger.info(f"Fetched {len(pages)} pages")
        return pages

    def update_page(self, page_id: int, data: dict) -> dict:
        """Update a WordPress page."""
        logger.info(f"Updating page {page_id}")
        resp = self._request("POST", f"wp/v2/pages/{page_id}", json=data)
        return resp.json()

    # --- Posts ---

    def get_posts(self) -> list:
        """Fetch all published WordPress posts."""
        logger.info("Fetching all WordPress posts...")
        posts = self._get_all_paginated("wp/v2/posts", {"status": "publish"})
        logger.info(f"Fetched {len(posts)} posts")
        return posts

    def update_post(self, post_id: int, data: dict) -> dict:
        """Update a WordPress post."""
        logger.info(f"Updating post {post_id}")
        resp = self._request("POST", f"wp/v2/posts/{post_id}", json=data)
        return resp.json()

    # --- WooCommerce Products ---

    def get_products(self) -> list:
        """Fetch all published WooCommerce products."""
        logger.info("Fetching all WooCommerce products...")
        products = self._get_all_paginated("wp/v2/product", {"status": "publish"})
        logger.info(f"Fetched {len(products)} products")
        return products

    def update_product(self, product_id: int, data: dict) -> dict:
        """Update a WooCommerce product."""
        logger.info(f"Updating product {product_id}")
        resp = self._request("POST", f"wp/v2/product/{product_id}", json=data)
        return resp.json()

    # --- Media ---

    def get_media(self) -> list:
        """Fetch all media items."""
        logger.info("Fetching all media items...")
        media = self._get_all_paginated("wp/v2/media")
        logger.info(f"Fetched {len(media)} media items")
        return media

    def update_media(self, media_id: int, data: dict) -> dict:
        """Update media item metadata (alt text, title, etc.)."""
        logger.info(f"Updating media {media_id}")
        resp = self._request("POST", f"wp/v2/media/{media_id}", json=data)
        return resp.json()

    # --- Cache ---

    def purge_litespeed_cache(self):
        """Purge LiteSpeed cache if configured."""
        if not self.litespeed_purge:
            return
        try:
            # LiteSpeed cache purge via REST API
            self._request("GET", "litespeed/v1/purge/all")
            logger.info("LiteSpeed cache purged successfully")
        except Exception as e:
            logger.warning(f"LiteSpeed cache purge failed (non-critical): {e}")

    # --- Connectivity Test ---

    def test_connection(self) -> dict:
        """Test API connectivity and return site info."""
        logger.info(f"Testing connection to {self.base_url}...")
        try:
            resp = self._request("GET", "")
            info = resp.json()
            logger.info(f"Connected to: {info.get('name', 'Unknown')} — {info.get('description', '')}")
            return {
                "success": True,
                "name": info.get("name"),
                "description": info.get("description"),
                "url": info.get("url"),
                "namespaces": info.get("namespaces", []),
            }
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {"success": False, "error": str(e)}

    def test_auth(self) -> dict:
        """Test authenticated access."""
        logger.info("Testing authenticated access...")
        try:
            resp = self._request("GET", "wp/v2/users/me")
            user = resp.json()
            logger.info(f"Authenticated as: {user.get('name', 'Unknown')}")
            return {
                "success": True,
                "user": user.get("name"),
                "slug": user.get("slug"),
                "roles": user.get("roles", []),
            }
        except Exception as e:
            logger.error(f"Auth test failed: {e}")
            return {"success": False, "error": str(e)}
