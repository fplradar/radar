# tts_openai.py
# Génère une voix off naturelle (accent britannique, voix masculine)
# Entrée : fichier markdown (script social)
# Sortie : fichier MP3 dans social_audio/<date>/

import os, sys, re, requests

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    print("❌ Variable OPENAI_API_KEY manquante.")
    print("   PowerShell : $env:OPENAI_API_KEY = 'sk-...'")
    sys.exit(1)

API_URL = "https://api.openai.com/v1/audio/speech"
MODEL = "gpt-4o-mini-tts"   # modèle TTS
VOICE = "alloy"             # voix (ex: alloy, verse, echo)
FORMAT = "mp3"

def clean_markdown(path: str) -> str:
    if not os.path.isfile(path):
        return ""
    text = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = re.sub(r"^#{1,6}\\s*", "", line)  # en-têtes markdown
            line = re.sub(r"^[-*]\\s*", "", line)    # puces
            line = line.strip()
            if line:
                text.append(line)
    raw = " ".join(text)
    raw = re.sub(r"\\s+", " ", raw).strip()
    return raw

def generate_tts(in_file: str, out_file: str):
    text = clean_markdown(in_file)
    if not text:
        print("❌ Script social vide ou introuvable.")
        return

    # Style: accent britannique, voix masculine, chaleureuse
    style_prompt = (
        "Read this like a warm, natural British male voice. "
        "Conversational tone, flowing speech, no blanks or awkward pauses."
    )
    payload = {
        "model": MODEL,
        "voice": VOICE,
        "input": style_prompt + " " + text,
        "format": FORMAT,
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    print(f"🎙️ Génération TTS avec modèle={MODEL}, voix={VOICE}...")
    r = requests.post(API_URL, headers=headers, json=payload, stream=True)

    if r.status_code != 200:
        print(f"❌ Erreur API {r.status_code}: {r.text}")
        return

    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    print(f"✅ Fichier audio généré : {out_file}")

def main():
    if len(sys.argv) != 3:
        print("Usage: python tts_openai.py <script_social.md> <out_file.mp3>")
        sys.exit(1)
    in_file = sys.argv[1]
    out_file = sys.argv[2]
    generate_tts(in_file, out_file)

if __name__ == "__main__":
    main()
