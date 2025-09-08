# export_ideas_today.py
# Construit data/ideas.json à partir des visuels générés.
# - Si le dossier du jour (social_images_out/YYYY-MM-DD) n'existe pas
#   ou est vide, on prend automatiquement le DERNIER dossier disponible.

from __future__ import annotations
import datetime as _dt
import pathlib as _pl
import json as _json
import re as _re

BASE = _pl.Path(__file__).resolve().parent
IMAGES_ROOT = BASE / "social_images_out"
OUT_DIR = BASE / "data"
OUT_FILE = OUT_DIR / "ideas.json"

def _slug_to_title(name: str) -> str:
    name = _re.sub(r"\.[A-Za-z0-9]+$", "", name)  # retire extension
    name = _re.sub(r"^(?:\d{1,2}_)*\d{1,2}_", "", name)  # retire préfixes numériques
    name = name.replace("_", " ").replace("-", " ")
    name = _re.sub(r"\s+", " ", name).strip()
    return name[:1].upper() + name[1:] if name else "Idée"

def _extract_titles_from_md(md_path: _pl.Path) -> list[str]:
    titles: list[str] = []
    if not md_path.exists():
        return titles
    text = md_path.read_text(encoding="utf-8", errors="ignore")
    # Titres "## ..."
    for line in text.splitlines():
        m = _re.match(r"^\s{0,3}#{2,3}\s+(.+?)\s*$", line)
        if m:
            titles.append(m.group(1).strip())
    # Sinon, puces "- ..."
    if not titles:
        for line in text.splitlines():
            m = _re.match(r"^\s*[-*]\s+(.+?)\s*$", line)
            if m:
                titles.append(m.group(1).strip())
    return titles

def _find_target_date_folder() -> tuple[_pl.Path, str] | None:
    today = _dt.date.today().strftime("%Y-%m-%d")
    today_dir = IMAGES_ROOT / today
    # 1) si le dossier d'aujourd'hui a des PNG, on le prend
    if today_dir.exists() and any(today_dir.glob("*.png")):
        return today_dir, today
    # 2) sinon, on prend le dernier dossier AAAA-MM-JJ qui contient des PNG
    candidates = []
    if IMAGES_ROOT.exists():
        for p in IMAGES_ROOT.iterdir():
            if p.is_dir() and _re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.name):
                if any(p.glob("*.png")):
                    candidates.append(p)
    if not candidates:
        return None
    candidates.sort(key=lambda d: d.name, reverse=True)  # le plus récent en premier
    chosen = candidates[0]
    return chosen, chosen.name

def main() -> None:
    found = _find_target_date_folder()
    if not found:
        print(f"[INFO] Aucun dossier d'images trouvé dans {IMAGES_ROOT}")
        return
    images_dir, date_str = found
    print(f"[INFO] Dossier utilisé : {images_dir}")

    images = sorted(images_dir.glob("*.png"), key=lambda p: p.name.lower())
    if not images:
        print(f"[INFO] Aucune image .png dans {images_dir}")
        return

    # titles depuis fpl_summaries/social_YYYY-MM-DD.md si présent
    md_path = BASE / "fpl_summaries" / f"social_{date_str}.md"
    md_titles = _extract_titles_from_md(md_path)

    ideas = []
    for idx, img in enumerate(images):
        title = md_titles[idx] if idx < len(md_titles) else _slug_to_title(img.name)
        ideas.append({
            "title": title,
            "description": f"Visuel social du {date_str}",
            "metrics": {"views": 0, "score": 0},
            "image_path": img.as_posix(),
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(_json.dumps(ideas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {len(ideas)} idées exportées vers {OUT_FILE}")

if __name__ == "__main__":
    main()
