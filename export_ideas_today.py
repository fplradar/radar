# export_ideas_today.py
# Construit data/ideas.json à partir des visuels du jour (social_images_out/YYYY-MM-DD)
# et, si disponible, des titres trouvés dans fpl_summaries/social_YYYY-MM-DD.md

from __future__ import annotations
import datetime as _dt
import pathlib as _pl
import json as _json
import re as _re

BASE = _pl.Path(__file__).resolve().parent
TODAY = _dt.date.today().strftime("%Y-%m-%d")

SOCIAL_MD = BASE / "fpl_summaries" / f"social_{TODAY}.md"
IMAGES_DIR = BASE / "social_images_out" / TODAY
OUT_DIR = BASE / "data"
OUT_FILE = OUT_DIR / "ideas.json"

def _slug_to_title(name: str) -> str:
    # retire extension
    name = _re.sub(r"\.[A-Za-z0-9]+$", "", name)
    # retire préfixes numériques type "01_01_" ou "01_"
    name = _re.sub(r"^(?:\d{1,2}_)*\d{1,2}_", "", name)
    # underscores/traits -> espaces
    name = name.replace("_", " ").replace("-", " ")
    # compresse espaces
    name = _re.sub(r"\s+", " ", name).strip()
    # capitalisation douce
    if name:
        name = name[0].upper() + name[1:]
    return name or "Idée"

def _extract_titles_from_md(md_path: _pl.Path) -> list[str]:
    titles: list[str] = []
    if not md_path.exists():
        return titles
    text = md_path.read_text(encoding="utf-8", errors="ignore")
    # Cherche des titres de type "## Titre"
    for line in text.splitlines():
        m = _re.match(r"^\s{0,3}#{2,3}\s+(.+?)\s*$", line)
        if m:
            titles.append(m.group(1).strip())
    # fallback: puces
    if not titles:
        for line in text.splitlines():
            m = _re.match(r"^\s*[-*]\s+(.+?)\s*$", line)
            if m:
                titles.append(m.group(1).strip())
    return titles

def main() -> None:
    if not IMAGES_DIR.exists():
        print(f"[INFO] Dossier images introuvable: {IMAGES_DIR}")
        print("[INFO] Aucune idée exportée.")
        return

    images = sorted([p for p in IMAGES_DIR.glob("*.png")], key=lambda p: p.name.lower())
    if not images:
        print(f"[INFO] Aucune image .png dans {IMAGES_DIR}")
        return

    md_titles = _extract_titles_from_md(SOCIAL_MD)

    ideas = []
    for idx, img in enumerate(images):
        # titre depuis le markdown si dispo, sinon à partir du nom de fichier
        title = md_titles[idx] if idx < len(md_titles) else _slug_to_title(img.name)
        idea = {
            "title": title,
            "description": f"Visuel social du {TODAY}",
            "metrics": {"views": 0, "score": 0},
            "image_path": img.as_posix(),  # chemin utilisable par le rapport HTML
        }
        ideas.append(idea)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(_json.dumps(ideas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {len(ideas)} idées exportées vers {OUT_FILE}")

if __name__ == "__main__":
    main()
