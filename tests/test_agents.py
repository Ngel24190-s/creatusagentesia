"""Automated test suite for NosVers Agent Ecosystem.

Uses pytest with mocked WordPress API calls so tests run
without network access.
"""

import os
import sys
import json
import pytest
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime, timezone

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def test_config(tmp_path):
    """Provide a test configuration with temp directories."""
    return {
        "wordpress": {
            "site_url": "https://test.nosvers.com",
            "api_user": "test_user",
            "api_password": "test_pass",
            "litespeed_purge": False,
        },
        "paths": {
            "reports_dir": str(tmp_path / "reports"),
            "logs_dir": str(tmp_path / "logs"),
            "content_seeds_dir": str(tmp_path / "content_seeds"),
            "shared_state": str(tmp_path / "shared_state.json"),
        },
        "logging": {"level": "DEBUG", "log_file": str(tmp_path / "logs" / "test.log")},
        "seo": {
            "primary_keywords": ["lombricompost", "LombriThé", "sol vivant"],
            "brand_voice": {
                "tone": "scientific, artisanal, honest",
                "forbidden_phrases": ["incroyable", "magique", "révolutionnaire"],
            },
        },
        "social": {"platforms": ["instagram", "facebook", "tiktok"]},
        "email": {"enabled": False},
        "telegram": {"bot_token": "", "chat_id": ""},
    }


@pytest.fixture
def sample_pages():
    """Sample WordPress pages for testing."""
    return [
        {
            "id": 1,
            "title": {"rendered": "Accueil — NosVers"},
            "content": {"rendered": (
                "<h1>Bienvenue chez NosVers</h1>"
                "<p>Notre lombricompost artisanal est produit en Dordogne "
                "avec des millions de vers de terre.</p>"
                "<h2>Nos Produits</h2>"
                "<p>Le LombriThé nourrit votre sol vivant naturellement.</p>"
            )},
            "excerpt": {"rendered": ""},
            "link": "https://test.nosvers.com/accueil",
            "featured_media": 10,
        },
        {
            "id": 2,
            "title": {"rendered": "Page Vide"},
            "content": {"rendered": ""},
            "excerpt": {"rendered": ""},
            "link": "https://test.nosvers.com/vide",
            "featured_media": 0,
        },
    ]


@pytest.fixture
def sample_posts():
    """Sample WordPress posts."""
    return [
        {
            "id": 100,
            "title": {"rendered": "Comment utiliser le lombricompost"},
            "content": {"rendered": (
                "<h1>Guide du lombricompost</h1>"
                "<p>Le lombricompost est un engrais naturel incroyable "
                "produit par les vers de terre en Dordogne.</p>"
                "<h2>Méthode d'application</h2>"
                "<p>Appliquez 500g par mètre carré au printemps.</p>"
            )},
            "excerpt": {"rendered": ""},
            "link": "https://test.nosvers.com/guide-lombricompost",
            "featured_media": 11,
        },
    ]


@pytest.fixture
def sample_products():
    """Sample WooCommerce products."""
    return [
        {
            "id": 200,
            "title": {"rendered": "LombriThé 5L"},
            "content": {"rendered": (
                "<h1>LombriThé — Extrait liquide de lombricompost</h1>"
                "<p>Notre LombriThé concentre les micro-organismes bénéfiques "
                "du sol vivant pour vos plantes.</p>"
            )},
            "excerpt": {"rendered": ""},
            "link": "https://test.nosvers.com/produit/lombrithe-5l",
            "featured_media": 12,
        },
    ]


@pytest.fixture
def sample_media():
    """Sample WordPress media items."""
    return [
        {
            "id": 10,
            "title": {"rendered": "Ferme NosVers vue aérienne"},
            "alt_text": "Vue aérienne de la ferme NosVers en Dordogne",
            "caption": {"rendered": ""},
            "source_url": "https://test.nosvers.com/wp-content/uploads/ferme-nosvers.jpg",
            "mime_type": "image/jpeg",
            "media_details": {"width": 1920, "height": 1080},
        },
        {
            "id": 11,
            "title": {"rendered": "IMG_2024"},
            "alt_text": "",
            "caption": {"rendered": ""},
            "source_url": "https://test.nosvers.com/wp-content/uploads/IMG_2024.jpg",
            "mime_type": "image/jpeg",
            "media_details": {"width": 640, "height": 480},
        },
        {
            "id": 12,
            "title": {"rendered": "LombriThé bouteille"},
            "alt_text": "LombriThé",
            "caption": {"rendered": ""},
            "source_url": "https://test.nosvers.com/wp-content/uploads/lombrithe.jpg",
            "mime_type": "image/jpeg",
            "media_details": {"width": 1200, "height": 800},
        },
    ]


# ---------------------------------------------------------------------------
# Helper: mock config loader so agents don't try to read config.yaml
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_config_dirs(test_config):
    """Ensure test directories exist."""
    for key in ("reports_dir", "logs_dir", "content_seeds_dir"):
        os.makedirs(test_config["paths"][key], exist_ok=True)


# ---------------------------------------------------------------------------
# Tests: Content Guardian
# ---------------------------------------------------------------------------

class TestContentGuardian:
    """Tests for agent_content.py — ContentGuardian."""

    def _make_agent(self, test_config):
        with patch("agents.agent_content.load_config", return_value=test_config):
            from agents.agent_content import ContentGuardian
            agent = ContentGuardian(test_config)
            agent.wp = MagicMock()
            return agent

    def test_strip_html(self):
        from agents.agent_content import _strip_html
        assert _strip_html("<p>Hello <b>world</b></p>") == "Hello world"
        assert _strip_html("&amp; &lt;test&gt;") == "& <test>"

    def test_extract_headings(self):
        from agents.agent_content import _extract_headings
        html = "<h1>Title</h1><h2>Subtitle</h2><h3>Section</h3>"
        headings = _extract_headings(html)
        assert len(headings) == 3
        assert headings[0] == {"level": 1, "text": "Title"}
        assert headings[1] == {"level": 2, "text": "Subtitle"}

    def test_brand_voice_detects_forbidden(self, test_config):
        agent = self._make_agent(test_config)
        agent._check_brand_voice(
            "Ce produit est vraiment incroyable pour le sol",
            "https://test.com/page",
            "page"
        )
        assert len(agent.issues) == 1
        assert agent.issues[0]["issue_type"] == "brand_drift"

    def test_brand_voice_clean(self, test_config):
        agent = self._make_agent(test_config)
        agent._check_brand_voice(
            "Ce lombricompost artisanal nourrit le sol naturellement",
            "https://test.com/page",
            "page"
        )
        assert len(agent.issues) == 0

    def test_seo_missing_keywords(self, test_config):
        agent = self._make_agent(test_config)
        html = "<h1>Titre</h1><p>Contenu sans aucun mot-clé pertinent.</p>"
        agent._check_seo(html, "Titre", "https://test.com", "page")
        seo_issues = [i for i in agent.issues if i["issue_type"] == "seo"]
        assert any("mot-clé" in i["message"] for i in seo_issues)

    def test_seo_heading_hierarchy(self, test_config):
        agent = self._make_agent(test_config)
        # H1 → H3 (skipping H2)
        html = "<h1>Titre</h1><h3>Sous-section</h3><p>Contenu lombricompost.</p>"
        agent._check_seo(html, "Titre", "https://test.com", "page")
        seo_issues = [i for i in agent.issues if "Hiérarchie" in i.get("message", "")]
        assert len(seo_issues) == 1

    def test_seo_no_h1(self, test_config):
        agent = self._make_agent(test_config)
        html = "<h2>Sous-titre</h2><p>Contenu lombricompost.</p>"
        agent._check_seo(html, "Titre", "https://test.com", "page")
        assert any("H1" in i["message"] for i in agent.issues)

    def test_audit_empty_page(self, test_config, sample_pages):
        agent = self._make_agent(test_config)
        empty_page = sample_pages[1]  # Page Vide
        agent._audit_item(empty_page, "page")
        assert len(agent.issues) == 1
        assert agent.issues[0]["issue_type"] == "content"
        assert "vide" in agent.issues[0]["message"].lower()

    @patch("agents.agent_content.update_section")
    def test_run_generates_reports(self, mock_update, test_config, sample_pages, sample_posts, sample_products):
        agent = self._make_agent(test_config)
        agent.wp.get_pages.return_value = sample_pages
        agent.wp.get_posts.return_value = sample_posts
        agent.wp.get_products.return_value = sample_products

        # Override reports dir to use absolute path from test_config
        report_path = agent.run()

        assert os.path.exists(report_path)
        assert report_path.endswith(".md")

        # Check JSON output
        json_path = os.path.join(test_config["paths"]["reports_dir"], "corrections_pending.json")
        assert os.path.exists(json_path)
        with open(json_path) as f:
            corrections = json.load(f)
        assert isinstance(corrections, list)

    @patch("agents.agent_content.update_section")
    def test_apply_corrections_not_approved(self, mock_update, test_config):
        agent = self._make_agent(test_config)
        # Shared state says "pending" — should skip
        with patch("agents.shared_state.load_config", return_value=test_config):
            from agents.shared_state import save_state
            save_state({"content_audit": {"status": "pending"}, "blockers": []})
            agent.apply_corrections()
        mock_update.assert_not_called()

    @patch("agents.agent_content.update_section")
    def test_apply_corrections_approved_empty(self, mock_update, test_config):
        agent = self._make_agent(test_config)
        # Write empty corrections file
        json_path = os.path.join(test_config["paths"]["reports_dir"], "corrections_pending.json")
        with open(json_path, "w") as f:
            json.dump([], f)

        with patch("agents.shared_state.load_config", return_value=test_config):
            from agents.shared_state import save_state
            save_state({"content_audit": {"status": "approved"}, "blockers": []})
            agent.apply_corrections()

        mock_update.assert_called_once()
        assert mock_update.call_args[1].get("status") == "applied"


# ---------------------------------------------------------------------------
# Tests: Photo Manager
# ---------------------------------------------------------------------------

class TestPhotoManager:
    """Tests for agent_photos.py — PhotoManager."""

    def _make_agent(self, test_config):
        with patch("agents.agent_photos.load_config", return_value=test_config):
            from agents.agent_photos import PhotoManager
            agent = PhotoManager(test_config)
            agent.wp = MagicMock()
            return agent

    def test_missing_alt_text(self, test_config, sample_media):
        agent = self._make_agent(test_config)
        # IMG_2024 has empty alt_text
        agent._check_alt_text(sample_media[1])
        assert len(agent.issues) == 1
        assert agent.issues[0]["issue_type"] == "missing_alt"

    def test_short_alt_text(self, test_config, sample_media):
        agent = self._make_agent(test_config)
        # LombriThé has alt_text < 10 chars
        agent._check_alt_text(sample_media[2])
        assert len(agent.issues) == 1
        assert agent.issues[0]["issue_type"] == "short_alt"

    def test_good_alt_text(self, test_config, sample_media):
        agent = self._make_agent(test_config)
        agent._check_alt_text(sample_media[0])
        assert len(agent.issues) == 0

    def test_generic_filename_detected(self, test_config, sample_media):
        agent = self._make_agent(test_config)
        agent._check_filename(sample_media[1])  # IMG_2024.jpg
        assert len(agent.issues) == 1
        assert agent.issues[0]["issue_type"] == "generic_filename"

    def test_good_filename(self, test_config, sample_media):
        agent = self._make_agent(test_config)
        agent._check_filename(sample_media[0])  # ferme-nosvers.jpg
        assert len(agent.issues) == 0

    def test_low_resolution(self, test_config, sample_media):
        agent = self._make_agent(test_config)
        agent._check_dimensions(sample_media[1])  # 640x480
        assert len(agent.issues) == 1
        assert agent.issues[0]["issue_type"] == "low_resolution"

    def test_good_resolution(self, test_config, sample_media):
        agent = self._make_agent(test_config)
        agent._check_dimensions(sample_media[0])  # 1920x1080
        assert len(agent.issues) == 0

    def test_suggest_alt_text_from_title(self, test_config, sample_media):
        agent = self._make_agent(test_config)
        suggestion = agent._suggest_alt_text(sample_media[0])
        assert "NosVers" in suggestion

    def test_suggest_filename(self, test_config, sample_media):
        agent = self._make_agent(test_config)
        filename = agent._suggest_filename(sample_media[1])
        assert filename.startswith("nosvers-")
        assert filename.endswith(".jpg")

    def test_orphaned_media(self, test_config, sample_media, sample_pages):
        agent = self._make_agent(test_config)
        # Media item 11 is used as featured_media in sample_posts
        # but sample_pages[0] has featured_media=10
        orphan_media = [sample_media[1]]  # IMG_2024
        agent._check_orphaned_media(
            orphan_media,
            sample_pages, [], []
        )
        assert any(i["issue_type"] == "orphaned" for i in agent.issues)

    def test_products_without_images(self, test_config):
        agent = self._make_agent(test_config)
        products = [{"id": 300, "title": {"rendered": "Produit sans image"},
                      "link": "https://test.com/produit", "featured_media": 0}]
        agent._check_products_without_images(products)
        assert len(agent.photos_needed) == 1

    @patch("agents.agent_photos.update_section")
    def test_run_generates_reports(self, mock_update, test_config, sample_media, sample_pages, sample_products):
        agent = self._make_agent(test_config)
        agent.wp.get_media.return_value = sample_media
        agent.wp.get_pages.return_value = sample_pages
        agent.wp.get_posts.return_value = []
        agent.wp.get_products.return_value = sample_products

        report_path = agent.run()
        assert os.path.exists(report_path)

        json_path = os.path.join(test_config["paths"]["reports_dir"], "media_issues.json")
        assert os.path.exists(json_path)


# ---------------------------------------------------------------------------
# Tests: Social Media Manager
# ---------------------------------------------------------------------------

class TestSocialMediaManager:
    """Tests for agent_social.py — SocialMediaManager."""

    def _make_agent(self, test_config):
        with patch("agents.agent_social.load_config", return_value=test_config):
            from agents.agent_social import SocialMediaManager
            agent = SocialMediaManager(test_config)
            agent.wp = MagicMock()
            return agent

    def test_determine_content_type_product(self, test_config):
        agent = self._make_agent(test_config)
        item = {"_type": "product", "content": {"rendered": "test"}}
        assert agent._determine_content_type(item) == "product"

    def test_determine_content_type_education(self, test_config):
        agent = self._make_agent(test_config)
        item = {"_type": "post", "content": {"rendered": "<p>Comment utiliser le compost selon Dr. Elaine Ingham</p>"}}
        assert agent._determine_content_type(item) == "education"

    def test_determine_content_type_behind_scenes(self, test_config):
        agent = self._make_agent(test_config)
        item = {"_type": "post", "content": {"rendered": "<p>Aujourd'hui on a trié les vers.</p>"}}
        assert agent._determine_content_type(item) == "behind_scenes"

    def test_select_hashtags_always_includes_nosvers(self, test_config):
        agent = self._make_agent(test_config)
        hashtags = agent._select_hashtags("random text about something", count=5)
        assert "#NosVers" in hashtags

    def test_select_hashtags_relevance(self, test_config):
        agent = self._make_agent(test_config)
        hashtags = agent._select_hashtags("lombricompost artisanal en Dordogne", count=5)
        assert "#lombricompost" in hashtags
        assert "#Dordogne" in hashtags

    def test_get_cta(self, test_config):
        agent = self._make_agent(test_config)
        assert "nosvers.com" in agent._get_cta("product")
        assert "commentaire" in agent._get_cta("education")
        assert "Suivez" in agent._get_cta("behind_scenes")

    def test_generate_instagram(self, test_config):
        agent = self._make_agent(test_config)
        result = agent._generate_instagram(
            "Test Produit", "Un lombricompost artisanal de qualité.",
            "product", "https://test.com"
        )
        assert result["platform"] == "instagram"
        assert "caption" in result
        assert len(result["hashtags"]) > 0

    def test_generate_facebook(self, test_config):
        agent = self._make_agent(test_config)
        result = agent._generate_facebook(
            "Test Produit", "Un lombricompost artisanal de qualité.",
            "product", "https://test.com"
        )
        assert result["platform"] == "facebook"
        assert "https://test.com" in result["text"]

    def test_generate_tiktok(self, test_config):
        agent = self._make_agent(test_config)
        result = agent._generate_tiktok(
            "Test", "Le sol vivant est riche en micro-organismes.",
            "education", "https://test.com"
        )
        assert result["platform"] == "tiktok"
        assert "HOOK" in result["script"]

    def test_process_content_seeds(self, test_config):
        agent = self._make_agent(test_config)
        # Write a seed file
        seeds_dir = test_config["paths"]["content_seeds_dir"]
        with open(os.path.join(seeds_dir, "note_ferme.txt"), "w") as f:
            f.write("Journée de récolte\nAujourd'hui on a récolté 200kg de lombricompost frais "
                    "avec les vers de terre. Le sol est riche et vivant. La Dordogne nous offre "
                    "un climat parfait pour l'élevage de vers.")

        agent._process_content_seeds()
        assert len(agent.posts_generated) == 1
        assert agent.posts_generated[0]["content_type"] == "behind_scenes"

    @patch("agents.agent_social.load_state", return_value={"content_audit": {"status": "clean"}, "media_audit": {"status": "clean"}})
    @patch("agents.agent_social.update_section")
    def test_run_generates_queue(self, mock_update, mock_state, test_config, sample_posts, sample_products):
        agent = self._make_agent(test_config)
        agent.wp.get_posts.return_value = sample_posts
        agent.wp.get_products.return_value = sample_products

        report_path = agent.run()
        assert os.path.exists(report_path)

        json_path = os.path.join(test_config["paths"]["reports_dir"], "social_queue.json")
        assert os.path.exists(json_path)

    @patch("agents.agent_social.load_state")
    @patch("agents.agent_social.update_section")
    def test_blocking_logic(self, mock_update, mock_state, test_config, sample_posts):
        """Posts with pending corrections should be blocked."""
        mock_state.return_value = {
            "content_audit": {"status": "pending"},
            "media_audit": {"status": "clean"},
        }
        agent = self._make_agent(test_config)
        agent.wp.get_posts.return_value = sample_posts
        agent.wp.get_products.return_value = []

        # Write corrections that block the post
        corrections = [{"url": "https://test.nosvers.com/guide-lombricompost",
                         "issue_type": "grammar", "message": "test"}]
        json_path = os.path.join(test_config["paths"]["reports_dir"], "corrections_pending.json")
        with open(json_path, "w") as f:
            json.dump(corrections, f)

        agent.run()
        # The post should have been skipped
        assert len(agent.posts_generated) == 0


# ---------------------------------------------------------------------------
# Tests: Shared State
# ---------------------------------------------------------------------------

class TestSharedState:
    """Tests for shared_state.py."""

    def test_load_default(self, test_config):
        with patch("agents.shared_state.load_config", return_value=test_config):
            from agents.shared_state import load_state
            state = load_state()
        assert state["last_run"] is None
        assert "content_audit" in state
        assert "blockers" in state

    def test_save_and_load(self, test_config):
        with patch("agents.shared_state.load_config", return_value=test_config):
            from agents.shared_state import load_state, save_state
            state = load_state()
            state["content_audit"]["status"] = "approved"
            save_state(state)

            reloaded = load_state()
            assert reloaded["content_audit"]["status"] == "approved"
            assert reloaded["last_run"] is not None

    def test_update_section(self, test_config):
        with patch("agents.shared_state.load_config", return_value=test_config):
            from agents.shared_state import update_section, load_state
            update_section("content_audit", status="applied", issues_count=5)
            state = load_state()
            assert state["content_audit"]["status"] == "applied"
            assert state["content_audit"]["issues_count"] == 5

    def test_add_and_clear_blockers(self, test_config):
        with patch("agents.shared_state.load_config", return_value=test_config):
            from agents.shared_state import add_blocker, clear_blockers, load_state
            add_blocker("Test blocker", "test_agent")
            state = load_state()
            assert len(state["blockers"]) == 1
            assert state["blockers"][0]["description"] == "Test blocker"

            clear_blockers()
            state = load_state()
            assert len(state["blockers"]) == 0


# ---------------------------------------------------------------------------
# Tests: WP Client (unit tests with mocked requests)
# ---------------------------------------------------------------------------

class TestWPClient:
    """Tests for wp_client.py — WPClient."""

    def _make_client(self, test_config):
        with patch("agents.wp_client.load_config", return_value=test_config):
            from agents.wp_client import WPClient
            return WPClient(test_config)

    def test_base_url_construction(self, test_config):
        client = self._make_client(test_config)
        assert client.base_url == "https://test.nosvers.com"
        assert client.api_url == "https://test.nosvers.com/wp-json"

    @patch("requests.Session.request")
    def test_get_pages_calls_api(self, mock_request, test_config):
        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_resp.headers = {"X-WP-TotalPages": "1"}
        mock_resp.raise_for_status = MagicMock()
        mock_request.return_value = mock_resp

        client = self._make_client(test_config)
        pages = client.get_pages()
        assert pages == []
        mock_request.assert_called()

    @patch("requests.Session.request")
    def test_test_connection_success(self, mock_request, test_config):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "name": "NosVers",
            "description": "Test",
            "url": "https://test.nosvers.com",
            "namespaces": ["wp/v2"],
        }
        mock_resp.raise_for_status = MagicMock()
        mock_request.return_value = mock_resp

        client = self._make_client(test_config)
        result = client.test_connection()
        assert result["success"] is True
        assert result["name"] == "NosVers"

    @patch("requests.Session.request")
    def test_test_connection_failure(self, mock_request, test_config):
        from requests.exceptions import ConnectionError
        mock_request.side_effect = ConnectionError("Network error")

        client = self._make_client(test_config)
        result = client.test_connection()
        assert result["success"] is False
