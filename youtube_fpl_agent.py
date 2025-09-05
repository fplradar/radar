from datetime import datetime
import calendar
import feedparser

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

    ...
feed = feedparser.parse("https://www.youtube.com/feeds/videos.xml?channel_id=UCiDF_uaU1V00dAc8ddKvNxA")  # Exemple: chaîne YouTube officielle FPL

videos = collect_videos(feed)

# Affiche les 5 vidéos les plus récentes
for video in videos[:5]:
    print(f"[{video['published_dt'].strftime('%Y-%m-%d')}] {video['title']}")
    print(f"🔗 {video['url']}\n")

now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

with open("resume.md", "w", encoding="utf-8") as f:
    f.write(f"# Rapport automatique\n\nDernière exécution : {now}\n")

print("Fichier resume.md généré.")

