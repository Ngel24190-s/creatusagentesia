#!/usr/bin/env python3
"""Agent 4 — Orchestrator (Chef d'Orchestre)

Coordinates all NosVers agents, manages shared state,
and produces weekly summary reports for Angel and Africa.

Usage:
    python orchestrator.py --run-all
    python orchestrator.py --agent content
    python orchestrator.py --agent photos
    python orchestrator.py --agent social
    python orchestrator.py --test
    python orchestrator.py --report
"""

import argparse
import os
import sys
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.config_loader import load_config
from agents.logger import get_logger
from agents.shared_state import load_state, save_state, update_section
from agents.wp_client import WPClient
from agents.agent_content import ContentGuardian
from agents.agent_photos import PhotoManager
from agents.agent_social import SocialMediaManager
from agents.notifier import get_notifier

logger = get_logger("orchestrator")


class Orchestrator:
    """Coordinates the NosVers agent ecosystem."""

    def __init__(self):
        self.config = load_config()
        self.wp = WPClient(self.config)
        self.notifier = get_notifier(self.config)

    def test_connection(self) -> bool:
        """Test WordPress API connectivity and authentication."""
        logger.info("=" * 60)
        logger.info("NosVers Agent Ecosystem — Connection Test")
        logger.info("=" * 60)

        # Test basic connectivity
        conn = self.wp.test_connection()
        if not conn["success"]:
            logger.error(f"Connection FAILED: {conn.get('error')}")
            print(f"\n  FAILED — {conn.get('error')}")
            return False

        print(f"\n  Site: {conn.get('name')}")
        print(f"  URL: {conn.get('url')}")

        # Check available namespaces
        namespaces = conn.get("namespaces", [])
        has_wc = any("wc" in ns for ns in namespaces)
        has_wp = "wp/v2" in namespaces
        print(f"  WP REST API: {'OK' if has_wp else 'NOT FOUND'}")
        print(f"  WooCommerce: {'OK' if has_wc else 'NOT FOUND'}")

        # Test authentication
        auth = self.wp.test_auth()
        if auth["success"]:
            print(f"  Auth: OK — logged in as '{auth.get('user')}'")
        else:
            print(f"  Auth: FAILED — {auth.get('error')}")
            logger.warning("Authentication failed — agents will run in read-only mode")

        # Quick data test
        try:
            pages = self.wp.get_pages()
            print(f"  Pages found: {len(pages)}")
        except Exception:
            print("  Pages: could not fetch")

        try:
            media = self.wp.get_media()
            print(f"  Media items: {len(media)}")
        except Exception:
            print("  Media: could not fetch")

        print()
        logger.info("Connection test complete")
        return conn["success"]

    def run_content_audit(self):
        """Run Agent 1 — Content Guardian."""
        logger.info("Starting Content Guardian...")
        agent = ContentGuardian(self.config)
        report = agent.run()
        print(f"  Content audit report: {report}")
        return report

    def run_media_audit(self):
        """Run Agent 2 — Photo Manager."""
        logger.info("Starting Photo Manager...")
        agent = PhotoManager(self.config)
        report = agent.run()
        print(f"  Media audit report: {report}")
        return report

    def run_social_generation(self):
        """Run Agent 3 — Social Media Manager."""
        logger.info("Starting Social Media Manager...")
        agent = SocialMediaManager(self.config)
        report = agent.run()
        print(f"  Social queue: {report}")
        return report

    def run_all(self):
        """Run all agents in the correct order with cross-agent coordination."""
        logger.info("=" * 60)
        logger.info("NosVers Agent Ecosystem — Full Run")
        logger.info("=" * 60)
        print("\nNosVers Agent Ecosystem — Full Run")
        print("=" * 50)

        # Clear stale blockers from previous runs
        from agents.shared_state import clear_blockers
        clear_blockers()

        # Step 1: Content audit
        print("\n[1/3] Content Guardian (Gardien du Contenu)...")
        try:
            self.run_content_audit()
        except Exception as e:
            logger.error(f"Content Guardian failed: {e}")
            print(f"  ERROR: {e}")

        # Step 2: Photo audit
        print("\n[2/3] Photo Manager (Gestionnaire des Médias)...")
        try:
            self.run_media_audit()
        except Exception as e:
            logger.error(f"Photo Manager failed: {e}")
            print(f"  ERROR: {e}")

        # Step 3: Social posts (reads output of steps 1 and 2)
        print("\n[3/3] Social Media Manager (Responsable Réseaux Sociaux)...")
        try:
            self.run_social_generation()
        except Exception as e:
            logger.error(f"Social Media Manager failed: {e}")
            print(f"  ERROR: {e}")

        print("\n" + "=" * 50)
        print("Run complete. Check reports/ for all outputs.")
        print("Review and approve in shared_state.json before applying changes.\n")

        # Send Telegram notification
        state = load_state()
        self.notifier.send_report_summary(state)

        logger.info("Full run complete")

    def generate_weekly_report(self) -> str:
        """Generate weekly summary report for Angel and Africa."""
        logger.info("Generating weekly report...")

        state = load_state()
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        base_dir = os.path.dirname(os.path.abspath(__file__))
        reports_dir = os.path.join(base_dir, self.config["paths"]["reports_dir"])
        os.makedirs(reports_dir, exist_ok=True)

        report_path = os.path.join(reports_dir, f"weekly_report_{date_str}.md")

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# Rapport Hebdomadaire NosVers — {date_str}\n\n")
            f.write(f"Dernier run : {state.get('last_run', 'Jamais')}\n\n")

            # Content audit summary
            ca = state.get("content_audit", {})
            f.write("## Audit du Contenu\n\n")
            f.write(f"- **Statut :** {ca.get('status', 'non exécuté')}\n")
            f.write(f"- **Anomalies :** {ca.get('issues_count', '—')}\n")
            f.write(f"- **Éléments audités :** {ca.get('audited_items', '—')}\n")
            if ca.get("report"):
                f.write(f"- **Rapport :** `{ca['report']}`\n")
            f.write("\n")

            # Media audit summary
            ma = state.get("media_audit", {})
            f.write("## Audit des Médias\n\n")
            f.write(f"- **Statut :** {ma.get('status', 'non exécuté')}\n")
            f.write(f"- **Anomalies :** {ma.get('issues_count', '—')}\n")
            f.write(f"- **Photos nécessaires :** {ma.get('photos_needed', '—')}\n")
            if ma.get("report"):
                f.write(f"- **Rapport :** `{ma['report']}`\n")
            f.write("\n")

            # Social queue summary
            sq = state.get("social_queue", {})
            f.write("## Réseaux Sociaux\n\n")
            f.write(f"- **Statut :** {sq.get('status', 'non exécuté')}\n")
            f.write(f"- **Posts générés :** {sq.get('count', '—')}\n")
            if sq.get("posts"):
                f.write(f"- **File d'attente :** `{sq['posts']}`\n")
            f.write("\n")

            # Blockers
            blockers = state.get("blockers", [])
            f.write("## Blocages\n\n")
            if blockers:
                for b in blockers:
                    f.write(f"- **[{b.get('agent', '?')}]** {b.get('description', '—')} "
                            f"({b.get('timestamp', '')})\n")
            else:
                f.write("Aucun blocage en cours.\n")
            f.write("\n")

            # Action items
            f.write("## Actions Requises\n\n")
            actions = []
            if ca.get("status") == "pending" and ca.get("issues_count", 0) > 0:
                actions.append("Valider les corrections de contenu dans `shared_state.json` "
                               "(changer `content_audit.status` en `approved`)")
            if ma.get("status") == "pending" and ma.get("photos_needed", 0) > 0:
                actions.append("Prendre les photos listées dans `reports/photo_needed.md`")
            if sq.get("status") == "draft":
                actions.append("Relire et approuver les posts dans "
                               "`reports/social_queue_*.md`")

            if actions:
                for i, action in enumerate(actions, 1):
                    f.write(f"{i}. {action}\n")
            else:
                f.write("Aucune action requise pour le moment.\n")

        logger.info(f"Weekly report written: {report_path}")
        print(f"Weekly report: {report_path}")

        # Send via email if configured
        self._email_report(report_path)

        return report_path

    def apply_corrections(self):
        """Apply all approved corrections (content + media)."""
        logger.info("=" * 60)
        logger.info("NosVers — Applying Approved Corrections")
        logger.info("=" * 60)
        print("\nApplying approved corrections...")

        # Content corrections
        print("\n[1/2] Content corrections...")
        try:
            content_agent = ContentGuardian(self.config)
            content_agent.apply_corrections()
            print("  Content corrections applied.")
        except Exception as e:
            logger.error(f"Content corrections failed: {e}")
            print(f"  ERROR: {e}")

        # Media alt text corrections
        print("\n[2/2] Media alt text corrections...")
        try:
            photo_agent = PhotoManager(self.config)
            photo_agent.apply_alt_texts()
            print("  Media corrections applied.")
        except Exception as e:
            logger.error(f"Media corrections failed: {e}")
            print(f"  ERROR: {e}")

        # Purge cache
        self.wp.purge_litespeed_cache()
        print("\nCorrections applied. Re-run audit to verify.\n")

    def send_status_notification(self):
        """Send current ecosystem status via Telegram."""
        state = load_state()
        if self.notifier.send_report_summary(state):
            print("Telegram notification sent.")
        else:
            print("Telegram notification not sent (check configuration).")

    def _email_report(self, report_path: str):
        """Send weekly report via email if SMTP is configured."""
        email_cfg = self.config.get("email", {})
        if not email_cfg.get("enabled"):
            return

        try:
            with open(report_path, "r", encoding="utf-8") as f:
                report_content = f.read()

            msg = MIMEMultipart()
            msg["From"] = email_cfg["from_address"]
            msg["To"] = ", ".join(email_cfg["to_addresses"])
            msg["Subject"] = f"NosVers — Rapport Hebdomadaire {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
            msg.attach(MIMEText(report_content, "plain", "utf-8"))

            with smtplib.SMTP(email_cfg["smtp_host"], email_cfg["smtp_port"]) as server:
                server.starttls()
                server.login(email_cfg["smtp_user"], email_cfg["smtp_password"])
                server.send_message(msg)

            logger.info("Weekly report sent via email")
        except Exception as e:
            logger.warning(f"Failed to send email report: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="NosVers Agent Ecosystem — Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python orchestrator.py --test          Test WP API connection
  python orchestrator.py --run-all       Run all agents in sequence
  python orchestrator.py --agent content Run only Content Guardian
  python orchestrator.py --agent photos  Run only Photo Manager
  python orchestrator.py --agent social  Run only Social Media Manager
  python orchestrator.py --report        Generate weekly report
        """
    )
    parser.add_argument("--test", action="store_true",
                        help="Test WordPress API connection")
    parser.add_argument("--run-all", action="store_true",
                        help="Run all agents in sequence")
    parser.add_argument("--agent", choices=["content", "photos", "social"],
                        help="Run a specific agent")
    parser.add_argument("--report", action="store_true",
                        help="Generate weekly summary report")
    parser.add_argument("--apply", action="store_true",
                        help="Apply approved corrections to WordPress")
    parser.add_argument("--notify", action="store_true",
                        help="Send current status via Telegram")

    args = parser.parse_args()

    if not any([args.test, args.run_all, args.agent, args.report, args.apply, args.notify]):
        parser.print_help()
        sys.exit(0)

    orch = Orchestrator()

    if args.test:
        success = orch.test_connection()
        sys.exit(0 if success else 1)

    if args.run_all:
        orch.run_all()
    elif args.agent == "content":
        orch.run_content_audit()
    elif args.agent == "photos":
        orch.run_media_audit()
    elif args.agent == "social":
        orch.run_social_generation()

    if args.apply:
        orch.apply_corrections()

    if args.report or args.run_all:
        orch.generate_weekly_report()

    if args.notify:
        orch.send_status_notification()


if __name__ == "__main__":
    main()
