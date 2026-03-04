"""Agent 3 — Social Media Manager (Responsable Réseaux Sociaux)

Transforms farm content into ready-to-publish social media posts
for Instagram, Facebook, and TikTok.
"""

import os
import json
from datetime import datetime, timezone
from html import unescape
import re

from agents.config_loader import load_config
from agents.logger import get_logger
from agents.wp_client import WPClient
from agents.shared_state import load_state, update_section, add_blocker

logger = get_logger("social_manager")


def _strip_html(html: str) -> str:
    """Remove HTML tags and decode entities."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


class SocialMediaManager:
    """Generates social media posts from WordPress content and content seeds."""

    # Brand voice rules
    HASHTAGS_POOL = [
        "#lombricompost", "#LombriThé", "#solVivant", "#Dordogne",
        "#versDeTerre", "#agroécologie", "#permaculture", "#compost",
        "#ferme", "#agriculture", "#engraisNaturel", "#jardin",
        "#NosVers", "#fermeFamiliale", "#SoilFoodWeb",
    ]

    CTA_PRODUCT = "Disponible sur nosvers.com — lien en bio."
    CTA_EDUCATION = "Posez vos questions en commentaire !"
    CTA_BEHIND_SCENES = "Suivez la ferme pour la suite."

    def __init__(self, config: dict = None):
        if config is None:
            config = load_config()
        self.config = config
        self.wp = WPClient(config)
        self.posts_generated = []

    def _determine_content_type(self, item: dict) -> str:
        """Determine if content is product, educational, or behind-the-scenes."""
        item_type = item.get("_type", "post")
        if item_type == "product":
            return "product"

        # Check content for educational markers
        text = _strip_html(item.get("content", {}).get("rendered", "")).lower()
        educational_markers = [
            "comment", "pourquoi", "saviez-vous", "explication",
            "méthode", "technique", "dr. elaine", "soil food web",
            "biologie du sol", "micro-organismes",
        ]
        for marker in educational_markers:
            if marker in text:
                return "education"

        return "behind_scenes"

    def _select_hashtags(self, text: str, count: int = 5) -> list:
        """Select relevant hashtags based on content."""
        text_lower = text.lower()
        scored = []
        for tag in self.HASHTAGS_POOL:
            keyword = tag.lstrip("#").lower()
            score = 1 if keyword in text_lower else 0
            scored.append((tag, score))

        # Sort by relevance, then take top N
        scored.sort(key=lambda x: x[1], reverse=True)
        selected = [tag for tag, _ in scored[:count]]

        # Always include #NosVers
        if "#NosVers" not in selected:
            selected[-1] = "#NosVers"

        return selected

    def _get_cta(self, content_type: str) -> str:
        """Get the appropriate call-to-action."""
        if content_type == "product":
            return self.CTA_PRODUCT
        elif content_type == "education":
            return self.CTA_EDUCATION
        return self.CTA_BEHIND_SCENES

    def _generate_instagram(self, title: str, text: str, content_type: str, url: str) -> dict:
        """Generate Instagram post variant."""
        hashtags = self._select_hashtags(text)

        # Build caption: concise, visual, 150-220 words target
        caption_parts = []

        # Hook line
        if content_type == "product":
            caption_parts.append(f"{title}\n")
            caption_parts.append(
                f"Produit directement de notre ferme familiale en Dordogne, "
                f"sans intermédiaire.\n"
            )
        elif content_type == "education":
            caption_parts.append(f"{title}\n")
        else:
            caption_parts.append(f"Aujourd'hui à la ferme : {title.lower()}\n")

        # Body — summarize the key points from the text
        sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 20]
        body_sentences = sentences[:4]  # Take first 4 meaningful sentences
        if body_sentences:
            caption_parts.append(". ".join(body_sentences) + ".\n")

        # CTA
        caption_parts.append(f"\n{self._get_cta(content_type)}\n")

        # Hashtags
        caption_parts.append(f"\n{' '.join(hashtags)}")

        return {
            "platform": "instagram",
            "caption": "\n".join(caption_parts),
            "hashtags": hashtags,
            "cta": self._get_cta(content_type),
            "source_url": url,
        }

    def _generate_facebook(self, title: str, text: str, content_type: str, url: str) -> dict:
        """Generate Facebook post variant — longer, conversational."""
        parts = []

        if content_type == "product":
            parts.append(f"{title}\n")
            parts.append(
                "Nous le produisons ici, à la ferme, en Dordogne. "
                "Pas d'usine, pas d'intermédiaire — directement du ver à votre sol.\n"
            )
        elif content_type == "education":
            parts.append(f"{title}\n")
            parts.append(
                "On vous explique ce que ça veut dire concrètement, "
                "depuis notre expérience sur le terrain.\n"
            )
        else:
            parts.append(f"Nouvelles de la ferme : {title}\n")

        # Include more text for Facebook (target 200-300 words)
        sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 15]
        body = ". ".join(sentences[:8])
        if body:
            parts.append(f"{body}.\n")

        parts.append(f"\n{self._get_cta(content_type)}")

        if content_type == "product":
            parts.append(f"\n{url}")

        return {
            "platform": "facebook",
            "text": "\n".join(parts),
            "cta": self._get_cta(content_type),
            "source_url": url,
        }

    def _generate_tiktok(self, title: str, text: str, content_type: str, url: str) -> dict:
        """Generate TikTok/Reels script — punchy hook, short."""
        hook_options = {
            "product": f"Vous savez ce que vos plantes mangent vraiment ?",
            "education": f"Ce que personne ne vous dit sur le sol de votre jardin.",
            "behind_scenes": f"Un jour normal à la ferme de vers... ou pas.",
        }

        hook = hook_options.get(content_type, hook_options["behind_scenes"])

        # Extract one key fact
        sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 20]
        key_fact = sentences[0] if sentences else title

        script = (
            f"HOOK (3 premières secondes) : « {hook} »\n\n"
            f"CORPS : {key_fact}.\n"
            f"Ici à NosVers, en Dordogne, on travaille avec des millions de vers "
            f"pour créer le meilleur amendement naturel possible.\n\n"
            f"FIN : {self._get_cta(content_type)}"
        )

        hashtags = self._select_hashtags(text, count=3)

        return {
            "platform": "tiktok",
            "script": script,
            "hook": hook,
            "hashtags": hashtags,
            "cta": self._get_cta(content_type),
            "source_url": url,
        }

    def _process_content_item(self, item: dict):
        """Generate all platform variants for a content item."""
        title = _strip_html(item.get("title", {}).get("rendered", "Sans titre"))
        text = _strip_html(item.get("content", {}).get("rendered", ""))
        url = item.get("link", "")
        content_type = self._determine_content_type(item)

        if not text or len(text) < 50:
            logger.debug(f"Skipping item '{title}' — insufficient content")
            return

        post_set = {
            "title": title,
            "content_type": content_type,
            "source_url": url,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "variants": {
                "instagram": self._generate_instagram(title, text, content_type, url),
                "facebook": self._generate_facebook(title, text, content_type, url),
                "tiktok": self._generate_tiktok(title, text, content_type, url),
            },
        }

        self.posts_generated.append(post_set)

    def _process_content_seeds(self):
        """Read content seeds from content_seeds/ directory."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        seeds_dir = os.path.join(base_dir, self.config["paths"]["content_seeds_dir"])

        if not os.path.exists(seeds_dir):
            return

        for filename in os.listdir(seeds_dir):
            if not filename.endswith(".txt"):
                continue

            filepath = os.path.join(seeds_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                seed_text = f.read().strip()

            if not seed_text:
                continue

            logger.info(f"Processing content seed: {filename}")

            # Treat seed as a generic behind-the-scenes item
            lines = seed_text.split("\n")
            title = lines[0][:80] if lines else "Note de la ferme"
            body = " ".join(lines[1:]) if len(lines) > 1 else seed_text

            item = {
                "title": {"rendered": title},
                "content": {"rendered": body},
                "link": "https://nosvers.com",
                "_type": "seed",
            }
            self._process_content_item(item)

    def run(self) -> str:
        """Execute social media post generation. Returns path to the queue."""
        logger.info("=== Social Media Manager — Starting post generation ===")
        self.posts_generated = []

        # Check shared state for blockers
        state = load_state()
        content_status = state.get("content_audit", {}).get("status", "")

        # Fetch content from WP
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

        # Check for content issues before generating social posts
        blocked_urls = set()
        if content_status == "pending":
            # Read the corrections file to know which items have issues
            corrections_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                self.config["paths"]["reports_dir"],
                "corrections_pending.json"
            )
            if os.path.exists(corrections_path):
                with open(corrections_path, "r", encoding="utf-8") as f:
                    corrections = json.load(f)
                blocked_urls = {c.get("url", "") for c in corrections
                                if c.get("issue_type") in ("grammar", "brand_drift")}
                if blocked_urls:
                    logger.warning(
                        f"Blocking {len(blocked_urls)} items with pending content corrections"
                    )

        # Check for missing photos
        media_status = state.get("media_audit", {}).get("status", "")
        awaiting_photo = set()
        if media_status == "pending":
            photo_json = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                self.config["paths"]["reports_dir"],
                "media_issues.json"
            )
            if os.path.exists(photo_json):
                with open(photo_json, "r", encoding="utf-8") as f:
                    media_data = json.load(f)
                for need in media_data.get("photos_needed", []):
                    awaiting_photo.add(need.get("url", ""))

        # Generate posts for each item
        for post in posts:
            url = post.get("link", "")
            if url in blocked_urls:
                logger.info(f"Skipping post '{post.get('title', {}).get('rendered', '')}' — pending corrections")
                continue
            post["_type"] = "post"
            self._process_content_item(post)

        for product in products:
            url = product.get("link", "")
            product["_type"] = "product"
            if url in blocked_urls:
                logger.info(f"Skipping product — pending corrections")
                continue
            self._process_content_item(product)

            # Mark as draft if awaiting photo
            if url in awaiting_photo and self.posts_generated:
                self.posts_generated[-1]["status"] = "draft — en attente de photo"

        # Process content seeds
        self._process_content_seeds()

        # Write output
        report_path = self._write_queue()

        update_section("social_queue",
                       status="draft",
                       posts=report_path,
                       count=len(self.posts_generated))

        logger.info(f"=== Social Media Manager — Generated {len(self.posts_generated)} post sets ===")
        return report_path

    def _write_queue(self) -> str:
        """Write social media queue as Markdown for human review."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        reports_dir = os.path.join(base_dir, self.config["paths"]["reports_dir"])
        os.makedirs(reports_dir, exist_ok=True)

        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        md_path = os.path.join(reports_dir, f"social_queue_{date_str}.md")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# File d'Attente Réseaux Sociaux — {date_str}\n\n")
            f.write(f"**Posts générés : {len(self.posts_generated)}**\n\n")
            f.write("Chaque publication ci-dessous est déclinée pour Instagram, "
                    "Facebook et TikTok.\n")
            f.write("Angel, Africa — relisez et marquez « approuvé » dans "
                    "`shared_state.json` quand vous êtes prêts.\n\n")
            f.write("---\n\n")

            for idx, post_set in enumerate(self.posts_generated, 1):
                status = post_set.get("status", "à valider")
                f.write(f"## {idx}. {post_set['title']}\n\n")
                f.write(f"- **Type :** {post_set['content_type']}\n")
                f.write(f"- **Source :** {post_set['source_url']}\n")
                f.write(f"- **Statut :** {status}\n\n")

                # Instagram
                ig = post_set["variants"]["instagram"]
                f.write("### Instagram\n\n")
                f.write("```\n")
                f.write(ig["caption"])
                f.write("\n```\n\n")

                # Facebook
                fb = post_set["variants"]["facebook"]
                f.write("### Facebook\n\n")
                f.write("```\n")
                f.write(fb["text"])
                f.write("\n```\n\n")

                # TikTok
                tk = post_set["variants"]["tiktok"]
                f.write("### TikTok / Reels\n\n")
                f.write("```\n")
                f.write(tk["script"])
                f.write("\n```\n\n")
                f.write("---\n\n")

        # JSON version for programmatic access
        json_path = os.path.join(reports_dir, "social_queue.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.posts_generated, f, indent=2, ensure_ascii=False)

        logger.info(f"Social queue written: {md_path}")
        return md_path


def run_agent(config: dict = None):
    """Entry point for the orchestrator."""
    agent = SocialMediaManager(config)
    return agent.run()
