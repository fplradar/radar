# tts_pyttsx3.py
# Génère une voix off locale avec pyttsx3
# Amélioré : paramètres rate, volume, gentle pauses

import os, sys, re, pyttsx3

def clean_markdown(path: str, gentle: bool = False) -> str:
    if not os.path.isfile(path):
        return ""
    lines = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = re.sub(r"^#{1,6}\s*", "", line)  # titres markdown
            line = re.sub(r"^[-*]\s*", "", line)    # puces
            line = line.strip()
            if line:
                if gentle:
                    # Ajoute une petite pause après chaque ligne
                    lines.append(line + ". ")
                else:
                    lines.append(line)
    text = " ".join(lines)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def list_voices(engine):
    return engine.getProperty("voices")

def choose_voice_auto(voices):
    # 1) Cherche voix UK
    for v in voices:
        meta = f"{getattr(v,'id','')}|{getattr(v,'name','')}|{getattr(v,'languages','')}"
        if "en-GB" in meta or "English (Great Britain)" in meta:
            return v.id
    # 2) Cherche David (EN-US masculin)
    for v in voices:
        if "David" in f"{getattr(v,'id','')}{getattr(v,'name','')}":
            return v.id
    return None

def choose_voice_forced(voices, selector: str):
    if not selector:
        return None
    selector = selector.strip()
    if selector.isdigit():
        idx = int(selector)
        if 0 <= idx < len(voices):
            return voices[idx].id
        return None
    s = selector.lower()
    for v in voices:
        if s in str(getattr(v,"id","")).lower() or s in str(getattr(v,"name","")).lower():
            return v.id
    return None

def generate_tts(in_file: str, out_file: str,
                 voice_selector: str | None = None,
                 rate: int = 150, volume: float = 1.0,
                 gentle: bool = True):
    text = clean_markdown(in_file, gentle=gentle)
    if not text:
        print("❌ Script social vide ou introuvable.")
        return

    os.makedirs(os.path.dirname(out_file), exist_ok=True)

    engine = pyttsx3.init()
    engine.setProperty("rate", rate)
    engine.setProperty("volume", volume)

    voices = list_voices(engine)

    # Sélection voix forcée ou auto
    voice_id = choose_voice_forced(voices, voice_selector)
    if not voice_id:
        voice_id = choose_voice_auto(voices)

    if voice_id:
        engine.setProperty("voice", voice_id)
        print(f"🎙️ Voix sélectionnée : {voice_id}")
    else:
        print("⚠️ Aucune voix spécifique trouvée, utilisation par défaut.")

    engine.save_to_file(text, out_file)
    engine.runAndWait()
    print(f"✅ Fichier audio généré : {out_file}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python tts_pyttsx3.py <script_social.md> <out_file.wav> [voice_selector] [rate] [volume] [gentle]")
        sys.exit(1)

    in_file = sys.argv[1]
    out_file = sys.argv[2]
    voice_selector = sys.argv[3] if len(sys.argv) >= 4 else None
    rate = int(sys.argv[4]) if len(sys.argv) >= 5 else 150
    volume = float(sys.argv[5]) if len(sys.argv) >= 6 else 1.0
    gentle = (len(sys.argv) >= 7 and sys.argv[6].lower() in ["1","true","yes","gentle"])

    generate_tts(in_file, out_file, voice_selector, rate, volume, gentle)

if __name__ == "__main__":
    main()
