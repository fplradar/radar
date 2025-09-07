# tts_pyttsx3.py
# Génère une voix off locale avec pyttsx3
# - Sélection auto : priorité EN-GB (UK), sinon EN-US David, sinon défaut
# - Possibilité de FORCER la voix via 3e argument :
#     * index numérique (ex: 3)
#     * ID/nom partiel (ex: "Hazel" ou l'ID complet du registre)

import os, sys, re, pyttsx3

def clean_markdown(path: str) -> str:
    if not os.path.isfile(path):
        return ""
    lines = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = re.sub(r"^#{1,6}\s*", "", line)  # supprime titres markdown
            line = re.sub(r"^[-*]\s*", "", line)    # supprime puces
            line = line.strip()
            if line:
                lines.append(line)
    text = " ".join(lines)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def list_voices(engine):
    return engine.getProperty("voices")

def choose_voice_auto(voices):
    # 1) Toute voix en-GB (UK)
    for v in voices:
        meta = f"{getattr(v,'id','')}|{getattr(v,'name','')}|{getattr(v,'languages','')}"
        if "en-GB" in meta or "English (Great Britain)" in meta:
            return v.id
    # 2) Microsoft David (EN-US masculin)
    for v in voices:
        if "David" in f"{getattr(v,'id','')}{getattr(v,'name','')}":
            return v.id
    # 3) défaut
    return None

def choose_voice_forced(voices, selector: str):
    # selector = index numérique OU sous-chaîne (id/name)
    if selector is None:
        return None
    selector = selector.strip()
    # Numérique ?
    if selector.isdigit():
        idx = int(selector)
        if 0 <= idx < len(voices):
            return voices[idx].id
        return None
    # Sinon recherche par sous-chaîne (case-insensitive) dans id ou name
    s = selector.lower()
    for v in voices:
        if s in str(getattr(v, "id", "")).lower() or s in str(getattr(v, "name", "")).lower():
            return v.id
    return None

def generate_tts(in_file: str, out_file: str, voice_selector: str | None = None, rate: int = 175):
    text = clean_markdown(in_file)
    if not text:
        print("❌ Script social vide ou introuvable.")
        return

    os.makedirs(os.path.dirname(out_file), exist_ok=True)

    engine = pyttsx3.init()
    engine.setProperty("rate", rate)

    voices = list_voices(engine)

    # Essai 1 : voix forcée si fournie
    voice_id = choose_voice_forced(voices, voice_selector)
    # Essai 2 : auto
    if not voice_id:
        voice_id = choose_voice_auto(voices)

    if voice_id:
        engine.setProperty("voice", voice_id)
        print(f"🎙️ Voix sélectionnée : {voice_id}")
    else:
        print("⚠️ Aucune voix spécifique trouvée, utilisation de la voix par défaut.")

    engine.save_to_file(text, out_file)
    engine.runAndWait()
    print(f"✅ Fichier audio généré : {out_file}")

def main():
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python tts_pyttsx3.py <script_social.md> <out_file.wav> [voice_selector]")
        print("Exemples de voice_selector :")
        print("  3                       (index numérique)")
        print("  Hazel                   (nom/ID partiel)")
        print("  HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-GB_HAZEL_11.0")
        sys.exit(1)

    in_file = sys.argv[1]
    out_file = sys.argv[2]
    voice_selector = sys.argv[3] if len(sys.argv) == 4 else None
    generate_tts(in_file, out_file, voice_selector)

if __name__ == "__main__":
    main()
