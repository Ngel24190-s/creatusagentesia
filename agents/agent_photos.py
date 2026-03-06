"""Agent 2 — Photo Manager (Gestionnaire des Médias)

Audits, organizes, and optimizes images in the WordPress media library.
"""

import os
import re
import json
from datetime import datetime, timezone

from agents.config_loader import load_config
from agents.logger import get_logger
from agents.wp_client import WPClient
from agents.shared_state import update_section, add_blocker

logger = get_logger("photo_manager")


class PhotoManager:
    """Audits WordPress media library for SEO, naming, and usage."""

    def __init__(self, config: dict = None):
        if config is None:
            config = load_config()
        self.config = config
        self.wp = WPClient(config)
        self.issues = []
        self.photos_needed = []

    def _check_alt_text(self, media_item: dict):
        """Check if alt text is present and meaningful."""
        alt = media_item.get("alt_text", "").strip()
        media_id = media_item["id"]
        source_url = media_item.get("source_url", "")
        title = media_item.get("title", {}).get("rendered", "")

        if not alt:
            # Suggest alt text based on title and context
            suggested = self._suggest_alt_text(media_item)
            self.issues.append({
                "media_id": media_id,
                "source_url": source_url,
                "issue_type": "missing_alt",
                "message": "Texte alternatif manquant",
                "current": "",
                "suggestion": suggested,
            })
        elif len(alt) < 10:
            self.issues.append({
                "media_id": media_id,
                "source_url": source_url,
                "issue_type": "short_alt",
                "message": "Texte alternatif trop court (< 10 caractères)",
                "current": alt,
                "suggestion": self._suggest_alt_text(media_item),
            })

    def _suggest_alt_text(self, media_item: dict) -> str:
        """Generate a suggested alt text based on available context."""
        title = media_item.get("title", {}).get("rendered", "").strip()
        caption = media_item.get("caption", {}).get("rendered", "").strip()
        filename = os.path.basename(media_item.get("source_url", ""))

        # Remove HTML from caption
        if caption:
            caption = re.sub(r"<[^>]+>", "", caption).strip()

        if caption and len(caption) > 10:
            return caption
        if title and title.lower() != filename.lower().rsplit(".", 1)[0]:
            return f"NosVers — {title}"
        return "Photo NosVers — lombricompost artisanal en Dordogne"

    def _check_filename(self, media_item: dict):
        """Check if filename follows naming convention."""
        source_url = media_item.get("source_url", "")
        filename = os.path.basename(source_url)

        # Flag generic camera names
        generic_patterns = [
            r"^IMG_\d+",
            r"^DSC_?\d+",
            r"^DSCN?\d+",
            r"^P\d{7}",
            r"^photo[_-]?\d+",
            r"^image[_-]?\d+",
            r"^\d{8}[_-]",
            r"^Screenshot",
            r"^Capture",
        ]

        for pattern in generic_patterns:
            if re.match(pattern, filename, re.IGNORECASE):
                suggested = self._suggest_filename(media_item)
                self.issues.append({
                    "media_id": media_item["id"],
                    "source_url": source_url,
                    "issue_type": "generic_filename",
                    "message": f"Nom de fichier générique : {filename}",
                    "current": filename,
                    "suggestion": suggested,
                })
                break

    def _suggest_filename(self, media_item: dict) -> str:
        """Suggest a descriptive filename."""
        title = media_item.get("title", {}).get("rendered", "").strip()
        ext = os.path.splitext(media_item.get("source_url", ""))[-1] or ".jpg"

        if title:
            # Slugify the title
            slug = title.lower()
            slug = re.sub(r"[àáâãäå]", "a", slug)
            slug = re.sub(r"[èéêë]", "e", slug)
            slug = re.sub(r"[ìíîï]", "i", slug)
            slug = re.sub(r"[òóôõö]", "o", slug)
            slug = re.sub(r"[ùúûü]", "u", slug)
            slug = re.sub(r"[ç]", "c", slug)
            slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
            return f"nosvers-{slug}{ext}"

        return f"nosvers-media-{media_item['id']}{ext}"

    def _check_dimensions(self, media_item: dict):
        """Check image dimensions for hero usage suitability."""
        details = media_item.get("media_details", {})
        width = details.get("width", 0)
        height = details.get("height", 0)

        if width > 0 and width < 800:
            self.issues.append({
                "media_id": media_item["id"],
                "source_url": media_item.get("source_url", ""),
                "issue_type": "low_resolution",
                "message": f"Image trop petite pour usage héro : {width}×{height}px",
                "current": f"{width}×{height}",
                "suggestion": "Remplacer par une image d'au moins 1200px de large",
            })

    def _check_orphaned_media(self, media_items: list, pages: list, posts: list, products: list):
        """Detect media items not used in any page, post, or product."""
        all_items = pages + posts + products
        featured_ids = {item.get("featured_media") for item in all_items}

        # Build a single set of all content strings for fast substring checks
        content_parts = []
        for item in all_items:
            content_parts.append(item.get("content", {}).get("rendered", ""))
        all_content = " ".join(content_parts)

        # Check each media item
        for media in media_items:
            source_url = media.get("source_url", "")
            media_id = media["id"]
            filename = os.path.basename(source_url)

            if not source_url:
                continue

            # Check if referenced in any content or as featured image
            is_featured = media_id in featured_ids
            is_in_content = filename in all_content or source_url in all_content

            if not is_featured and not is_in_content:
                self.issues.append({
                    "media_id": media_id,
                    "source_url": source_url,
                    "issue_type": "orphaned",
                    "message": "Média non utilisé (orphelin)",
                    "current": filename,
                    "suggestion": "Vérifier si ce fichier est encore nécessaire",
                })

    def _check_products_without_images(self, products: list):
        """Find products missing featured images."""
        for product in products:
            featured = product.get("featured_media", 0)
            title = product.get("title", {}).get("rendered", "Sans titre")
            url = product.get("link", f"ID:{product.get('id')}")

            if not featured or featured == 0:
                self.photos_needed.append({
                    "product": title,
                    "url": url,
                    "need": "Photo principale du produit (image mise en avant)",
                })

    def run(self) -> str:
        """Execute the full media audit. Returns path to the report."""
        logger.info("=== Photo Manager — Starting media audit ===")
        self.issues = []
        self.photos_needed = []

        # Fetch data
        try:
            media_items = self.wp.get_media()
        except Exception as e:
            logger.error(f"Failed to fetch media: {e}")
            add_blocker(f"Cannot fetch media from WP API: {e}", "photo_manager")
            media_items = []

        try:
            pages = self.wp.get_pages()
        except Exception:
            pages = []

        try:
            posts = self.wp.get_posts()
        except Exception:
            posts = []

        try:
            products = self.wp.get_products()
        except Exception:
            products = []

        # Run checks on each media item
        for item in media_items:
            mime = item.get("mime_type", "")
            if not mime.startswith("image/"):
                continue
            self._check_alt_text(item)
            self._check_filename(item)
            self._check_dimensions(item)

        # Cross-reference checks
        self._check_orphaned_media(media_items, pages, posts, products)
        self._check_products_without_images(products)

        # Generate reports
        report_path = self._write_reports()

        # Update shared state
        update_section("media_audit",
                       status="pending",
                       report=report_path,
                       issues_count=len(self.issues),
                       photos_needed=len(self.photos_needed))

        logger.info(f"=== Photo Manager — Audit complete: {len(self.issues)} issues, "
                     f"{len(self.photos_needed)} photos needed ===")
        return report_path

    def _write_reports(self) -> str:
        """Write media audit report and photo needed list."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        reports_dir = os.path.join(base_dir, self.config["paths"]["reports_dir"])
        os.makedirs(reports_dir, exist_ok=True)

        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Markdown audit report
        md_path = os.path.join(reports_dir, f"media_audit_{date_str}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# Audit des Médias — {date_str}\n\n")
            f.write(f"**Anomalies détectées : {len(self.issues)}**\n\n")

            if not self.issues:
                f.write("Aucun problème détecté dans la bibliothèque de médias.\n")
            else:
                type_labels = {
                    "missing_alt": "Texte Alternatif Manquant",
                    "short_alt": "Texte Alternatif Trop Court",
                    "generic_filename": "Nom de Fichier Générique",
                    "low_resolution": "Résolution Insuffisante",
                    "orphaned": "Média Orphelin",
                }

                by_type = {}
                for issue in self.issues:
                    itype = issue["issue_type"]
                    by_type.setdefault(itype, []).append(issue)

                for itype, issues in by_type.items():
                    f.write(f"## {type_labels.get(itype, itype)} ({len(issues)})\n\n")
                    for i, issue in enumerate(issues, 1):
                        f.write(f"{i}. **ID {issue['media_id']}** — {issue['source_url']}\n")
                        f.write(f"   - {issue['message']}\n")
                        f.write(f"   - Actuel : `{issue.get('current', '—')}`\n")
                        f.write(f"   - Suggestion : {issue.get('suggestion', '—')}\n\n")

        # Photo needed report
        photo_path = os.path.join(reports_dir, "photo_needed.md")
        with open(photo_path, "w", encoding="utf-8") as f:
            f.write("# Photos Nécessaires\n\n")
            f.write("Les produits et pages suivants nécessitent de vraies photos.\n")
            f.write("Angel, Africa — merci de prendre ces photos quand possible.\n\n")

            if not self.photos_needed:
                f.write("Aucune photo manquante pour le moment.\n")
            else:
                for i, need in enumerate(self.photos_needed, 1):
                    f.write(f"{i}. **{need['product']}**\n")
                    f.write(f"   - URL : {need['url']}\n")
                    f.write(f"   - Ce qu'il faut photographier : {need['need']}\n\n")

        # JSON report for programmatic access
        json_path = os.path.join(reports_dir, "media_issues.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "issues": self.issues,
                "photos_needed": self.photos_needed,
            }, f, indent=2, ensure_ascii=False)

        logger.info(f"Reports written: {md_path}, {photo_path}")
        return md_path

    def apply_alt_texts(self):
        """Apply approved alt text updates via WP REST API."""
        from agents.shared_state import load_state
        state = load_state()
        if state.get("media_audit", {}).get("status") != "approved":
            logger.warning("Media corrections not approved yet. Skipping apply.")
            return

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_path = os.path.join(base_dir, self.config["paths"]["reports_dir"], "media_issues.json")

        if not os.path.exists(json_path):
            logger.warning("No media issues JSON found.")
            return

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        applied = 0
        for issue in data.get("issues", []):
            if issue["issue_type"] in ("missing_alt", "short_alt") and issue.get("suggestion"):
                try:
                    self.wp.update_media(issue["media_id"], {
                        "alt_text": issue["suggestion"]
                    })
                    applied += 1
                except Exception as e:
                    logger.error(f"Failed to update alt text for media {issue['media_id']}: {e}")

        logger.info(f"Applied {applied} alt text updates")
        update_section("media_audit", status="applied")


def run_agent(config: dict = None):
    """Entry point for the orchestrator."""
    agent = PhotoManager(config)
    return agent.run()
