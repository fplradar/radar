from datetime import datetime
import calendar
import feedparser


def collect_videos(feed):
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

