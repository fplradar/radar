# render_images.py
# Rend des images depuis les prompts .txt de social_images/<date> via OpenAI Images API
import os, sys, time, json, base64, glob
from datetime import datetime

# --- Dépendances ---
try:
    import requests
except ImportError:
    print("⚠️ Module 'requests' manquant. Installe d'abord : pip install requests")
    sys.exit(1)

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    print("❌ OPENAI_API_KEY manquant dans l'environnement.")
    print("   PowerShell (session): $env:OPENAI_API_KEY = 'sk-...'")
    sys.exit(1)

MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
SIZE = os.getenv("OPENAI_IMAGE_SIZE", "1024x1024")  # 512x512, 1024x1024, 2048x2048
API_URL = "https://api.openai.com/v1/images/generations"

ROOT = os.getcwd()  # doit être C:\\Users\\admin\\Documents\\radar
IN_ROOT = os.path.join(ROOT, "social_images")
OUT_ROOT = os.path.join(ROOT, "social_images_out")

def newest_date_dir(root):
    """Retourne le sous-dossier (YYYY-MM-DD) le plus récent dans root, sinon None."""
    dates = []
    for p in glob.glob(os.path.join(root, "*")):
        if os.path.isdir(p):
            base = os.path.basename(p)
            try:
                # tente de parser YYYY-MM-DD
                datetime.strptime(base, "%Y-%m-%d")
                dates.append(base)
            except ValueError:
                pass
    return max(dates) if dates else None

def list_prompt_files(in_dir):
    files = sorted(glob.glob(os.path.join(in_dir, "*.txt")))
    return files

def call_openai_image(prompt, retries=3, delay=2):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "size": SIZE,
    }
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            r = requests.post(API_URL, headers=headers, data=json.dumps(payload), timeout=60)
            if r.status_code == 200:
                return r.json()
            else:
                # tente de lire l'erreur JSON
                try:
                    err = r.json()
                except Exception:
                    err = r.text
                print(f"❗ API error (try {attempt}/{retries}): {r.status_code} -> {err}")
                last_err = err
        except Exception as e:
            print(f"❗ Exception (try {attempt}/{retries}): {e}")
            last_err = str(e)
        time.sleep(delay * attempt)
    raise RuntimeError(f"Echec API après {retries} tentatives: {last_err}")

def b64_to_png(b64, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(b64))

def main():
    # Permet de forcer une date: python render_images.py 2025-09-06
    forced_date = sys.argv[1] if len(sys.argv) > 1 else None
    in_date = forced_date or newest_date_dir(IN_ROOT)
    if not in_date:
        print(f"❌ Aucun dossier date trouvé dans {IN_ROOT}")
        sys.exit(1)

    in_dir = os.path.join(IN_ROOT, in_date)
    out_dir = os.path.join(OUT_ROOT, in_date)
    files = list_prompt_files(in_dir)
    if not files:
        print(f"❌ Aucun .txt trouvé dans {in_dir}")
        sys.exit(1)

    print(f"📥 Dossier prompts : {in_dir}")
    print(f"📤 Dossier sortie  : {out_dir}")
    print(f"🖼️ Modèle={MODEL}  Taille={SIZE}")
    print(f"🔑 API key: OK\n")

    for idx, path in enumerate(files, 1):
        base = os.path.splitext(os.path.basename(path))[0]
        with open(path, "r", encoding="utf-8") as f:
            prompt = f.read().strip()
        if not prompt:
            print(f"- {base}: prompt vide, saut.")
            continue

        print(f"- [{idx}/{len(files)}] Génère: {base} ...", end="", flush=True)
        try:
            data = call_openai_image(prompt)
            b64 = data["data"][0]["b64_json"]
            out_path = os.path.join(out_dir, f"{idx:02}_{base}.png")
            b64_to_png(b64, out_path)
            print(f" OK -> {out_path}")
            time.sleep(0.5)  # petite pause
        except Exception as e:
            print(f" ÉCHEC: {e}")

    print("\n✅ Terminé.")

if __name__ == "__main__":
    main()
