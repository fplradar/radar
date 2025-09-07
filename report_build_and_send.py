# report_build_and_send.py
# Génère un rapport HTML avec résumé global puis fiches idées (avec images),
# puis envoie par Outlook si variable d’environnement REPORT_EMAIL_TO est définie.

from __future__ import annotations
import json, os, datetime, pathlib, statistics
from typing import List, Dict, Any

BASE_DIR = pathlib.Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "ideas.json"          # <-- par défaut
OUT_DIR   = BASE_DIR / "out"
OUT_FILE  = OUT_DIR / "report.html"

def load_data(path: pathlib.Path) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "ideas" in data:
        data = data["ideas"]
    assert isinstance(data, list), "Le fichier JSON doit contenir une liste d'idées."
    return data

def build_summary(ideas: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(ideas)
    metrics_all = [i.get("metrics", {}) for i in ideas]
    def avg(key, default=0.0):
        vals = [float(m.get(key, 0)) for m in metrics_all if key in m]
        return round(statistics.fmean(vals), 2) if vals else default
    top_by = lambda k: sorted(ideas, key=lambda x: float(x.get("metrics", {}).get(k, 0)), reverse=True)

    summary = {
        "count": n,
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "avg_views": avg("views"),
        "avg_score": avg("score"),
        "top_views": top_by("views")[:3],
        "top_score": top_by("score")[:3],
    }
    return summary

def html_escape(s: str) -> str:
    import html
    return html.escape(s, quote=True)

def card_html(idea: Dict[str, Any]) -> str:
    title = html_escape(str(idea.get("title", "Sans titre")))
    desc  = html_escape(str(idea.get("description", "")))
    m = idea.get("metrics", {})
    views = m.get("views", "")
    score = m.get("score", "")
    img   = idea.get("image_url") or idea.get("image_path") or ""
    img_tag = f'<img src="{html_escape(img)}" alt="image" style="max-width:320px;border-radius:12px;border:1px solid #ddd;" />' if img else ""

    extra_rows = ""
    for k, v in m.items():
        if k not in ("views", "score"):
            extra_rows += f"<div><span style='opacity:.7'>{html_escape(k)}:</span> {html_escape(str(v))}</div>"

    return f"""
    <div style="border:1px solid #e5e7eb;border-radius:16px;padding:16px;display:flex;gap:16px;align-items:flex-start;">
      {img_tag}
      <div style="flex:1;min-width:0">
        <h3 style="margin:0 0 8px 0;font-family:Segoe UI,Arial,sans-serif">{title}</h3>
        <p style="margin:0 0 8px 0;opacity:.9">{desc}</p>
        <div style="display:flex;gap:16px;margin-top:8px;flex-wrap:wrap">
          <div><strong>Vues:</strong> {views}</div>
          <div><strong>Score:</strong> {score}</div>
          {extra_rows}
        </div>
      </div>
    </div>
    """

def render_html(summary: Dict[str, Any], ideas: List[Dict[str, Any]]) -> str:
    head = """
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>FPL Radar — Rapport quotidien</title>
    """
    css = """
    body{font-family:Segoe UI,Arial,sans-serif;background:#fafafa;color:#111;margin:24px;}
    .wrap{max-width:1000px;margin:0 auto;display:flex;flex-direction:column;gap:16px}
    .grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
    .chip{background:#eef2ff;color:#3730a3;padding:6px 10px;border-radius:999px;display:inline-block}
    h1{margin:.2em 0}
    """
    top_views_html = "".join(f"<li>{html_escape(i.get('title',''))} — {i.get('metrics',{}).get('views','')}</li>" for i in summary["top_views"])
    top_score_html = "".join(f"<li>{html_escape(i.get('title',''))} — {i.get('metrics',{}).get('score','')}</li>" for i in summary["top_score"])

    cards = "\n".join(card_html(i) for i in ideas)

    return f"""<!doctype html>
<html lang="fr">
<head>{head}<style>{css}</style></head>
<body>
  <div class="wrap">
    <header>
      <h1>FPL Radar — Rapport quotidien</h1>
      <div class="grid">
        <span class="chip">Généré: {summary['generated_at']}</span>
        <span class="chip">Nb idées: {summary['count']}</span>
        <span class="chip">Vues moy.: {summary['avg_views']}</span>
      </div>
      <div style="display:flex;gap:24px;flex-wrap:wrap;margin-top:8px">
        <div>
          <h3>Top vues</h3>
          <ol>{top_views_html}</ol>
        </div>
        <div>
          <h3>Top score</h3>
          <ol>{top_score_html}</ol>
        </div>
      </div>
    </header>
    <hr style="border:none;border-top:1px solid #e5e7eb;margin:8px 0 16px 0"/>
    <section>
      <h2>Idées (avec images)</h2>
      <div style="display:flex;flex-direction:column;gap:12px">{cards}</div>
    </section>
  </div>
</body>
</html>"""

def save_html(html: str, path: pathlib.Path) -> pathlib.Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path

def try_send_outlook(subject: str, html_body: str, attachment_path: pathlib.Path | None = None) -> bool:
    """
    Envoi via Outlook si disponible et si REPORT_EMAIL_TO est défini.
    - REPORT_EMAIL_TO: destinataire(s), séparés par ';'
    - REPORT_EMAIL_SUBJECT (optionnel)
    """
    to = os.getenv("REPORT_EMAIL_TO")
    if not to:
        return False
    try:
        import win32com.client  # pywin32
    except Exception:
        return False

    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)
    mail.To = to
    mail.Subject = os.getenv("REPORT_EMAIL_SUBJECT", subject)
    mail.HTMLBody = html_body
    if attachment_path and attachment_path.exists():
        mail.Attachments.Add(str(attachment_path))
    mail.Send()
    return True

def main():
    ideas = load_data(DATA_FILE)
    summary = build_summary(ideas)
    html = render_html(summary, ideas)
    saved = save_html(html, OUT_FILE)

    subject = f"[FPL Radar] Rapport {summary['generated_at']}"
    sent = try_send_outlook(subject, html_body=html, attachment_path=saved)

    print(f"[OK] Rapport généré: {saved}")
    if sent:
        print(f"[OK] Email envoyé à REPORT_EMAIL_TO.")
    else:
        print("[INFO] Email non envoyé (Outlook indisponible ou REPORT_EMAIL_TO non défini).")

if __name__ == "__main__":
    main()
