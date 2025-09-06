from datetime import datetime, UTC
import os
import re
import time
import argparse
import feedparser
import unicodedata

# Optionnelle si tu utilises --voiceover
try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

# --------- Paramètres par défaut ---------
USE_TRANSCRIPTS = False
DEFAULT_CHANNEL = "UCVPb_jLxwaoYd-Dm7aSWQKQ"
DEFAULT_LIMIT = 5
PAUSE_S = 0.5
CHANNELS_FILE = "channels.txt"

# --------- Utilitaires ---------

def slugify_filename(text: str, max_len: int = 40) -> str:
    """
    Nom de fichier sûr pour Windows/macOS/Linux.
    """
    if not text:
        text = "image"
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r'[<>:"/\\|?*]', "_", text)
    text = re.sub(r"[^A-Za-z0-9_-]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("._-")
    if not text:
        text = "image"
    if len(text) > max_len:
        text = text[:max_len].rstrip("._-") or "image"
    reserved = {"CON","PRN","AUX","NUL","COM1","COM2","COM3","COM4","COM5","COM6","COM7","COM8","COM9",
                "LPT1","LPT2","LPT3","LPT4","LPT5","LPT6","LPT7","LPT8","LPT9"}
    if text.upper() in reserved:
        text = f"{text}_file"
    return text or "image"

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
            'id': getattr(entry, 'yt_videoid', None),
            'title': getattr(entry, 'title', None),
            'url': getattr(entry, 'link', None),
            'published_dt': published_dt,
        })
    videos.sort(key=lambda v: v['published_dt'], reverse=True)
    return videos

# --------- Résumé ---------

def summarize_from_title(title: str) -> str:
    if not title:
        return "Résumé indisponible."
    t = title.strip()
    t = re.sub(r"\s+", " ", t)
    words = [w for w in re.split(r"[^\w']+", t) if w]
    tags = []
    for w in words:
        if w.upper().startswith("GW"):
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

# --------- Génération d'images ---------

def extract_prompts_from_script(script_path: str):
    """
    Extrait des lignes 'illustrables' du script social.
    """
    prompts = []
    with open(script_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if len(line) < 10:
                continue
            prompts.append(line)
    return prompts

def generate_images_from_prompts(prompts: list[str], output_dir: str):
    """
    Sauvegarde chaque prompt en .txt (une image à générer par prompt).
    """
    os.makedirs(output_dir, exist_ok=True)
    for i, prompt in enumerate(prompts, 1):
        base = slugify_filename(prompt, max_len=40)
        filename = os.path.join(output_dir, f"{i:02}_{base}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(prompt)
        print(f"🖼️ Prompt sauvegardé pour génération image : {filename}")

# --------- Voix off ---------

def read_social_text(script_path: str) -> str:
    """
    Lit le Markdown social et retourne un texte lisible pour TTS.
    """
    if not os.path.isfile(script_path):
        return ""
    lines = []
    with open(script_path, encoding="utf-8") as f:
        for line in f:
            # Supprime les markdown headers / puces
            line = re.sub(r"^#{1,6}\\s*", "", line)
            line = re.sub(r"^[-*]\\s*", "", line)
            lines.append(line.strip())
    # Joint, retire les lignes vides multiples
    text = " ".join([l for l in lines if l])
    text = re.sub(r"\\s+", " ", text).strip()
    return text

def generate_voiceover_from_script(script_path: str, out_dir: str, filename: str = "voice.wav", rate: int = 175):
    """
    Génère un fichier audio WAV avec pyttsx3 à partir du script social.
    """
    if pyttsx3 is None:
        print("⚠️ pyttsx3 non installé. Installe avec: pip install pyttsx3")
        return
    text = read_social_text(script_path)
    if not text:
        print("⚠️ Script social introuvable ou vide.")
        return

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, filename)

    engine = pyttsx3.init()
    # Réglages voix (tu peux ajuster selon tes préférences)
    engine.setProperty('rate', rate)         # vitesse
    # engine.setProperty('volume', 1.0)      # volume 0.0 - 1.0
    # Pour changer de voix (si disponible):
    # voices = engine.getProperty('voices')
    # if voices:
    #     engine.setProperty('voice', voices[0].id)  # 0: voix par défaut

    engine.save_to_file(text, out_path)
    engine.runAndWait()
    print(f"🎙️ Voix off générée : {out_path}")

# --------- CLI ---------

def parse_args():
    p = argparse.ArgumentParser(description="FPL Radar — résumés YouTube (sans transcription).")
    p.add_argument("--channel", "-c", help="YouTube channel_id (UC....)")
    p.add_argument("--limit", "-n", type=int, default=DEFAULT_LIMIT, help="Nombre de vidéos à traiter par chaîne")
    p.add_argument("--multi", action="store_true", help="Activer le mode multi-chaînes via channels.txt")
    p.add_argument("--generate-social", action="store_true", help="Générer le script social illustré")
    p.add_argument("--generate-images", action="store_true", help="Générer des images depuis script social")
    p.add_argument("--voiceover", action="store_true", help="Générer une voix off depuis le script social")
    return p.parse_args()

# --------- Traitement ---------

def process_channel(ucid: str, limit: int, date_str: str, output_dir: str, collected: list):
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={ucid}"
    print(f"Flux utilisé : {feed_url}")

    feed = feedparser.parse(feed_url)
    videos = collect_videos(feed)
    print(f"{len(videos)} vidéos trouvées (avant filtre Shorts).")

    videos = [v for v in videos if '/shorts/' not in (v.get('url') or '')]
    print(f"{len(videos)} vidéos après filtre Shorts.")

    collected.extend(videos[:limit])

    with open(os.path.join(output_dir, f"{date_str}.md"), "a", encoding="utf-8") as f:
        f.write(f"# Chaîne {ucid}\n\n")
        for video in videos[:limit]:
            print(f"[{video['published_dt'].strftime('%Y-%m-%d')}] {video['title']}")
            print(f"🔗 {video['url']}")
            summary = generate_summary(video['title'], None)
            print("Résumé :")
            print(summary)
            print("\n" + "-" * 40 + "\n")
            f.write(f"## {video['published_dt'].strftime('%Y-%m-%d')} — {video['title']}\n")
            f.write(f"🔗 {video['url']}\n\n")
            f.write(f"Résumé :\n{summary}\n\n---\n\n")
            time.sleep(PAUSE_S)

# --------- Main ---------

if __name__ == "__main__":
    args = parse_args()
    date_str = datetime.now(UTC).strftime("%Y-%m-%d")
    output_dir = "fpl_summaries"
    os.makedirs(output_dir, exist_ok=True)
    collected_videos = []

    if args.multi:
        if not os.path.isfile(CHANNELS_FILE):
            print(f"Fichier {CHANNELS_FILE} introuvable.")
            exit(1)
        with open(CHANNELS_FILE, encoding="utf-8") as f:
            for line in f:
                ucid = line.strip()
                if ucid and not ucid.startswith("#"):
                    process_channel(ucid, args.limit, date_str, output_dir, collected_videos)
    else:
        ucid = args.channel.strip() if args.channel else DEFAULT_CHANNEL
        process_channel(ucid, args.limit, date_str, output_dir, collected_videos)

    # Génération du script social (markdown)
    if args.generate_social:
        social_path = os.path.join(output_dir, f"social_{date_str}.md")
        with open(social_path, "w", encoding="utf-8") as f:
            f.write(f"# Script social — {date_str}\n\n")
            f.write("Aujourd’hui dans FPL, voici ce qu’il faut retenir en 30 secondes :\n\n")
            f.write("Watchlist Gameweek : des noms ressortent, comme Sarr contre Villa.\n")
            f.write("Free Hit ? Mateta et un premium en attaque, c’est dans toutes les drafts.\n")
            f.write("Tendances du jour : Watchlist, Free Hit, et des choix offensifs à surveiller.\n")
            f.write("Tu veux ce genre de résumé chaque jour ? Pense à t’abonner.\n")
        print(f"📱 Script social généré dans {social_path}")
    else:
        social_path = os.path.join(output_dir, f"social_{date_str}.md")

    # Prompts images -> fichiers .txt
    if args.generate_images:
        prompts = extract_prompts_from_script(social_path)
        image_output_dir = os.path.join("social_images", date_str)
        generate_images_from_prompts(prompts, image_output_dir)

    # Voix off TTS -> WAV
    if args.voiceover:
        audio_dir = os.path.join("social_audio", date_str)
        generate_voiceover_from_script(social_path, audio_dir, filename="voice.wav", rate=175)

    print(f"📁 Résumés écrits dans {output_dir}/{date_str}.md")
