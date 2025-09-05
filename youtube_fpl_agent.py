from datetime import datetime
import calendar
import feedparser
from youtube_transcript_api import YouTubeTranscriptApi

def collect_videos(feed):
    videos = []

    for entry in getattr(feed, 'entries', []):
        published_dt = None

        # 1) Priorité à published_parsed (struct_time)
        if getattr(entry, 'published_parsed', None):
            published_dt = datetime(*entry.published_parsed[:6])
        else:
            # 2) Repli sur published ou updated (chaînes)
            for attr in ("published", "updated"):
                val = getattr(entry, attr, None)
                if val:
                    try:
                        parsed = feedparser._parse_date(val)
                        if parsed:
                            published_dt = datetime(*parsed[:6])
                            break
                    except Exception:
                        pass

        # Ignorer si aucune date valable
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

def fetch_transcript(video_id):
    """
    Récupère la transcription brute d'une vidéo YouTube si disponible.
    Retourne une chaîne de caractères ou None.
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["fr", "en"])
        return " ".join([t["text"] for t in transcript])
    except Exception as e:
        print(f"⚠️ Erreur lors de la récupération de la transcription pour {video_id} : {e}")
        return None

def generate_summary(transcript):
    """
    Reçoit la transcription d'une vidéo et retourne un résumé structuré.
    (Version simple, à améliorer plus tard si besoin)
    """
    if not transcript:
        return "Résumé indisponible (pas de transcription trouvée)."

    # Limiter la taille si nécessaire
    text = transcript[:2000]

    # Exemple très simple : garder les premières phrases comme résumé
    lines = text.split(". ")
    summary = ". ".join(lines[:3]).strip()

    return summary + ("..." if len(lines) > 3 else "")

# === Point d’entrée ===

feed = feedparser.parse("https://www.youtube.com/feeds/videos.xml?channel_id=UCiDF_uaU1V00dAc8ddKvNxA")

videos = collect_videos(feed)

for video in videos[:5]:
    print(f"[{video['published_dt'].strftime('%Y-%m-%d')}] {video['title']}")
    print(f"🔗 {video['url']}")

    transcript = fetch_transcript(video['id'])
    summary = generate_summary(transcript)

    print("Résumé :")
    print(summary)
    print("\n" + "-" * 40 + "\n")

now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

with open("resume.md", "w", encoding="utf-8") as f:
    f.write(f"# Rapport automatique\n\nDernière exécution : {now}\n")

print("Fichier resume.md généré.")
