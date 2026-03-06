#!/usr/bin/env python3
"""Test script for WordPress REST API connectivity."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.config_loader import load_config
from agents.wp_client import WPClient


def main():
    print("NosVers — WordPress API Connection Test")
    print("=" * 50)

    config = load_config()
    client = WPClient(config)

    # Test 1: Basic connectivity
    print("\n[1] Testing basic connectivity...")
    result = client.test_connection()
    if result["success"]:
        print(f"    OK — Site: {result.get('name')}")
        print(f"    URL: {result.get('url')}")
        namespaces = result.get("namespaces", [])
        print(f"    Namespaces: {len(namespaces)} available")
        print(f"    WooCommerce: {'Yes' if any('wc' in ns for ns in namespaces) else 'No'}")
    else:
        print(f"    FAILED — {result.get('error')}")
        sys.exit(1)

    # Test 2: Authentication
    print("\n[2] Testing authentication...")
    auth = client.test_auth()
    if auth["success"]:
        print(f"    OK — User: {auth.get('user')}")
        print(f"    Roles: {auth.get('roles', [])}")
    else:
        print(f"    FAILED — {auth.get('error')}")

    # Test 3: Fetch pages
    print("\n[3] Fetching pages...")
    try:
        pages = client.get_pages()
        print(f"    OK — {len(pages)} pages found")
        for p in pages[:5]:
            title = p.get("title", {}).get("rendered", "?")
            print(f"    - {title}")
    except Exception as e:
        print(f"    FAILED — {e}")

    # Test 4: Fetch media
    print("\n[4] Fetching media...")
    try:
        media = client.get_media()
        print(f"    OK — {len(media)} media items found")
        images = [m for m in media if m.get("mime_type", "").startswith("image/")]
        print(f"    Images: {len(images)}")
    except Exception as e:
        print(f"    FAILED — {e}")

    # Test 5: Fetch products
    print("\n[5] Fetching WooCommerce products...")
    try:
        products = client.get_products()
        print(f"    OK — {len(products)} products found")
        for p in products[:5]:
            title = p.get("title", {}).get("rendered", "?")
            print(f"    - {title}")
    except Exception as e:
        print(f"    FAILED — {e}")

    print("\n" + "=" * 50)
    print("Connection test complete.\n")


if __name__ == "__main__":
    main()
