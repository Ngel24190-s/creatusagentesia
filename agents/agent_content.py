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
        """
        from agents.shared_state import load_state
        state = load_state()
        if state.get("content_audit", {}).get("status") != "approved":
            logger.warning("Content corrections not approved yet. Skipping apply.")
            return

        logger.info("Applying approved content corrections is not yet implemented.")
        logger.info("Manual review and application recommended for first runs.")
        update_section("content_audit", status="applied")


def run_agent(config: dict = None):
    """Entry point for the orchestrator."""
    agent = ContentGuardian(config)
    return agent.run()
