# list_voices.py
# Affiche toutes les voix disponibles avec pyttsx3 (Windows)

import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty("voices")

print("=== Voix disponibles ===")
for i, v in enumerate(voices):
    print(f"[{i}] id={v.id}  name={getattr(v, 'name', '')}  lang={getattr(v, 'languages', '')}")
