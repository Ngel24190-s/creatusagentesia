"""Notification module for NosVers Agent Ecosystem.

Supports Telegram bot notifications for sending reports and alerts
to Angel and Africa.
"""

import json
import requests
from agents.logger import get_logger

logger = get_logger("notifier")


class TelegramNotifier:
    """Send notifications via Telegram Bot API."""

    API_BASE = "https://api.telegram.org/bot{token}"

    def __init__(self, config: dict):
        tg_config = config.get("telegram", {})
        self.bot_token = tg_config.get("bot_token", "")
        self.chat_id = tg_config.get("chat_id", "")
        self.enabled = bool(self.bot_token and self.chat_id)

        if not self.enabled:
            logger.debug("Telegram notifications disabled (no token/chat_id)")

    def _api_url(self, method: str) -> str:
        return f"{self.API_BASE.format(token=self.bot_token)}/{method}"

    def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Send a text message to the configured chat."""
        if not self.enabled:
            logger.debug("Telegram not configured, skipping notification")
            return False

        # Telegram has a 4096 char limit per message
        chunks = self._split_message(text, max_len=4000)

        for chunk in chunks:
            try:
                resp = requests.post(
                    self._api_url("sendMessage"),
                    json={
                        "chat_id": self.chat_id,
                        "text": chunk,
                        "parse_mode": parse_mode,
                    },
                    timeout=15,
                )
                if resp.status_code != 200:
                    logger.warning(f"Telegram API returned {resp.status_code}: {resp.text}")
                    return False
            except Exception as e:
                logger.warning(f"Failed to send Telegram message: {e}")
                return False

        return True

    def send_report_summary(self, state: dict) -> bool:
        """Send a formatted summary of the ecosystem state."""
        ca = state.get("content_audit", {})
        ma = state.get("media_audit", {})
        sq = state.get("social_queue", {})
        blockers = state.get("blockers", [])

        lines = [
            "*NosVers — Résumé Automatique*",
            "",
            f"*Contenu:* {ca.get('status', '—')} ({ca.get('issues_count', 0)} anomalies)",
            f"*Médias:* {ma.get('status', '—')} ({ma.get('issues_count', 0)} anomalies, "
            f"{ma.get('photos_needed', 0)} photos nécessaires)",
            f"*Réseaux sociaux:* {sq.get('status', '—')} ({sq.get('count', 0)} posts)",
        ]

        if blockers:
            lines.append("")
            lines.append(f"*Blocages ({len(blockers)}):*")
            for b in blockers[:5]:
                lines.append(f"  - [{b.get('agent', '?')}] {b.get('description', '')}")

        lines.append("")
        lines.append("Consultez `reports/` pour les détails.")

        return self.send_message("\n".join(lines))

    def notify_run_complete(self, agent_name: str, issues_count: int = 0):
        """Send a quick notification after an agent run."""
        emoji_map = {
            "content_guardian": "Content Guardian",
            "photo_manager": "Photo Manager",
            "social_manager": "Social Media Manager",
            "orchestrator": "Orchestrator",
        }
        label = emoji_map.get(agent_name, agent_name)

        if issues_count > 0:
            msg = f"*{label}* terminé — {issues_count} anomalie(s) détectée(s). Vérifiez les rapports."
        else:
            msg = f"*{label}* terminé — aucune anomalie."

        return self.send_message(msg)

    @staticmethod
    def _split_message(text: str, max_len: int = 4000) -> list:
        """Split long messages for Telegram's character limit."""
        if len(text) <= max_len:
            return [text]

        chunks = []
        lines = text.split("\n")
        current = ""

        for line in lines:
            if len(current) + len(line) + 1 > max_len:
                chunks.append(current)
                current = line
            else:
                current = f"{current}\n{line}" if current else line

        if current:
            chunks.append(current)

        return chunks


def get_notifier(config: dict) -> TelegramNotifier:
    """Factory function to create a notifier from config."""
    return TelegramNotifier(config)
