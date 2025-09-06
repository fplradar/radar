from datetime import datetime, UTC
import os
import re
import time
import argparse
import feedparser
# Transcripts désactivés pour l’instant (429)
# from youtube_transcript_api import YouTubeTranscriptApi

# --------- Paramètres par défaut ---------
USE_TRANSCRIPTS = False   # garder False pour éviter 429
DEFAULT_CHANNEL = "UCVPb_jLxwaoYd-Dm7aSWQKQ"  # FPL Tips
DEFAULT_LIMIT = 5
PAUSE_S = 0.5             # petite pause entre vidéos

# --------- Flux YouTube ---------

def collect_videos(feed):
    videos = []
    for entry in getattr(feed, 'entries', []):
        published_dt = None
        if getattr(entry, 'published_parsed', None):
            published_dt = datetime(*entry.published_parsed[:6], tzinfo=UTC)
        else:
            for attr in ("published", "updated"):
                val = getattr(entry, attr, None)
                if val:
                    try:
                        parsed = feedparser._parse_date(val)
                        if parsed:
                            published_dt = datetime(*parsed[:6], tzinfo=UTC)
                            break
                    except Exception:
                        pass
        if not published_dt:
            continue
        videos.append({
            'id': getattr(entry, 'yt_videoid', None) or (entry.get('yt_videoid') if hasattr(entry, 'get') else None),
            'title': getattr(entry, 'title', None) or (entry.get('title') if hasattr(entry, 'get') else None),
            'url': getattr(entry, 'link', None) or (entry.get('link') if hasattr(entry, 'get') else None),
            'published_dt': published_dt,
        })
    videos.sort(key=lambda v: v['published_dt'], reverse=True)
    return videos

# --------- Résumé (fallback sans transcript) ---------

def summarize_from_title(title: str) -> str:
    if not title:
        return "Résumé indisponible."
    t = title.strip()
    t = re.sub(r"\s+", " ", t)
    words = [w for w in re.split(r"[^\w']+", t) if w]
    tags = []
    for w in words:
        if w.upper() in {
            "GW1","GW2","GW3","GW4","GW5","GW6","GW7","GW8","GW9","GW10",
            "GW11","GW12","GW13","GW14","GW15","GW16","GW17","GW18","GW19",
            "GW20","GW21","GW22","GW23","GW24","GW25","GW26","GW27","GW28",
            "GW29","GW30","GW31","GW32","GW33","GW34","GW35","GW36","GW37","GW38"}:
            tags.append(w.upper())
        elif w.lower() in {"wildcard","free","hit","draft","watchlist","team","selection","tips","picks"}:
            tags.append(w.capitalize())
    tags = list(dict.fromkeys(tags))
    hint = f" ({', '.join(tags)})" if tags else ""
    return f"Vidéo FPL : {t}{hint}"

def generate_summary(title: str, transcript: str | None) -> str:
    if USE_TRANSCRIPTS and transcript:
        text = transcript.strip().replace("\n", " ")
        text = re.sub(r"\s+", " ", text)
        text = text[:2000]
        sentences = re.split(r"(?<=[.!?])\s+", text)
        summary = " ".join(sentences[:3]).strip()
        return summary + (" ..." if len(sentences) > 3 else "")
    return summarize_from_title(title or "")

# --------- CLI ---------

def parse_args():
    p = argparse.ArgumentParser(description="FPL Radar — résumés YouTube (sans transcription).")
    p.add_argument("--channel", "-c", default=DEFAULT_CHANNEL, help="YouTube channel_id (UC....)")
    p.add_argument("--limit", "-n", type=int, default=DEFAULT_LIMIT, help="Nombre de vidéos à traiter")
    return p.parse_args()

# --------- Point d'entrée ---------

if __name__ == "__main__":
    args = parse_args()
    ucid = args.channel.strip()
    limit = max(1, args.limit)

    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={ucid}"
    print(f"Flux utilisé : {feed_url}")

    feed = feedparser.parse(feed_url)
    videos = collect_videos(feed)
    print(f"{len(videos)} vidéos trouvées (avant filtre Shorts).")

    # Ignorer les Shorts
    videos = [v for v in videos if '/shorts/' not in (v.get('url') or '')]
    print(f"{len(videos)} vidéos après filtre Shorts.")

    # Affichage + pause
    for video in videos[:limit]:
        print(f"[{video['published_dt'].strftime('%Y-%m-%d')}] {video['title']}")
        print(f"🔗 {video['url']}")
        summary = generate_summary(video['title'], None)
        print("Résumé :")
        print(summary)
        print("\n" + "-" * 40 + "\n")
        time.sleep(PAUSE_S)

    # Écriture Markdown quotidienne
    os.makedirs("fpl_summaries", exist_ok=True)
    date_str = datetime.now(UTC).strftime("%Y-%m-%d")
    output_path = os.path.join("fpl_summaries", f"{date_str}.md")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# Résumés YouTube — {date_str}\n\n")
        for video in videos[:limit]:
            summary = generate_summary(video['title'], None)
            f.write(f"## {video['published_dt'].strftime('%Y-%m-%d')} — {video['title']}\n")
            f.write(f"🔗 {video['url']}\n\n")
            f.write(f"Résumé :\n{summary}\n\n---\n\n")
            time.sleep(PAUSE_S)

    print(f"📁 Résumés écrits dans {output_path}")
