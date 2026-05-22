"""
Generates the PowerPoint presentation for the paper:
"The Evolution of Automated Fake News Detection"

Run:  python build_presentation.py
Output: presentation.pptx
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import json, os

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
DARK_BLUE   = RGBColor(0x1A, 0x3A, 0x5C)   # slide background accent
MID_BLUE    = RGBColor(0x27, 0x6F, 0xBF)   # headings
ACCENT      = RGBColor(0xE8, 0x7C, 0x1E)   # highlights / numbers
LIGHT_GREY  = RGBColor(0xF2, 0xF4, 0xF7)   # content background
WHITE       = RGBColor(0xFF, 0xFF, 0xFF)
DARK_TEXT   = RGBColor(0x1E, 0x1E, 0x2E)
GREEN       = RGBColor(0x27, 0xAE, 0x60)
RED         = RGBColor(0xC0, 0x39, 0x2B)

SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)

prs = Presentation()
prs.slide_width  = SLIDE_W
prs.slide_height = SLIDE_H

BLANK = prs.slide_layouts[6]   # completely blank layout

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def add_rect(slide, l, t, w, h, fill_rgb=None, line_rgb=None, line_pt=0):
    shape = slide.shapes.add_shape(1, Inches(l), Inches(t), Inches(w), Inches(h))
    shape.line.fill.background()
    if fill_rgb:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_rgb
    else:
        shape.fill.background()
    if line_rgb and line_pt:
        shape.line.color.rgb = line_rgb
        shape.line.width = Pt(line_pt)
    else:
        shape.line.fill.background()
    return shape


def add_text(slide, text, l, t, w, h,
             font_size=18, bold=False, color=DARK_TEXT,
             align=PP_ALIGN.LEFT, italic=False, wrap=True):
    txb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf  = txb.text_frame
    tf.word_wrap = wrap
    p   = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size  = Pt(font_size)
    run.font.bold  = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return txb


def add_image(slide, path, l, t, w, h=None):
    if not os.path.exists(path):
        return
    if h:
        slide.shapes.add_picture(path, Inches(l), Inches(t), Inches(w), Inches(h))
    else:
        slide.shapes.add_picture(path, Inches(l), Inches(t), Inches(w))


def header_bar(slide, title_text, subtitle_text=""):
    """Dark top bar with slide title."""
    add_rect(slide, 0, 0, 13.33, 1.35, fill_rgb=DARK_BLUE)
    add_text(slide, title_text,
             0.4, 0.12, 11.5, 0.75,
             font_size=28, bold=True, color=WHITE, align=PP_ALIGN.LEFT)
    if subtitle_text:
        add_text(slide, subtitle_text,
                 0.4, 0.85, 11.5, 0.45,
                 font_size=14, color=RGBColor(0xAA, 0xCC, 0xEE),
                 italic=True, align=PP_ALIGN.LEFT)


def bullet_box(slide, items, l, t, w, h,
               font_size=17, bullet="▸ ", color=DARK_TEXT, spacing=0.06):
    """Render a list of strings as bullet points."""
    for i, item in enumerate(items):
        add_text(slide, bullet + item,
                 l, t + i * spacing * (font_size / 14),
                 w, spacing * (font_size / 14) + 0.1,
                 font_size=font_size, color=color)


def metric_box(slide, label, value, l, t, w=2.2, h=1.1,
               val_color=GREEN, bg=LIGHT_GREY):
    """Small KPI card."""
    add_rect(slide, l, t, w, h, fill_rgb=bg,
             line_rgb=MID_BLUE, line_pt=1)
    add_text(slide, label, l+0.1, t+0.06, w-0.2, 0.38,
             font_size=13, color=DARK_TEXT, align=PP_ALIGN.CENTER)
    add_text(slide, value, l+0.1, t+0.42, w-0.2, 0.55,
             font_size=22, bold=True, color=val_color, align=PP_ALIGN.CENTER)


# ===========================================================================
# SLIDE 1 — Title
# ===========================================================================
slide = prs.slides.add_slide(BLANK)

add_rect(slide, 0, 0, 13.33, 7.5, fill_rgb=DARK_BLUE)
add_rect(slide, 0, 2.7, 13.33, 2.3, fill_rgb=MID_BLUE)

add_text(slide,
         "The Evolution of Automated",
         0.8, 1.5, 11.7, 0.85,
         font_size=36, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
add_text(slide,
         "Fake News Detection",
         0.8, 2.25, 11.7, 0.75,
         font_size=36, bold=True, color=RGBColor(0xFF, 0xD7, 0x00),
         align=PP_ALIGN.CENTER)

add_text(slide,
         "From TF-IDF Baselines to Bidirectional LSTMs and BERT",
         0.8, 2.88, 11.7, 0.55,
         font_size=17, italic=True, color=WHITE, align=PP_ALIGN.CENTER)

add_text(slide, "Author:  Tudor [Surname]",
         1.5, 4.55, 5.5, 0.45,
         font_size=15, color=RGBColor(0xCC, 0xDD, 0xFF), align=PP_ALIGN.LEFT)
add_text(slide, "Coordinator:  Lect. Dr. Alina-Delia Călin",
         1.5, 5.05, 8.0, 0.45,
         font_size=15, color=RGBColor(0xCC, 0xDD, 0xFF), align=PP_ALIGN.LEFT)
add_text(slide,
         "Master's Programme — High Performance Computing and Big Data Analytics",
         1.5, 5.55, 10.0, 0.45,
         font_size=13, italic=True, color=RGBColor(0xAA, 0xBB, 0xDD),
         align=PP_ALIGN.LEFT)
add_text(slide, "2026", 0.8, 6.8, 11.7, 0.4,
         font_size=13, color=RGBColor(0x88, 0xAA, 0xCC), align=PP_ALIGN.CENTER)


# ===========================================================================
# SLIDE 2 — Motivation & Problem
# ===========================================================================
slide = prs.slides.add_slide(BLANK)
add_rect(slide, 0, 0, 13.33, 7.5, fill_rgb=WHITE)
header_bar(slide, "Why Does This Matter?", "The fake news problem at scale")

add_rect(slide, 0.4, 1.55, 5.9, 5.6, fill_rgb=LIGHT_GREY,
         line_rgb=MID_BLUE, line_pt=1)
add_rect(slide, 6.9, 1.55, 6.0, 5.6, fill_rgb=LIGHT_GREY,
         line_rgb=ACCENT, line_pt=1)

add_text(slide, "The Problem", 0.6, 1.65, 5.5, 0.45,
         font_size=16, bold=True, color=MID_BLUE)
facts = [
    "Misinformation spreads 6× faster than true news on social media",
    "2016 US election: fake stories outpaced real news in Facebook engagement",
    "Public health crises amplified by vaccine and pandemic misinformation",
    "Manual fact-checking cannot scale to millions of posts per day",
    "Automated detection is no longer optional — it is essential",
]
for i, f in enumerate(facts):
    add_text(slide, "▸  " + f, 0.6, 2.25 + i*0.88, 5.6, 0.78,
             font_size=14, color=DARK_TEXT)

add_text(slide, "Our Approach", 7.1, 1.65, 5.6, 0.45,
         font_size=16, bold=True, color=ACCENT)
approach = [
    "Systematically compare three generations of NLP methods",
    "Shared benchmark: ISOT Fake News Dataset (~45 000 articles)",
    "Fair evaluation under identical preprocessing conditions",
    "Document the accuracy vs. complexity trade-off",
]
for i, a in enumerate(approach):
    add_text(slide, "▸  " + a, 7.1, 2.25 + i*0.98, 5.7, 0.85,
             font_size=14, color=DARK_TEXT)

add_rect(slide, 6.9, 5.7, 6.0, 1.25, fill_rgb=DARK_BLUE)
add_text(slide,
         "Classical ML  →  Deep RNN / LSTM  →  BERT",
         7.0, 5.85, 5.8, 0.9,
         font_size=17, bold=True, color=WHITE, align=PP_ALIGN.CENTER)


# ===========================================================================
# SLIDE 3 — Dataset
# ===========================================================================
slide = prs.slides.add_slide(BLANK)
add_rect(slide, 0, 0, 13.33, 7.5, fill_rgb=WHITE)
header_bar(slide, "Dataset: ISOT Fake News Corpus",
           "University of Victoria — publicly available on Kaggle")

add_image(slide, 'figures/fig_class_dist.png', 0.35, 1.5, 4.8)

add_rect(slide, 5.5, 1.55, 7.5, 2.5, fill_rgb=LIGHT_GREY,
         line_rgb=MID_BLUE, line_pt=1)
add_text(slide, "Dataset at a Glance", 5.7, 1.65, 7.1, 0.42,
         font_size=16, bold=True, color=MID_BLUE)
stats = [
    "44 898 labelled news articles",
    "21 417 real articles  (Reuters, 2015–2018)",
    "23 481 fake articles  (Politifact-flagged sources)",
    "Fields: title, text, subject, date",
    "Near-balanced classes → no imbalance bias",
]
for i, s in enumerate(stats):
    add_text(slide, "▸  " + s, 5.7, 2.2 + i*0.47, 7.1, 0.42,
             font_size=14, color=DARK_TEXT)

add_rect(slide, 5.5, 4.2, 7.5, 2.9, fill_rgb=LIGHT_GREY,
         line_rgb=ACCENT, line_pt=1)
add_text(slide, "Preprocessing Pipeline", 5.7, 4.3, 7.1, 0.42,
         font_size=16, bold=True, color=ACCENT)
steps = [
    "Lowercase  →  Remove URLs",
    "Strip non-alphabetic characters  →  Collapse whitespace",
    "NLTK stopword removal (classical ML only)",
    "Vocabulary capped at 15 000 tokens (deep models)",
    "Sequences truncated / padded to 150 tokens",
]
for i, s in enumerate(steps):
    add_text(slide, "▸  " + s, 5.7, 4.78 + i*0.47, 7.1, 0.42,
             font_size=14, color=DARK_TEXT)


# ===========================================================================
# SLIDE 4 — Models Overview
# ===========================================================================
slide = prs.slides.add_slide(BLANK)
add_rect(slide, 0, 0, 13.33, 7.5, fill_rgb=WHITE)
header_bar(slide, "Three Generations of Detection Methods", "")

boxes = [
    (0.35,  "Generation 1\nClassical ML",
     ["TF-IDF bag-of-words features", "Naive Bayes", "Logistic Regression",
      "Random Forest (100 trees)", "Full 36k training set"],
     LIGHT_GREY, MID_BLUE),
    (4.75,  "Generation 2\nDeep Recurrent",
     ["Learned word embeddings", "Vanilla RNN (vanishing ∇)",
      "Bidirectional LSTM (gates)", "500-sample quick-mode run",
      "PyTorch from scratch"],
     LIGHT_GREY, ACCENT),
    (9.15,  "Generation 3\nBERT Transformer",
     ["Pre-trained on 3.3B words", "Self-attention (full context)",
      "WordPiece tokenisation", "110M parameters fine-tuned",
      "Test Accuracy: 99.87% ✓"],
     LIGHT_GREY, RGBColor(0x8E, 0x44, 0xAD)),
]

for (lx, title, items, bg, hdr_color) in boxes:
    add_rect(slide, lx, 1.5, 4.1, 5.65, fill_rgb=bg,
             line_rgb=hdr_color, line_pt=2)
    add_rect(slide, lx, 1.5, 4.1, 0.75, fill_rgb=hdr_color)
    add_text(slide, title, lx+0.1, 1.55, 3.9, 0.65,
             font_size=15, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    for i, item in enumerate(items):
        add_text(slide, "▸  " + item, lx+0.15, 2.4 + i*0.84, 3.8, 0.75,
                 font_size=13, color=DARK_TEXT)

add_text(slide, "All models evaluated on the same 4 489-sample stratified test set",
         0.5, 7.1, 12.3, 0.38,
         font_size=13, italic=True, color=RGBColor(0x66, 0x77, 0x88),
         align=PP_ALIGN.CENTER)


# ===========================================================================
# SLIDE 5 — Classical ML Results
# ===========================================================================
slide = prs.slides.add_slide(BLANK)
add_rect(slide, 0, 0, 13.33, 7.5, fill_rgb=WHITE)
header_bar(slide, "Classical ML Results", "TF-IDF + Sklearn, 8 980-sample test set")

add_image(slide, 'figures/fig_classical_comparison.png', 0.35, 1.5, 7.6)

add_rect(slide, 8.2, 1.55, 4.8, 5.6, fill_rgb=LIGHT_GREY,
         line_rgb=MID_BLUE, line_pt=1)
add_text(slide, "Key Numbers", 8.4, 1.65, 4.4, 0.42,
         font_size=16, bold=True, color=MID_BLUE)

metric_box(slide, "Naive Bayes Acc.",  "94.0 %",  8.35, 2.2,  w=2.1, val_color=RED)
metric_box(slide, "Log. Regression",  "99.1 %",  10.6, 2.2,  w=2.1, val_color=GREEN)
metric_box(slide, "Random Forest",    "99.8 %",  8.35, 3.5,  w=2.1, val_color=GREEN)
metric_box(slide, "RF mis-classified","15 / 8 980", 10.6, 3.5, w=2.1,
           val_color=MID_BLUE)

add_rect(slide, 8.2, 4.75, 4.8, 2.3, fill_rgb=DARK_BLUE)
add_text(slide, "Takeaway", 8.4, 4.82, 4.4, 0.38,
         font_size=14, bold=True, color=ACCENT)
note = ("Strong stylistic signals in the ISOT corpus let even "
        "a bag-of-words model exceed 94 %. Random Forest is near-perfect "
        "at 99.8 % — but has zero understanding of language semantics.")
add_text(slide, note, 8.4, 5.25, 4.4, 1.7,
         font_size=12, color=WHITE)


# ===========================================================================
# SLIDE 6 — RNN Theory + Results
# ===========================================================================
slide = prs.slides.add_slide(BLANK)
add_rect(slide, 0, 0, 13.33, 7.5, fill_rgb=WHITE)
header_bar(slide, "Vanilla RNN — Architecture & Results",
           "2 000 training samples · 5 epochs · CPU quick mode")

add_rect(slide, 0.35, 1.55, 6.3, 2.55, fill_rgb=LIGHT_GREY,
         line_rgb=MID_BLUE, line_pt=1)
add_text(slide, "How it works", 0.55, 1.65, 6.0, 0.42,
         font_size=15, bold=True, color=MID_BLUE)
add_text(slide,
         "hₜ  =  tanh( Wₕₕ · hₜ₋₁  +  Wₓₕ · xₜ  +  b )",
         0.55, 2.18, 6.0, 0.55,
         font_size=15, bold=True, color=DARK_BLUE, align=PP_ALIGN.CENTER)
rnn_points = [
    "Processes tokens one at a time, left → right",
    "Hidden state carries memory of the whole prefix",
    "Vanishing gradients  →  forgets early tokens",
    "Pipeline: Embedding → RNN → Dropout → Linear",
]
for i, p in enumerate(rnn_points):
    add_text(slide, "▸  " + p, 0.55, 2.88 + i*0.44, 6.0, 0.40,
             font_size=13, color=DARK_TEXT)

add_image(slide, 'figures/fig_rnn_training.png', 0.35, 4.2, 8.5)

add_rect(slide, 9.1, 1.55, 3.9, 5.6, fill_rgb=LIGHT_GREY,
         line_rgb=RED, line_pt=2)
add_text(slide, "Test Results", 9.3, 1.65, 3.5, 0.42,
         font_size=15, bold=True, color=RED)
metric_box(slide, "Accuracy", "70.3 %", 9.2, 2.2,  w=3.5, val_color=RED, bg=WHITE)
metric_box(slide, "F1 Macro", "0.702",  9.2, 3.45, w=3.5, val_color=RED, bg=WHITE)

add_text(slide,
         "Low accuracy expected:\n"
         "• Only 2 000 training samples\n"
         "• Vanishing gradients on ~150-token sequences\n"
         "• Fluctuating loss curve confirms instability",
         9.3, 4.7, 3.6, 2.3, font_size=12, color=DARK_TEXT)


# ===========================================================================
# SLIDE 7 — Bi-LSTM Theory + Results
# ===========================================================================
slide = prs.slides.add_slide(BLANK)
add_rect(slide, 0, 0, 13.33, 7.5, fill_rgb=WHITE)
header_bar(slide, "Bidirectional LSTM — Architecture & Results",
           "2 000 training samples · 5 epochs · CPU quick mode")

add_rect(slide, 0.35, 1.55, 6.3, 3.1, fill_rgb=LIGHT_GREY,
         line_rgb=MID_BLUE, line_pt=1)
add_text(slide, "LSTM Gates  (solving vanishing gradients)", 0.55, 1.65, 6.0, 0.42,
         font_size=14, bold=True, color=MID_BLUE)

gate_rows = [
    ("Forget", "fₜ = σ(Wf · [hₜ₋₁, xₜ])", "What to erase from memory"),
    ("Input",  "iₜ = σ(Wᵢ · [hₜ₋₁, xₜ])", "What new info to write"),
    ("Output", "oₜ = σ(Wₒ · [hₜ₋₁, xₜ])", "What to expose as hₜ"),
]
for i, (name, eq, desc) in enumerate(gate_rows):
    y = 2.2 + i * 0.67
    add_rect(slide, 0.45, y, 1.1, 0.5, fill_rgb=MID_BLUE)
    add_text(slide, name, 0.47, y+0.06, 1.06, 0.38,
             font_size=12, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, eq,   1.65, y+0.06, 2.8, 0.38,
             font_size=12, bold=True, color=DARK_BLUE)
    add_text(slide, desc, 4.5,  y+0.06, 2.1, 0.38,
             font_size=11, italic=True, color=DARK_TEXT)

add_rect(slide, 0.35, 4.2, 6.3, 0.9, fill_rgb=DARK_BLUE)
add_text(slide,
         "Bidirectional:  h = [ forward_hT  ;  backward_h₁ ]  →  full context",
         0.55, 4.3, 6.0, 0.65,
         font_size=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

add_image(slide, 'figures/fig_bilstm_training.png', 0.35, 5.2, 8.5)

add_rect(slide, 9.1, 1.55, 3.9, 5.6, fill_rgb=LIGHT_GREY,
         line_rgb=GREEN, line_pt=2)
add_text(slide, "Test Results", 9.3, 1.65, 3.5, 0.42,
         font_size=15, bold=True, color=GREEN)
metric_box(slide, "Accuracy",  "99.04 %", 9.2, 2.2,  w=3.5, val_color=GREEN, bg=WHITE)
metric_box(slide, "F1 Macro",  "0.9904",  9.2, 3.45, w=3.5, val_color=GREEN, bg=WHITE)
metric_box(slide, "Misclassified", "43 / 4 489", 9.2, 4.7, w=3.5,
           val_color=MID_BLUE, bg=WHITE)

add_text(slide,
         "Trained on just 2 000 samples — same\n"
         "accuracy as Random Forest (36k samples).\n\n"
         "Gate mechanism eliminates vanishing\n"
         "gradients; steady convergence over 5 epochs.",
         9.3, 5.85, 3.6, 1.5, font_size=12, color=DARK_TEXT)


# ===========================================================================
# SLIDE 8 — BERT (Pending)
# ===========================================================================
slide = prs.slides.add_slide(BLANK)
add_rect(slide, 0, 0, 13.33, 7.5, fill_rgb=WHITE)
header_bar(slide, "BERT — Transformer Fine-tuning",
           "bert-base-uncased · 2 000 training samples · 2 epochs")

add_rect(slide, 0.35, 1.55, 6.5, 5.6, fill_rgb=LIGHT_GREY,
         line_rgb=RGBColor(0x8E, 0x44, 0xAD), line_pt=1)
add_text(slide, "Architecture", 0.55, 1.65, 6.1, 0.42,
         font_size=16, bold=True, color=RGBColor(0x8E, 0x44, 0xAD))
bert_pts = [
    "12 Transformer layers, 768 hidden dims, 12 attention heads",
    "Pre-trained on BookCorpus + Wikipedia (3.3B words)",
    "Self-attention: every token attends to every other",
    "Fine-tuned end-to-end with AdamW  (lr = 2×10⁻⁵)",
    "Classification head on [CLS] token  →  Linear(768, 2)",
    "Max 128 tokens · WordPiece tokeniser · no OOV words",
    "Linear warm-up + decay over 2 epochs",
]
for i, p in enumerate(bert_pts):
    add_text(slide, "▸  " + p, 0.55, 2.2 + i*0.68, 6.1, 0.6,
             font_size=13, color=DARK_TEXT)

add_image(slide, 'figures/fig_bert_training.png', 0.35, 5.2, 6.5)

add_rect(slide, 7.15, 1.55, 5.85, 5.6, fill_rgb=RGBColor(0x2C, 0x1A, 0x4A))
add_text(slide, "Test Results", 7.35, 1.65, 5.4, 0.42,
         font_size=15, bold=True, color=RGBColor(0xFF, 0xD7, 0x00))

metric_box(slide, "Accuracy",     "99.87 %",  7.25, 2.2,  w=2.6, val_color=RGBColor(0xFF,0xD7,0x00), bg=RGBColor(0x3A,0x25,0x5C))
metric_box(slide, "F1 Macro",     "0.9987",   10.0, 2.2,  w=2.6, val_color=RGBColor(0xFF,0xD7,0x00), bg=RGBColor(0x3A,0x25,0x5C))
metric_box(slide, "Misclassified","6 / 4 489", 7.25, 3.5,  w=2.6, val_color=WHITE,  bg=RGBColor(0x3A,0x25,0x5C))
metric_box(slide, "Epochs",       "2",         10.0, 3.5,  w=2.6, val_color=WHITE,  bg=RGBColor(0x3A,0x25,0x5C))

add_text(slide,
         "After just 1 epoch: val acc = 99.91%\n"
         "After 2 epochs: train loss → 0.0017\n\n"
         "BERT's pre-trained representations\n"
         "need minimal fine-tuning — the\n"
         "[CLS] token learns near-perfect\n"
         "linear separation in 2 epochs.\n\n"
         "Best result across all 6 models.",
         7.35, 4.75, 5.4, 2.3,
         font_size=13, color=WHITE)


# ===========================================================================
# SLIDE 9 — Model Comparison
# ===========================================================================
slide = prs.slides.add_slide(BLANK)
add_rect(slide, 0, 0, 13.33, 7.5, fill_rgb=WHITE)
header_bar(slide, "Model Comparison", "All results on the ISOT test set")

add_image(slide, 'figures/fig_all_models.png', 0.35, 1.5, 8.0)

add_rect(slide, 8.65, 1.55, 4.35, 5.6, fill_rgb=LIGHT_GREY,
         line_rgb=MID_BLUE, line_pt=1)
add_text(slide, "Summary Table", 8.85, 1.65, 4.0, 0.42,
         font_size=15, bold=True, color=MID_BLUE)

rows = [
    ("Naive Bayes",        "94.0 %", "35 918"),
    ("Logistic Regression","99.1 %", "35 918"),
    ("Random Forest",      "99.8 %", "35 918"),
    ("RNN",                "70.3 %", "2 000"),
    ("Bi-LSTM",            "99.0 %", "2 000"),
    ("BERT",               "99.87 %","2 000"),
]
add_text(slide, "Model",    8.85, 2.18, 2.2, 0.35, font_size=12, bold=True, color=MID_BLUE)
add_text(slide, "Accuracy", 11.1, 2.18, 1.1, 0.35, font_size=12, bold=True, color=MID_BLUE)

for i, (name, acc, train) in enumerate(rows):
    y = 2.6 + i * 0.65
    bg = RGBColor(0xE8, 0xF5, 0xE9) if acc not in ("TBD",) and float(acc.replace(" %","")) > 99 else WHITE
    if acc == "TBD":
        bg = RGBColor(0xF3, 0xE5, 0xF5)
    add_rect(slide, 8.7, y, 4.2, 0.55, fill_rgb=bg)
    add_text(slide, name, 8.85, y+0.08, 2.1, 0.38, font_size=12, color=DARK_TEXT)
    col = GREEN if acc not in ("TBD",) and float(acc.replace(" %","")) > 99 else (RED if float(acc.replace(" %","")) < 80 else DARK_TEXT) if acc != "TBD" else RGBColor(0x8E,0x44,0xAD)
    add_text(slide, acc, 11.1, y+0.08, 1.7, 0.38,
             font_size=12, bold=True, color=col)


# ===========================================================================
# SLIDE 10 — Conclusions
# ===========================================================================
slide = prs.slides.add_slide(BLANK)
add_rect(slide, 0, 0, 13.33, 7.5, fill_rgb=WHITE)
header_bar(slide, "Conclusions & Future Work", "")

add_rect(slide, 0.35, 1.55, 8.0, 5.6, fill_rgb=LIGHT_GREY,
         line_rgb=MID_BLUE, line_pt=1)
add_text(slide, "Key Findings", 0.55, 1.65, 7.6, 0.42,
         font_size=16, bold=True, color=MID_BLUE)
findings = [
    "ISOT corpus has strong stylistic signals — even Naive Bayes hits 94 %",
    "Random Forest (TF-IDF) achieves 99.8 % — best classical result",
    "Vanilla RNN struggles: vanishing gradients on 150-token sequences → 70.3 %",
    "Bi-LSTM solves this via gates: 99.04 % accuracy from only 2 000 samples",
    "BERT achieves 99.87 % — the best result — in just 2 epochs of fine-tuning",
    "Architecture quality > dataset size when the signal-to-noise ratio is high",
]
for i, f in enumerate(findings):
    add_text(slide, "▸  " + f, 0.55, 2.22 + i*0.82, 7.6, 0.72,
             font_size=13, color=DARK_TEXT)

add_rect(slide, 8.7, 1.55, 4.3, 5.6, fill_rgb=DARK_BLUE)
add_text(slide, "Future Work", 8.9, 1.65, 3.9, 0.42,
         font_size=16, bold=True, color=ACCENT)
future = [
    "Test on noisier / cross-domain datasets",
    "Multilingual fake news detection",
    "Multimodal models (text + images + metadata)",
    "Model explainability (LIME / SHAP / BertViz)",
    "Graph-based propagation modelling",
    "Lightweight distillation for real-time deployment",
]
for i, f in enumerate(future):
    add_text(slide, "▸  " + f, 8.9, 2.22 + i*0.82, 3.9, 0.72,
             font_size=13, color=WHITE)

# ---------------------------------------------------------------------------
prs.save('presentation.pptx')
print('Saved: presentation.pptx')
