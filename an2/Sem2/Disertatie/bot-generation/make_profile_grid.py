"""
make_profile_grid.py
--------------------
Reads the BotFarm SQLite database, picks the best available bot for each of
the six personas, and saves a single dissertation-ready PNG grid.

Run from the bot-generation/ folder:
    python make_profile_grid.py

Output:  bot-generation/figures/profile_grid.png   (300 dpi, ~1900 px wide)
LaTeX:   \\includegraphics[width=\\linewidth]{bot-generation/figures/profile_grid}
"""

import sqlite3
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT      = Path(__file__).resolve().parent.parent   # …/Disertatie
BACKEND   = ROOT / "bot-generation" / "webapp" / "backend"
STATIC    = BACKEND / "static"
PIC_DIR   = STATIC / "profile_pics"

# Flask puts the SQLite file in the instance/ sub-folder
DB_PATH   = BACKEND / "instance" / "botfarm.db"
if not DB_PATH.exists():                             # fallback for older setups
    DB_PATH = BACKEND / "botfarm.db"

OUT_DIR   = ROOT / "bot-generation" / "figures"
OUT_FILE  = OUT_DIR / "profile_grid.png"

# ── Visual settings ────────────────────────────────────────────────────────────
PERSONAS = ["general", "political", "sports", "news", "influencer", "conspiracy"]

LABELS = {
    "general":    "General",
    "political":  "Political",
    "sports":     "Sports",
    "news":       "News",
    "influencer": "Influencer",
    "conspiracy": "Conspiracy",
}

ACCENTS = {
    "general":    (99,  102, 241),   # indigo
    "political":  (239, 68,  68),    # red
    "sports":     (34,  197, 94),    # green
    "news":       (234, 179, 8),     # amber
    "influencer": (236, 72,  153),   # pink
    "conspiracy": (139, 92,  246),   # purple
}

FACE_SIZE   = 280    # each circular face thumbnail
LABEL_H     = 56     # space below each face for text
GAP         = 18     # horizontal gap between cells
PAD         = 24     # outer padding
CORNER_R    = 14

BG          = (15,  23,  42)    # slate-900
CARD        = (30,  41,  59)    # slate-800
TEXT_MAIN   = (226, 232, 240)   # slate-200
TEXT_SUB    = (148, 163, 184)   # slate-400


# ── Database helpers ──────────────────────────────────────────────────────────

def load_bots():
    """Return {persona: row_dict} for the first ready bot of each persona."""
    if not DB_PATH.exists():
        print(f"ERROR: database not found.\nLooked at: {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur  = conn.cursor()
    result = {}

    for persona in PERSONAS:
        cur.execute(
            "SELECT id, username, display_name, profile_pic, persona "
            "FROM bots "
            "WHERE persona=? AND pic_status='ready' AND profile_pic IS NOT NULL "
            "ORDER BY id LIMIT 1",
            (persona,),
        )
        row = cur.fetchone()
        if row:
            result[persona] = dict(row)

    conn.close()
    return result


# ── Font loader ───────────────────────────────────────────────────────────────

def load_font(size):
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


# ── Image builder ─────────────────────────────────────────────────────────────

def circle_crop(img: Image.Image, size: int) -> Image.Image:
    """Resize *img* to *size* × *size* and apply a circular mask."""
    img  = img.convert("RGBA").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    out  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, mask=mask)
    return out


def placeholder_face(size: int, accent: tuple) -> Image.Image:
    """Solid-colour circle — used when no image is on disk."""
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((0, 0, size, size), fill=(*accent, 255))
    return img


def build_grid(bots: dict) -> Image.Image:
    n      = len(PERSONAS)
    cell_w = FACE_SIZE + PAD * 2
    cell_h = FACE_SIZE + LABEL_H + PAD * 2 + 6   # +6 for accent bar
    total_w = PAD + n * cell_w + (n - 1) * GAP + PAD
    total_h = PAD + cell_h + PAD

    canvas = Image.new("RGB", (total_w, total_h), BG)
    draw   = ImageDraw.Draw(canvas)

    font_label = load_font(17)
    font_name  = load_font(13)

    for i, persona in enumerate(PERSONAS):
        # ── card position ──
        x0 = PAD + i * (cell_w + GAP)
        y0 = PAD
        x1 = x0 + cell_w
        y1 = y0 + cell_h
        accent = ACCENTS[persona]

        # rounded card background
        draw.rounded_rectangle([x0, y0, x1, y1], radius=CORNER_R, fill=CARD)

        # ── face image ──
        face_x = x0 + PAD
        face_y = y0 + PAD
        bot    = bots.get(persona)

        face_img = None
        if bot:
            pic_path = PIC_DIR / bot["profile_pic"]
            if pic_path.exists():
                try:
                    face_img = circle_crop(Image.open(pic_path), FACE_SIZE)
                except Exception as exc:
                    print(f"  WARNING: could not open {pic_path}: {exc}")

        if face_img is None:
            face_img = placeholder_face(FACE_SIZE, accent)

        canvas.paste(face_img, (face_x, face_y), mask=face_img.split()[3])

        # ── accent bar under face ──
        bar_y = face_y + FACE_SIZE + 4
        draw.rectangle([x0 + PAD, bar_y, x1 - PAD, bar_y + 4], fill=accent)

        # ── persona label ──
        label    = LABELS[persona]
        lbbox    = draw.textbbox((0, 0), label, font=font_label)
        lw       = lbbox[2] - lbbox[0]
        draw.text(
            (x0 + (cell_w - lw) // 2, bar_y + 8),
            label, fill=TEXT_MAIN, font=font_label,
        )

        # ── bot display name ──
        if bot:
            name  = bot["display_name"]
            nbbox = draw.textbbox((0, 0), name, font=font_name)
            nw    = nbbox[2] - nbbox[0]
            # truncate if too wide
            while nw > cell_w - 8 and len(name) > 4:
                name  = name[:-1]
                nbbox = draw.textbbox((0, 0), name + "…", font=font_name)
                nw    = nbbox[2] - nbbox[0]
            if name != bot["display_name"]:
                name += "…"
            draw.text(
                (x0 + (cell_w - nw) // 2, bar_y + 29),
                name, fill=TEXT_SUB, font=font_name,
            )

    return canvas


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  BotFarm — Profile Grid Generator")
    print("=" * 55)

    print(f"\nDatabase : {DB_PATH}")
    print(f"Pics dir : {PIC_DIR}")

    bots = load_bots()
    print("\nBots found per persona:")
    for p in PERSONAS:
        b = bots.get(p)
        if b:
            pic_ok = (PIC_DIR / b["profile_pic"]).exists()
            print(f"  {p:12s}  @{b['username']:<20s}  {'✓ image on disk' if pic_ok else '⚠ image missing — placeholder'}")
        else:
            print(f"  {p:12s}  NOT FOUND — generate a {p}-persona bot first")

    ready = sum(1 for p in PERSONAS if bots.get(p))
    if ready == 0:
        print("\nERROR: no bots in database. Generate at least one bot per persona first.")
        sys.exit(1)
    if ready < len(PERSONAS):
        print(f"\n⚠  Only {ready}/{len(PERSONAS)} personas have bots. Missing ones will show as coloured placeholders.")
    else:
        print("\nAll 6 personas ready.")

    print("\nBuilding grid…")
    grid = build_grid(bots)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    grid.save(OUT_FILE, dpi=(300, 300))
    print(f"\nSaved  →  {OUT_FILE}")
    print(f"Size      {grid.width} × {grid.height} px  (300 dpi)")
    print()
    print("Use in LaTeX:")
    print(r"  \includegraphics[width=\linewidth]{bot-generation/figures/profile_grid}")


if __name__ == "__main__":
    main()
