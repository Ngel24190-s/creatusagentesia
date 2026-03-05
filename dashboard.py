#!/usr/bin/env python3
"""NosVers Dashboard — Generates an HTML report from agent outputs.

Usage:
    python dashboard.py              # Generate and open dashboard
    python dashboard.py --no-open    # Generate without opening browser
"""

import os
import sys
import json
import argparse
import webbrowser
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.config_loader import load_config


def _load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _escape(text):
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def generate_dashboard():
    config = load_config()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(base_dir, config["paths"]["reports_dir"])
    state_path = os.path.join(base_dir, config["paths"]["shared_state"])

    # Load data
    state = _load_json(state_path) or {}
    corrections = _load_json(os.path.join(reports_dir, "corrections_pending.json")) or []
    media_data = _load_json(os.path.join(reports_dir, "media_issues.json")) or {}
    social_queue = _load_json(os.path.join(reports_dir, "social_queue.json")) or []

    media_issues = media_data.get("issues", []) if isinstance(media_data, dict) else []
    photos_needed = media_data.get("photos_needed", []) if isinstance(media_data, dict) else []

    ca = state.get("content_audit", {})
    ma = state.get("media_audit", {})
    sq = state.get("social_queue", {})
    blockers = state.get("blockers", [])

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Group content issues by type
    content_by_type = {}
    for c in corrections:
        t = c.get("issue_type", "other")
        content_by_type.setdefault(t, []).append(c)

    # Group media issues by type
    media_by_type = {}
    for m in media_issues:
        t = m.get("issue_type", "other")
        media_by_type.setdefault(t, []).append(m)

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NosVers — Dashboard Agent Ecosystem</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; line-height: 1.6; }}
.header {{ background: linear-gradient(135deg, #1e3a2f 0%, #2d1b3d 100%); padding: 2rem; text-align: center; border-bottom: 3px solid #22c55e; }}
.header h1 {{ font-size: 2rem; color: #22c55e; margin-bottom: 0.5rem; }}
.header .subtitle {{ color: #94a3b8; font-size: 0.9rem; }}
.container {{ max-width: 1400px; margin: 0 auto; padding: 1.5rem; }}

/* Summary cards */
.summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
.card {{ background: #1e293b; border-radius: 12px; padding: 1.5rem; border-left: 4px solid #3b82f6; }}
.card.green {{ border-left-color: #22c55e; }}
.card.orange {{ border-left-color: #f59e0b; }}
.card.red {{ border-left-color: #ef4444; }}
.card.purple {{ border-left-color: #a855f7; }}
.card h3 {{ color: #94a3b8; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem; }}
.card .number {{ font-size: 2.5rem; font-weight: 700; color: #f8fafc; }}
.card .status {{ display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; margin-top: 0.5rem; }}
.status.pending {{ background: #f59e0b22; color: #f59e0b; }}
.status.draft {{ background: #3b82f622; color: #3b82f6; }}
.status.applied {{ background: #22c55e22; color: #22c55e; }}

/* Sections */
.section {{ background: #1e293b; border-radius: 12px; margin-bottom: 1.5rem; overflow: hidden; }}
.section-header {{ padding: 1rem 1.5rem; background: #334155; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }}
.section-header h2 {{ font-size: 1.1rem; color: #f8fafc; }}
.section-header .badge {{ background: #ef4444; color: white; padding: 2px 10px; border-radius: 12px; font-size: 0.8rem; }}
.section-body {{ padding: 1.5rem; }}

/* Tables */
table {{ width: 100%; border-collapse: collapse; }}
th {{ text-align: left; padding: 0.75rem; color: #94a3b8; font-size: 0.8rem; text-transform: uppercase; border-bottom: 1px solid #334155; }}
td {{ padding: 0.75rem; border-bottom: 1px solid #1e293b44; font-size: 0.9rem; vertical-align: top; }}
tr:hover {{ background: #334155; }}
.tag {{ display: inline-block; padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }}
.tag.grammar {{ background: #3b82f622; color: #3b82f6; }}
.tag.brand {{ background: #ef444422; color: #ef4444; }}
.tag.seo {{ background: #f59e0b22; color: #f59e0b; }}
.tag.content {{ background: #a855f722; color: #a855f7; }}
.tag.alt {{ background: #06b6d422; color: #06b6d4; }}
.tag.filename {{ background: #8b5cf622; color: #8b5cf6; }}
.tag.resolution {{ background: #f9731622; color: #f97316; }}
.tag.orphaned {{ background: #64748b22; color: #64748b; }}
.suggestion {{ color: #22c55e; font-style: italic; }}
.snippet {{ color: #94a3b8; font-family: monospace; font-size: 0.8rem; max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}

/* Social posts */
.social-post {{ background: #0f172a; border-radius: 8px; padding: 1.25rem; margin-bottom: 1rem; border: 1px solid #334155; }}
.social-post h4 {{ color: #f8fafc; margin-bottom: 0.5rem; }}
.social-post .meta {{ color: #64748b; font-size: 0.8rem; margin-bottom: 1rem; }}
.platforms {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; }}
.platform {{ background: #1e293b; border-radius: 8px; padding: 1rem; }}
.platform h5 {{ margin-bottom: 0.5rem; }}
.platform h5.ig {{ color: #e1306c; }}
.platform h5.fb {{ color: #1877f2; }}
.platform h5.tk {{ color: #00f2ea; }}
.platform pre {{ white-space: pre-wrap; font-size: 0.8rem; color: #cbd5e1; font-family: inherit; line-height: 1.5; }}

/* Blockers */
.blocker {{ background: #ef444422; border: 1px solid #ef4444; border-radius: 8px; padding: 1rem; margin-bottom: 0.5rem; }}
.no-issues {{ color: #22c55e; text-align: center; padding: 2rem; font-size: 1.1rem; }}

.footer {{ text-align: center; padding: 2rem; color: #475569; font-size: 0.8rem; }}
</style>
</head>
<body>
<div class="header">
    <h1>NosVers Agent Ecosystem</h1>
    <div class="subtitle">Dashboard — {now} | Dernier run : {state.get('last_run', 'Jamais')}</div>
</div>

<div class="container">

<!-- Summary Cards -->
<div class="summary">
    <div class="card orange">
        <h3>Anomalies Contenu</h3>
        <div class="number">{len(corrections)}</div>
        <span class="status pending">{ca.get('status', '—')}</span>
    </div>
    <div class="card red">
        <h3>Anomalies Medias</h3>
        <div class="number">{len(media_issues)}</div>
        <span class="status pending">{ma.get('status', '—')}</span>
    </div>
    <div class="card purple">
        <h3>Posts Sociaux</h3>
        <div class="number">{len(social_queue)}</div>
        <span class="status draft">{sq.get('status', '—')}</span>
    </div>
    <div class="card green">
        <h3>Photos Necessaires</h3>
        <div class="number">{len(photos_needed)}</div>
        <span class="status pending">{'a prendre' if photos_needed else 'ok'}</span>
    </div>
</div>
"""

    # Blockers
    if blockers:
        html += '<div class="section"><div class="section-header"><h2>Blocages</h2>'
        html += f'<span class="badge">{len(blockers)}</span></div><div class="section-body">'
        for b in blockers:
            html += f'<div class="blocker"><strong>[{_escape(b.get("agent", "?"))}]</strong> {_escape(b.get("description", ""))}</div>'
        html += '</div></div>'

    # Content Issues
    html += f"""
<div class="section">
    <div class="section-header">
        <h2>Audit du Contenu</h2>
        <span class="badge">{len(corrections)} anomalies</span>
    </div>
    <div class="section-body">
"""
    if not corrections:
        html += '<div class="no-issues">Aucune anomalie de contenu detectee</div>'
    else:
        html += '<table><thead><tr><th>Type</th><th>Page</th><th>Probleme</th><th>Extrait</th><th>Suggestion</th></tr></thead><tbody>'
        for c in corrections:
            itype = c.get("issue_type", "")
            tag_class = {"grammar": "grammar", "brand_drift": "brand", "seo": "seo", "content": "content"}.get(itype, "")
            tag_label = {"grammar": "Grammaire", "brand_drift": "Marque", "seo": "SEO", "content": "Contenu"}.get(itype, itype)
            url = _escape(c.get("url", ""))
            short_url = url.split("/")[-1] or url.split("/")[-2] if "/" in url else url
            msg = _escape(c.get("message", ""))
            original = _escape(str(c.get("original", ""))[:80])
            suggestion = c.get("suggestion", "")
            if isinstance(suggestion, list):
                suggestion = " / ".join(suggestion[:3])
            suggestion = _escape(str(suggestion)[:100])
            html += f'<tr><td><span class="tag {tag_class}">{tag_label}</span></td>'
            html += f'<td><a href="{url}" style="color:#3b82f6" target="_blank">{_escape(short_url)}</a></td>'
            html += f'<td>{msg}</td><td class="snippet">{original}</td>'
            html += f'<td class="suggestion">{suggestion}</td></tr>'
        html += '</tbody></table>'
    html += '</div></div>'

    # Media Issues
    html += f"""
<div class="section">
    <div class="section-header">
        <h2>Audit des Medias</h2>
        <span class="badge">{len(media_issues)} anomalies</span>
    </div>
    <div class="section-body">
"""
    if not media_issues:
        html += '<div class="no-issues">Aucune anomalie media detectee</div>'
    else:
        html += '<table><thead><tr><th>Type</th><th>ID</th><th>Fichier</th><th>Probleme</th><th>Suggestion</th></tr></thead><tbody>'
        for m in media_issues:
            itype = m.get("issue_type", "")
            tag_class = {"missing_alt": "alt", "short_alt": "alt", "generic_filename": "filename",
                         "low_resolution": "resolution", "orphaned": "orphaned"}.get(itype, "")
            tag_label = {"missing_alt": "Alt manquant", "short_alt": "Alt court", "generic_filename": "Nom generique",
                         "low_resolution": "Basse res.", "orphaned": "Orphelin"}.get(itype, itype)
            filename = _escape(os.path.basename(m.get("source_url", "")))
            msg = _escape(m.get("message", ""))
            suggestion = _escape(str(m.get("suggestion", ""))[:80])
            html += f'<tr><td><span class="tag {tag_class}">{tag_label}</span></td>'
            html += f'<td>{m.get("media_id", "")}</td><td>{filename}</td>'
            html += f'<td>{msg}</td><td class="suggestion">{suggestion}</td></tr>'
        html += '</tbody></table>'
    html += '</div></div>'

    # Photos Needed
    if photos_needed:
        html += '<div class="section"><div class="section-header"><h2>Photos a Prendre</h2>'
        html += f'<span class="badge">{len(photos_needed)}</span></div><div class="section-body"><table>'
        html += '<thead><tr><th>Produit</th><th>URL</th><th>Ce qu\'il faut</th></tr></thead><tbody>'
        for p in photos_needed:
            html += f'<tr><td><strong>{_escape(p.get("product", ""))}</strong></td>'
            html += f'<td><a href="{_escape(p.get("url", ""))}" style="color:#3b82f6" target="_blank">Voir</a></td>'
            html += f'<td>{_escape(p.get("need", ""))}</td></tr>'
        html += '</tbody></table></div></div>'

    # Social Queue
    html += f"""
<div class="section">
    <div class="section-header">
        <h2>File d'Attente Reseaux Sociaux</h2>
        <span class="badge">{len(social_queue)} posts</span>
    </div>
    <div class="section-body">
"""
    if not social_queue:
        html += '<div class="no-issues">Aucun post genere</div>'
    else:
        for idx, post in enumerate(social_queue, 1):
            title = _escape(post.get("title", "Sans titre"))
            ctype = post.get("content_type", "")
            status = _escape(post.get("status", "a valider"))
            variants = post.get("variants", {})
            html += f'<div class="social-post"><h4>{idx}. {title}</h4>'
            html += f'<div class="meta">Type: {ctype} | Source: {_escape(post.get("source_url", ""))} | Statut: {status}</div>'
            html += '<div class="platforms">'

            ig = variants.get("instagram", {})
            if ig:
                html += f'<div class="platform"><h5 class="ig">Instagram</h5><pre>{_escape(ig.get("caption", ""))}</pre></div>'

            fb = variants.get("facebook", {})
            if fb:
                html += f'<div class="platform"><h5 class="fb">Facebook</h5><pre>{_escape(fb.get("text", ""))}</pre></div>'

            tk = variants.get("tiktok", {})
            if tk:
                html += f'<div class="platform"><h5 class="tk">TikTok / Reels</h5><pre>{_escape(tk.get("script", ""))}</pre></div>'

            html += '</div></div>'

    html += '</div></div>'

    # Footer
    html += f"""
</div>
<div class="footer">
    NosVers Agent Ecosystem v1.0 — Genere le {now}<br>
    Pour approuver les corrections, editez <code>shared_state.json</code> et changez les statuts en "approved".
</div>
</body>
</html>"""

    # Write HTML
    output_path = os.path.join(reports_dir, "dashboard.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Dashboard generated: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="NosVers — Generate HTML Dashboard")
    parser.add_argument("--no-open", action="store_true", help="Don't open browser automatically")
    args = parser.parse_args()

    path = generate_dashboard()

    if not args.no_open:
        webbrowser.open(f"file://{os.path.abspath(path)}")
        print("Opening in browser...")


if __name__ == "__main__":
    main()
