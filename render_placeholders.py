# render_placeholders.py
# Génère des images placeholders (PNG) depuis les prompts .txt
# Entrée : social_images/<DATE>/*.txt
# Sortie : social_images_out/<DATE>/*.png

import os, sys, glob
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

ROOT = os.getcwd()  # C:\Users\admin\Documents\radar
IN_ROOT = os.path.join(ROOT, "social_images")
OUT_ROOT = os.path.join(ROOT, "social_images_out")

W, H = 1024, 1024
MARGIN = 60

def newest_date_dir(root):
    dates = []
    for p in glob.glob(os.path.join(root, "*")):
        if os.path.isdir(p):
            base = os.path.basename(p)
            try:
                datetime.strptime(base, "%Y-%m-%d")
                dates.append(base)
            except ValueError:
                pass
    return max(dates) if dates else None

def load_font(size=44):
    # Tente une police TrueType courante, sinon fallback bitmap
    candidates = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/calibri.ttf",
    ]
    for path in candidates:
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                pass
    return ImageFont.load_default()

# --- Utils compatibles Pillow 11 ---
def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    # draw.textbbox((0,0), ...) -> (l, t, r, b)
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    return r - l

def line_height(font: ImageFont.FreeTypeFont) -> int:
    # getbbox renvoie (l,t,r,b) de la boîte; hauteur = b - t
    l, t, r, b = font.getbbox("Ay")
    return b - t

def wrap_text(text, draw, font, max_width):
    # Coupe en lignes qui tiennent dans max_width (en pixels)
    words = text.split()
    lines = []
    cur = []
    for w in words:
        test = " ".join(cur + [w])
        if text_width(draw, test, font) <= max_width:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    # Si pas de mots (texte vide), renvoyer une ligne par défaut
    return lines or [""]

def background(idx):
    # Quelques palettes (gradient vertical simple)
    palettes = [
        ((30, 30, 60), (90, 40, 120)),
        ((10, 60, 120), (10, 140, 200)),
        ((20, 120, 80), (40, 200, 160)),
        ((120, 40, 40), (220, 80, 80)),
        ((100, 100, 100), (40, 40, 40)),
    ]
    a, b = palettes[idx % len(palettes)]
    img = Image.new("RGB", (W, H), a)
    # Gradient vertical pixel par pixel (suffisant pour quelques images)
    for y in range(H):
        ratio = y / (H - 1)
        r = int(a[0] * (1 - ratio) + b[0] * ratio)
        g = int(a[1] * (1 - ratio) + b[1] * ratio)
        bl = int(a[2] * (1 - ratio) + b[2] * ratio)
        for x in range(W):
            img.putpixel((x, y), (r, g, bl))
    return img

def main():
    forced_date = sys.argv[1] if len(sys.argv) > 1 else None
    in_date = forced_date or newest_date_dir(IN_ROOT)
    if not in_date:
        print(f"❌ Aucun dossier date trouvé dans {IN_ROOT}")
        sys.exit(1)

    in_dir = os.path.join(IN_ROOT, in_date)
    out_dir = os.path.join(OUT_ROOT, in_date)
    files = sorted(glob.glob(os.path.join(in_dir, "*.txt")))
    if not files:
        print(f"❌ Aucun .txt trouvé dans {in_dir}")
        sys.exit(1)

    os.makedirs(out_dir, exist_ok=True)
    print(f"📥 Dossier prompts : {in_dir}")
    print(f"📤 Dossier sortie  : {out_dir}")

    font_title = load_font(64)
    font_body = load_font(44)

    for i, path in enumerate(files, 1):
        base = os.path.splitext(os.path.basename(path))[0]
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = (f.read() or "").strip()

        img = background(i)
        draw = ImageDraw.Draw(img)

        # Titre court : 6-8 mots
        words = text.replace("\n", " ").split()
        title = " ".join(words[:8]) if words else "FPL"
        # Corps : ~250 caractères
        body = text[:250] if text else "Résumé visuel généré hors-API."

        max_w = W - 2 * MARGIN

        title_lines = wrap_text(title, draw, font_title, max_w)
        body_lines  = wrap_text(body,  draw, font_body,  max_w)

        line_h_title = line_height(font_title)
        line_h_body  = line_height(font_body)
        spacing_title = 12
        spacing_body  = 8

        h_title = len(title_lines) * line_h_title + (len(title_lines) - 1) * spacing_title
        h_body  = len(body_lines)  * line_h_body  + (len(body_lines)  - 1) * spacing_body
        total_h = h_title + 24 + h_body

        y = (H - total_h) // 2

        def draw_centered(lines, font, y0, line_h, spacing, fill=(255,255,255)):
            for line in lines:
                w_px = text_width(draw, line, font)
                x = (W - w_px) // 2
                # ombre
                draw.text((x+2, y0+2), line, font=font, fill=(0,0,0))
                # texte
                draw.text((x, y0), line, font=font, fill=fill)
                y0 += line_h + spacing
            return y0

        y = draw_centered(title_lines, font_title, y, line_h_title, spacing_title, fill=(255,255,255))
        y += 24
        draw_centered(body_lines, font_body, y, line_h_body, spacing_body, fill=(240,240,240))

        out_path = os.path.join(out_dir, f"{i:02}_{base}.png")
        img.save(out_path, "PNG")
        print(f"✅ {out_path}")

    print("✅ Terminé.")

if __name__ == "__main__":
    main()
