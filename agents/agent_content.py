"""Agent 1 — Content Guardian (Gardien du Contenu)

Audits and corrects all text content on nosvers.com for consistency,
French quality, SEO coherence, and brand alignment.
"""

import os
import re
import json
from datetime import datetime, timezone
from html import unescape

from agents.config_loader import load_config
from agents.logger import get_logger
from agents.wp_client import WPClient
from agents.shared_state import update_section, add_blocker

logger = get_logger("content_guardian")


def _strip_html(html: str) -> str:
    """Remove HTML tags and decode entities."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _extract_headings(html: str) -> list:
    """Extract heading hierarchy from HTML content."""
    headings = []
    for match in re.finditer(r"<(h[1-6])[^>]*>(.*?)</\1>", html, re.IGNORECASE | re.DOTALL):
        level = int(match.group(1)[1])
        text = _strip_html(match.group(2))
        headings.append({"level": level, "text": text})
    return headings


class ContentGuardian:
    """Audits WordPress content for grammar, brand voice, and SEO."""

    def __init__(self, config: dict = None):
        if config is None:
            config = load_config()
        self.config = config
        self.wp = WPClient(config)
        self.seo_config = config.get("seo", {})
        self.keywords = self.seo_config.get("primary_keywords", [])
        self.forbidden = self.seo_config.get("brand_voice", {}).get("forbidden_phrases", [])
        self.issues = []
        self._lt_tool = None

    def _get_language_tool(self):
        """Lazy-load LanguageTool for French grammar checking."""
        if self._lt_tool is None:
            try:
                import language_tool_python
                self._lt_tool = language_tool_python.LanguageTool("fr")
                logger.info("LanguageTool initialized for French")
            except Exception as e:
                logger.warning(f"LanguageTool not available, skipping grammar checks: {e}")
                self._lt_tool = False
        return self._lt_tool if self._lt_tool else None

    def _check_grammar(self, text: str, source_url: str, source_type: str):
        """Check French grammar and orthography."""
        lt = self._get_language_tool()
        if lt is None:
            return

        matches = lt.check(text)
        for m in matches:
            # Skip minor style suggestions
            if m.ruleId in ("WHITESPACE_RULE", "UNPAIRED_BRACKETS"):
                continue
            snippet = text[max(0, m.offset - 30):m.offset + m.errorLength + 30]
            self.issues.append({
                "url": source_url,
                "type": source_type,
                "issue_type": "grammar",
                "rule": m.ruleId,
                "message": m.message,
                "original": snippet,
                "suggestion": m.replacements[:3] if m.replacements else [],
            })

    def _check_brand_voice(self, text: str, source_url: str, source_type: str):
        """Check for forbidden phrases and brand drift."""
        text_lower = text.lower()
        for phrase in self.forbidden:
            if phrase.lower() in text_lower:
                # Find the snippet around the forbidden phrase
                idx = text_lower.index(phrase.lower())
                snippet = text[max(0, idx - 40):idx + len(phrase) + 40]
                self.issues.append({
                    "url": source_url,
                    "type": source_type,
                    "issue_type": "brand_drift",
                    "message": f"Phrase interdite détectée : « {phrase} »",
                    "original": snippet,
                    "suggestion": "Remplacer par une formulation enracinée dans l'expérience réelle de la ferme.",
                })

    def _check_seo(self, html: str, title: str, source_url: str, source_type: str):
        """Check SEO structure and keyword presence."""
        text = _strip_html(html)
        text_lower = text.lower()
        headings = _extract_headings(html)

        # Check keyword presence
        missing_keywords = []
        for kw in self.keywords:
            if kw.lower() not in text_lower and kw.lower() not in title.lower():
                missing_keywords.append(kw)

        if missing_keywords and len(missing_keywords) == len(self.keywords):
            self.issues.append({
                "url": source_url,
                "type": source_type,
                "issue_type": "seo",
                "message": f"Aucun mot-clé SEO principal trouvé dans le contenu",
                "original": f"Titre : {title}",
                "suggestion": f"Intégrer naturellement : {', '.join(missing_keywords[:3])}",
            })

        # Check heading hierarchy
        if headings:
            levels = [h["level"] for h in headings]
            if levels and levels[0] != 1:
                self.issues.append({
                    "url": source_url,
                    "type": source_type,
                    "issue_type": "seo",
                    "message": "Pas de H1 en tête du contenu",
                    "original": f"Premier titre : H{levels[0]} — « {headings[0]['text']} »",
                    "suggestion": "Ajouter un H1 principal avant les sous-titres",
                })
            # Check for skipped levels (e.g., H1 → H3 without H2)
            for i in range(1, len(levels)):
                if levels[i] > levels[i - 1] + 1:
                    self.issues.append({
                        "url": source_url,
                        "type": source_type,
                        "issue_type": "seo",
                        "message": f"Hiérarchie de titres sautée : H{levels[i-1]} → H{levels[i]}",
                        "original": f"« {headings[i-1]['text']} » → « {headings[i]['text']} »",
                        "suggestion": f"Ajouter un H{levels[i-1]+1} intermédiaire",
                    })

    def _audit_item(self, item: dict, item_type: str):
        """Audit a single page, post, or product."""
        title = _strip_html(item.get("title", {}).get("rendered", ""))
        content = item.get("content", {}).get("rendered", "")
        excerpt = item.get("excerpt", {}).get("rendered", "")
        url = item.get("link", f"ID:{item.get('id')}")

        plain_text = _strip_html(content)
        if excerpt:
            plain_text += " " + _strip_html(excerpt)

        if not plain_text.strip():
            self.issues.append({
                "url": url,
                "type": item_type,
                "issue_type": "content",
                "message": "Page vide — aucun contenu textuel détecté",
                "original": f"Titre : {title}",
                "suggestion": "Ajouter du contenu ou supprimer la page si inutile",
            })
            return

        self._check_grammar(plain_text, url, item_type)
        self._check_brand_voice(plain_text, url, item_type)
        self._check_seo(content, title, url, item_type)

    def run(self) -> str:
        """Execute the full content audit. Returns path to the report."""
        logger.info("=== Content Guardian — Starting audit ===")
        self.issues = []

        # Fetch all content
        try:
            pages = self.wp.get_pages()
        except Exception as e:
            logger.error(f"Failed to fetch pages: {e}")
            add_blocker(f"Cannot fetch pages from WP API: {e}", "content_guardian")
            pages = []

        try:
            posts = self.wp.get_posts()
        except Exception as e:
            logger.error(f"Failed to fetch posts: {e}")
            posts = []

        try:
            products = self.wp.get_products()
        except Exception as e:
            logger.error(f"Failed to fetch products: {e}")
            products = []

        # Audit each item
        for page in pages:
            self._audit_item(page, "page")

        for post in posts:
            self._audit_item(post, "post")

        for product in products:
            self._audit_item(product, "product")

        # Generate reports
        report_path = self._write_reports()

        # Update shared state
        update_section("content_audit",
                       status="pending",
                       report=report_path,
                       issues_count=len(self.issues),
                       audited_items=len(pages) + len(posts) + len(products))

        logger.info(f"=== Content Guardian — Audit complete: {len(self.issues)} issues found ===")
        return report_path

    def _write_reports(self) -> str:
        """Write audit report in Markdown and JSON."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        reports_dir = os.path.join(base_dir, self.config["paths"]["reports_dir"])
        os.makedirs(reports_dir, exist_ok=True)

        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # JSON report for corrections
        json_path = os.path.join(reports_dir, "corrections_pending.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.issues, f, indent=2, ensure_ascii=False)

        # Markdown report for humans
        md_path = os.path.join(reports_dir, f"audit_report_{date_str}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# Rapport d'Audit du Contenu — {date_str}\n\n")
            f.write(f"**Total d'anomalies détectées : {len(self.issues)}**\n\n")

            if not self.issues:
                f.write("Aucun problème détecté. Tout est en ordre.\n")
            else:
                # Group by type
                by_type = {}
                for issue in self.issues:
                    itype = issue["issue_type"]
                    by_type.setdefault(itype, []).append(issue)

                type_labels = {
                    "grammar": "Grammaire et Orthographe",
                    "brand_drift": "Dérive de la Voix de Marque",
                    "seo": "SEO",
                    "content": "Contenu",
                }

                for itype, issues in by_type.items():
                    f.write(f"## {type_labels.get(itype, itype)} ({len(issues)})\n\n")
                    for i, issue in enumerate(issues, 1):
                        f.write(f"### {i}. {issue['url']}\n")
                        f.write(f"- **Type de contenu :** {issue.get('type', '—')}\n")
                        f.write(f"- **Problème :** {issue['message']}\n")
                        f.write(f"- **Extrait :** `{issue.get('original', '—')}`\n")
                        suggestion = issue.get("suggestion", "—")
                        if isinstance(suggestion, list):
                            suggestion = " / ".join(suggestion)
                        f.write(f"- **Suggestion :** {suggestion}\n\n")

        logger.info(f"Reports written: {md_path}, {json_path}")
        return md_path

    def apply_corrections(self):
        """Apply approved corrections from corrections_pending.json.
        Only runs when shared_state content_audit.status == 'approved'.

        Applies grammar fixes by replacing error snippets in the original
        WordPress content via the REST API. Brand drift and SEO issues
        are logged but require manual intervention.
        """
        from agents.shared_state import load_state
        state = load_state()
        if state.get("content_audit", {}).get("status") != "approved":
            logger.warning("Content corrections not approved yet. Skipping apply.")
            return

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_path = os.path.join(
            base_dir, self.config["paths"]["reports_dir"], "corrections_pending.json"
        )

        if not os.path.exists(json_path):
            logger.warning("No corrections_pending.json found.")
            return

        with open(json_path, "r", encoding="utf-8") as f:
            corrections = json.load(f)

        if not corrections:
            logger.info("No corrections to apply.")
            update_section("content_audit", status="applied")
            return

        # Group corrections by URL and type for batch updates
        by_url = {}
        for c in corrections:
            url = c.get("url", "")
            by_url.setdefault(url, []).append(c)

        # Fetch all content for ID resolution
        content_map = {}
        for fetcher, wp_type in [
            (self.wp.get_pages, "page"),
            (self.wp.get_posts, "post"),
            (self.wp.get_products, "product"),
        ]:
            try:
                items = fetcher()
                for item in items:
                    link = item.get("link", "")
                    content_map[link] = {
                        "id": item["id"],
                        "wp_type": wp_type,
                        "content": item.get("content", {}).get("rendered", ""),
                    }
            except Exception as e:
                logger.error(f"Failed to fetch {wp_type}s for corrections: {e}")

        applied = 0
        skipped = 0
        manual_needed = []

        for url, issue_list in by_url.items():
            if url not in content_map:
                logger.warning(f"Cannot find WP item for URL: {url}")
                skipped += len(issue_list)
                continue

            item_info = content_map[url]
            item_id = item_info["id"]
            wp_type = item_info["wp_type"]
            current_content = item_info["content"]
            modified_content = current_content

            for issue in issue_list:
                issue_type = issue.get("issue_type", "")

                if issue_type == "grammar":
                    # Apply grammar fix: replace the error with the first suggestion
                    suggestions = issue.get("suggestion", [])
                    original = issue.get("original", "")
                    if suggestions and original:
                        # The original is a snippet with context; find the actual error
                        # by matching the snippet in content
                        first_fix = suggestions[0] if isinstance(suggestions, list) else suggestions
                        if original in modified_content:
                            modified_content = modified_content.replace(original, first_fix, 1)
                            applied += 1
                            logger.info(f"Applied grammar fix on {url}: '{original[:40]}...' → '{first_fix[:40]}...'")
                        else:
                            logger.debug(f"Snippet not found in content for {url}, skipping")
                            skipped += 1
                    else:
                        skipped += 1

                elif issue_type in ("brand_drift", "seo", "content"):
                    # These require human judgment — log for manual review
                    manual_needed.append({
                        "url": url,
                        "type": issue_type,
                        "message": issue.get("message", ""),
                    })
                    skipped += 1

            # Push updated content to WordPress if modified
            if modified_content != current_content:
                try:
                    update_data = {"content": modified_content}
                    if wp_type == "page":
                        self.wp.update_page(item_id, update_data)
                    elif wp_type == "post":
                        self.wp.update_post(item_id, update_data)
                    elif wp_type == "product":
                        self.wp.update_product(item_id, update_data)
                    logger.info(f"Updated {wp_type} {item_id} on WordPress")
                except Exception as e:
                    logger.error(f"Failed to update {wp_type} {item_id}: {e}")

        # Purge cache after applying changes
        if applied > 0:
            self.wp.purge_litespeed_cache()

        # Log summary
        logger.info(f"Corrections applied: {applied}, skipped: {skipped}, "
                     f"manual review needed: {len(manual_needed)}")

        if manual_needed:
            logger.info("The following issues require manual intervention:")
            for item in manual_needed:
                logger.info(f"  [{item['type']}] {item['url']}: {item['message']}")

        update_section("content_audit", status="applied",
                       applied_count=applied, skipped_count=skipped,
                       manual_review=len(manual_needed))


def run_agent(config: dict = None):
    """Entry point for the orchestrator."""
    agent = ContentGuardian(config)
    return agent.run()
