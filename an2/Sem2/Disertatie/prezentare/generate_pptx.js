// generate_pptx.js  –  Social Media Bots dissertation presentation
// Run from the folder that contains this file:
//   node generate_pptx.js
// Requires: npm install -g pptxgenjs

const pptxgen = require("pptxgenjs");
const path    = require("path");
const fs      = require("fs");

// ── palette ───────────────────────────────────────────────────────────────────
const BLUE    = "004174";   // blueCS  RGB(0,65,116)
const YELLOW  = "F5E1BE";   // yellowCS RGB(245,225,190)
const WHITE   = "FFFFFF";
const DARK    = "1A1A2E";   // near-black for body text on white
const LGRAY   = "E8EFF5";   // very light blue-tint for content bg
const DGRAY   = "5A6A7A";   // muted text

// ── image paths ───────────────────────────────────────────────────────────────
const IMG_DIR  = path.join(__dirname, "CSTheme_EN", "img");
const LOGO_CS  = path.join(IMG_DIR, "CS_white_logo.png");
const LOGO_UBB = path.join(IMG_DIR, "Sigla_UBB_claudiopolitana_alb.png");

// ── fonts ─────────────────────────────────────────────────────────────────────
// Oswald/Lato available on user's machine (from LaTeX template).
// Safe fallbacks rendered in LibreOffice QA: Arial / Calibri.
const F_TITLE  = "Arial";      // Oswald substitute for QA safety
const F_BODY   = "Calibri";

// ── layout ────────────────────────────────────────────────────────────────────
// Match Beamer 4:3 = 10" × 7.5"
const W = 10, H = 7.5;

// ── helpers ───────────────────────────────────────────────────────────────────
function makeShadow() {
  return { type: "outer", color: "000000", blur: 5, offset: 2, angle: 45, opacity: 0.12 };
}

// Full-slide blueCS background (for title / section / contact slides)
function addBlueBg(slide) {
  slide.background = { color: BLUE };
}

// Full-slide light background (content slides)
function addLightBg(slide) {
  slide.background = { color: "F4F8FC" };
}

// Slide title bar on content slides (no stripe – just coloured text)
function addContentTitle(slide, title) {
  slide.addText(title, {
    x: 0.4, y: 0.18, w: 9.2, h: 0.7,
    fontFace: F_TITLE, fontSize: 26, bold: true,
    color: BLUE, align: "left", valign: "middle", margin: 0,
  });
  // thin yellow rule under title (a cosmetic shape, not a stripe)
  slide.addShape("rect", {
    x: 0.4, y: 0.90, w: 9.2, h: 0.03,
    fill: { color: YELLOW }, line: { color: YELLOW },
  });
}

// Highlight / block box (like Beamer \begin{block})
function addBlock(slide, blockTitle, lines, opts = {}) {
  const {
    x = 0.4, y, w = 9.2, h = 1.0,
    titleSize = 12, bodySize = 11,
  } = opts;

  // Container with blue fill and soft shadow
  slide.addShape("roundRect", {
    x, y, w, h, rectRadius: 0.06,
    fill: { color: BLUE },
    shadow: makeShadow(),
    line: { color: BLUE },
  });

  // Yellow title row inside box
  slide.addText(blockTitle, {
    x: x + 0.08, y: y + 0.04, w: w - 0.16, h: 0.28,
    fontFace: F_TITLE, fontSize: titleSize, bold: true,
    color: YELLOW, align: "center", valign: "middle", margin: 0,
  });

  // White body text
  if (lines && lines.length) {
    const bodyItems = lines.map((txt, i) => ({
      text: txt,
      options: { breakLine: i < lines.length - 1 },
    }));
    slide.addText(bodyItems, {
      x: x + 0.12, y: y + 0.34, w: w - 0.24, h: h - 0.40,
      fontFace: F_BODY, fontSize: bodySize,
      color: WHITE, align: "left", valign: "top", margin: 0,
    });
  }
}

// Bullet list helper
function bullets(items, opts = {}) {
  return items.map((txt, i) => ({
    text: txt,
    options: { bullet: true, breakLine: i < items.length - 1, ...opts },
  }));
}

// Two-column card (blue fill, yellow title, white body)
function addCard(slide, title, bodyLines, cx, cy, cw, ch, bodySize = 10) {
  slide.addShape("roundRect", {
    x: cx, y: cy, w: cw, h: ch, rectRadius: 0.06,
    fill: { color: BLUE },
    shadow: makeShadow(),
    line: { color: BLUE },
  });
  slide.addText(title, {
    x: cx + 0.08, y: cy + 0.05, w: cw - 0.16, h: 0.28,
    fontFace: F_TITLE, fontSize: 11, bold: true,
    color: YELLOW, align: "center", valign: "middle", margin: 0,
  });
  const items = bodyLines.map((t, i) => ({
    text: t,
    options: { breakLine: i < bodyLines.length - 1 },
  }));
  slide.addText(items, {
    x: cx + 0.10, y: cy + 0.35, w: cw - 0.20, h: ch - 0.42,
    fontFace: F_BODY, fontSize: bodySize,
    color: WHITE, align: "left", valign: "top", margin: 0,
  });
}


// ══════════════════════════════════════════════════════════════════════════════
const pres = new pptxgen();
pres.layout  = "LAYOUT_4x3";   // 10" × 7.5"
pres.author  = "Murariu Tudor Cristian";
pres.title   = "Social Media Bots in the Age of Generative AI";
pres.subject = "Disertatie – HPCBDA, UBB 2026";

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 1 – TITLU
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  addBlueBg(s);

  // Logos row
  if (fs.existsSync(LOGO_CS))  s.addImage({ path: LOGO_CS,  x: 0.5,  y: 0.30, w: 1.5, h: 1.5 });
  if (fs.existsSync(LOGO_UBB)) s.addImage({ path: LOGO_UBB, x: 8.0,  y: 0.30, w: 1.5, h: 1.5 });

  // Yellow horizontal rule
  s.addShape("rect", {
    x: 1.8, y: 2.00, w: 6.4, h: 0.04,
    fill: { color: YELLOW }, line: { color: YELLOW },
  });

  // Main title
  s.addText([
    { text: "Social Media Bots", options: { breakLine: true } },
    { text: "in the Age of Generative AI", options: { fontSize: 28, breakLine: true } },
  ], {
    x: 0.6, y: 2.10, w: 8.8, h: 1.30,
    fontFace: F_TITLE, fontSize: 36, bold: true,
    color: YELLOW, align: "center", valign: "middle",
  });

  // Subtitle line
  s.addText("Detection, Simulation, and Electoral Influence", {
    x: 0.6, y: 3.45, w: 8.8, h: 0.40,
    fontFace: F_BODY, fontSize: 14, italic: true,
    color: YELLOW, align: "center",
  });

  // Rule 2
  s.addShape("rect", {
    x: 1.8, y: 3.90, w: 6.4, h: 0.04,
    fill: { color: YELLOW }, line: { color: YELLOW },
  });

  // Author
  s.addText("Murariu Tudor Cristian", {
    x: 0.6, y: 4.05, w: 8.8, h: 0.38,
    fontFace: F_TITLE, fontSize: 16, bold: true,
    color: WHITE, align: "center",
  });

  // Faculty / University
  s.addText("Facultatea de Matematică și Informatică", {
    x: 0.6, y: 4.50, w: 8.8, h: 0.32,
    fontFace: F_BODY, fontSize: 13,
    color: YELLOW, align: "center",
  });
  s.addText("Universitatea Babeș-Bolyai  ·  2026", {
    x: 0.6, y: 4.85, w: 8.8, h: 0.32,
    fontFace: F_BODY, fontSize: 13,
    color: WHITE, align: "center",
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// helper: section-divider slide (template-2 style)
// ─────────────────────────────────────────────────────────────────────────────
function addSectionSlide(title, subtitle) {
  const s = pres.addSlide();
  addBlueBg(s);

  // Large yellow title
  s.addText(title, {
    x: 0.6, y: 2.2, w: 8.8, h: 1.1,
    fontFace: F_TITLE, fontSize: 40, bold: true,
    color: YELLOW, align: "left", valign: "middle",
  });

  // White subtitle
  s.addText(subtitle, {
    x: 0.6, y: 3.5, w: 8.8, h: 0.55,
    fontFace: F_BODY, fontSize: 20,
    color: WHITE, align: "left",
  });

  // CS logo bottom-left
  if (fs.existsSync(LOGO_CS))
    s.addImage({ path: LOGO_CS, x: 0.4, y: 6.10, w: 1.2, h: 1.2 });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 2 – SECTION: Introducere
// ─────────────────────────────────────────────────────────────────────────────
addSectionSlide("Introducere", "Context și motivație");

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 3 – Contextul: un caz fără precedent
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  addLightBg(s);
  addContentTitle(s, "Contextul: un caz fără precedent");

  s.addText(bullets([
    "24 noiembrie 2024 – alegerile prezidențiale din România sunt anulate de Curtea Constituțională",
    "Operațiune coordonată prin TikTok și Telegram, cu amplificare artificială masivă",
    "~25.000 de conturi coordonate identificate de serviciile de informare",
    "Creștere de peste 200% a numărului de urmăritori într-o singură săptămână",
    "Prima anulare electorală din istoria UE motivată explicit prin influență coordonată online",
  ], { fontSize: 13 }), {
    x: 0.4, y: 1.05, w: 9.2, h: 3.30,
    fontFace: F_BODY, fontSize: 13, color: DARK,
    align: "left", valign: "top",
  });

  addBlock(s, "De ce contează pentru cercetare",
    [
      "Cazul României demonstrează că bot-ii de social media nu mai sunt un fenomen academic —",
      "ei pot altera rezultate electorale la scară națională.",
    ],
    { x: 0.4, y: 4.55, w: 9.2, h: 1.20, bodySize: 12 }
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 4 – Întrebările de cercetare
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  addLightBg(s);
  addContentTitle(s, "Întrebările de cercetare");

  s.addText(bullets([
    "Cap. 4 — Cum sunt construiți bot-ii de social media? Taxonomie și evoluție",
    "Cap. 5 — Cum îi detectează Machine Learning? Metode clasice și moderne",
    "Cap. 2 & 7 — Cum schimbă AI-ul generativ ambele părți ale conflictului?",
  ], { fontSize: 14 }), {
    x: 0.4, y: 1.05, w: 9.2, h: 2.50,
    fontFace: F_BODY, fontSize: 14, color: DARK,
    align: "left", valign: "top",
  });

  addBlock(s, "Contribuții experimentale originale",
    [
      "Experimentul 1 (Cap. 6): Detector multimodal BiLSTM antrenat pe Cresci-2017",
      "Experimentul 2 (Cap. 7): Generator de bot-i AI pentru red-teaming defensiv",
    ],
    { x: 0.4, y: 3.75, w: 9.2, h: 1.40, bodySize: 13 }
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 5 – Trei generații de bot-i
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  addLightBg(s);
  addContentTitle(s, "Trei generații de bot-i");

  const CW = 2.85, CH = 2.50, CY = 1.10;
  addCard(s, "Generația 1  ·  pre-2014",
    ["Scripturi simple", "Postare automată", "Fără adaptare la context"],
    0.4, CY, CW, CH);
  addCard(s, "Generația 2  ·  2014–2019",
    ["Social spambots", "Profil realist", "Comportament coordonat", "Evitare detecție"],
    3.57, CY, CW, CH);
  addCard(s, "Generația 3  ·  2020–prezent",
    ["Persoane LLM", "Deepfake-uri", "Identități sintetice complete"],
    6.74, CY, CW, CH);

  addBlock(s, "Schimbarea fundamentală",
    [
      "Conținutul generat de AI nu mai este un discriminator de încredere.",
      "Detecția trebuie să se deplaseze spre semnale comportamentale și de rețea.",
    ],
    { x: 0.4, y: 3.80, w: 9.2, h: 1.20, bodySize: 12 }
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 6 – Scara fenomenului: Big Data
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  addLightBg(s);
  addContentTitle(s, "Scara fenomenului: de ce e o problemă de Big Data");

  // Left card
  addCard(s, "Operațiuni documentate",
    [
      "Operation SIMCARTEL (Europol, oct. 2025)",
      "  49 milioane conturi false, 80+ țări",
      "",
      "TwiBot-22",
      "  926.949 conturi, 139M tweet-uri, structură de graf",
      "",
      "Cresci-2017",
      "  13.240 conturi, 6,6M tweet-uri",
    ],
    0.4, 1.10, 4.50, 3.60, 11);

  // Right card
  addCard(s, "Implicații tehnice",
    [
      "Detecția la scară reală necesită:",
      "",
      "• Procesare distribuită pentru grafuri sociale masive",
      "• Streaming în timp real (Apache Kafka, Spark)",
      "• Modele care nu se degradează la milioane de noduri",
    ],
    5.10, 1.10, 4.50, 3.60, 11);
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 7 – SECTION: Experimentul 1
// ─────────────────────────────────────────────────────────────────────────────
addSectionSlide("Experimentul 1", "Detectarea bot-ilor cu un BiLSTM multimodal");

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 8 – Obiectiv și date
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  addLightBg(s);
  addContentTitle(s, "Obiectiv și date");

  s.addText(bullets([
    "Obiectiv: detector multimodal BiLSTM bidirecțional cu self-attention",
    "Combină metadata cont (features numerice) + embedding-uri tweet-uri (semantică)",
    "Dataset: Cresci-2017 — 13.240 conturi, 6,6M tweet-uri",
    "TwiBot-22 exclus: cost computațional prohibitiv pentru hardware disponibil",
  ], { fontSize: 13 }), {
    x: 0.4, y: 1.05, w: 9.2, h: 3.00,
    fontFace: F_BODY, fontSize: 13, color: DARK,
    align: "left", valign: "top",
  });

  addBlock(s, "Problema metodologică centrală",
    [
      "Conturile bot și umane din Cresci-2017 au fost colectate în perioade diferite.",
      "Există risc de artefacte de eșantionare temporală — modelul poate învăța distribuția",
      "temporală, nu comportamentul real.",
    ],
    { x: 0.4, y: 4.25, w: 9.2, h: 1.45, bodySize: 11 }
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 9 – Arhitectura modelului
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  addLightBg(s);
  addContentTitle(s, "Arhitectura modelului");

  // Left column – Metadata branch
  addCard(s, "Ramura Metadata",
    [
      "4 grupuri tematice de features:",
      "rețea, activitate, profil, rapoarte derivate",
      "",
      "→ Bi-LSTM (hidden 128, 2 straturi)",
      "→ Self-attention",
      "→ Output 256-d",
    ],
    0.4, 1.10, 4.50, 2.90, 11);

  // Right column – Text branch
  addCard(s, "Ramura Text",
    [
      "Sentence-embedding 384-d",
      "(all-MiniLM-L6-v2)",
      "",
      "→ Proiecție la 128-d",
      "→ LayerNorm + ReLU",
      "→ Output 128-d",
    ],
    5.10, 1.10, 4.50, 2.90, 11);

  addBlock(s, "Fuziune și clasificare",
    [
      "Concatenare (256+128) → MLP cu sigmoid",
      "639.682 parametri total  ·  Antrenat pe RTX 4060 8GB VRAM",
    ],
    { x: 0.4, y: 4.18, w: 9.2, h: 1.15, bodySize: 12 }
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 10 – Rezultate
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  addLightBg(s);
  addContentTitle(s, "Rezultate");

  // Stat callouts row
  const stats = [
    { val: "99,21%", lbl: "Acuratețe test set" },
    { val: "98,98%", lbl: "F1 macro" },
    { val: "98,64%", lbl: "Doar metadata" },
  ];
  stats.forEach((st, i) => {
    const cx = 0.4 + i * 3.1;
    s.addShape("roundRect", {
      x: cx, y: 1.10, w: 2.85, h: 1.55, rectRadius: 0.08,
      fill: { color: LGRAY },
      shadow: makeShadow(),
      line: { color: LGRAY },
    });
    s.addText(st.val, {
      x: cx + 0.05, y: 1.18, w: 2.75, h: 0.75,
      fontFace: F_TITLE, fontSize: 32, bold: true,
      color: BLUE, align: "center", valign: "middle",
    });
    s.addText(st.lbl, {
      x: cx + 0.05, y: 1.94, w: 2.75, h: 0.55,
      fontFace: F_BODY, fontSize: 11,
      color: DGRAY, align: "center",
    });
  });

  // Comparison note
  s.addText(
    "Comparabil sau superior față de Botometer, BotRGCN și alte sisteme publicate pe seturi similare.",
    {
      x: 0.4, y: 2.85, w: 9.2, h: 0.55,
      fontFace: F_BODY, fontSize: 12, italic: true,
      color: DGRAY, align: "left",
    }
  );

  addBlock(s, "Limitare recunoscută explicit",
    [
      "Fără evaluare cross-dataset. Un scor de 99% pe Cresci-2017 nu dovedește generalizare —",
      "modelul poate fi supraajustat pe caracteristicile acestui dataset din 2017.",
    ],
    { x: 0.4, y: 3.55, w: 9.2, h: 1.30, bodySize: 12 }
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 11 – SECTION: Experimentul 2
// ─────────────────────────────────────────────────────────────────────────────
addSectionSlide("Experimentul 2", "Simularea bot-ilor generați de AI");

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 12 – Conceptul: o fermă de bot-i simulată
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  addLightBg(s);
  addContentTitle(s, "Conceptul: o fermă de bot-i simulată");

  s.addText(bullets([
    "Scop: înțelegere și red-teaming defensiv, NU deployment real",
    "Patru straturi generative independente:",
  ], { fontSize: 13 }), {
    x: 0.4, y: 1.05, w: 9.2, h: 1.20,
    fontFace: F_BODY, fontSize: 13, color: DARK,
    align: "left", valign: "top",
  });

  addCard(s, "Generare conținut",
    [
      "Text / conversații → Llama 3.1 8B (local, Ollama)",
      "Fotografii profil → Stable Diffusion Dreamshaper 8",
      "Video scurt → LTX-Video (generat local)",
    ],
    0.4, 2.40, 4.50, 2.00, 11);

  addCard(s, "Evaluare",
    [
      "Detecție → BiLSTM-ul din Experimentul 1",
      "",
      "Cadru închis:",
      "generare → test → analiză eșec",
    ],
    5.10, 2.40, 4.50, 2.00, 11);

  addBlock(s, "Cadru de red-teaming defensiv",
    ["Sistemul este proiectat pentru înțelegerea vulnerabilităților, nu pentru exploatare."],
    { x: 0.4, y: 4.58, w: 9.2, h: 0.90, bodySize: 12 }
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 13 – Ce produce sistemul
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  addLightBg(s);
  addContentTitle(s, "Ce produce sistemul");

  s.addText(bullets([
    "Profil JSON generat în secunde (biografie, interese, stil)",
    "Postări 280 caractere fără fine-tuning explicit",
    "Conversații DM cu memorie pe 20 de schimburi",
    "Fotografii 512×512, fără artefacte GAN clasice",
    "Video 3 secunde generat complet local",
  ], { fontSize: 13 }), {
    x: 0.4, y: 1.05, w: 5.50, h: 3.50,
    fontFace: F_BODY, fontSize: 13, color: DARK,
    align: "left", valign: "top",
  });

  addCard(s, "Cost marginal",
    [
      "Fracțiuni de cent per postare generată.",
      "",
      "O identitate sintetică completă poate fi",
      "produsă în sub un minut pe hardware",
      "consumer (RTX 4060).",
    ],
    6.10, 1.05, 3.50, 3.50, 11);
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 14 – Bucla de detecție
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  addLightBg(s);
  addContentTitle(s, "Bucla de detecție: constatarea centrală");

  s.addText(bullets([
    "Conturile generate au fost trecute prin detectorul din Experimentul 1",
    "Majoritatea marcate 'bot' cu probabilitate mare (>0,90)",
    "Detectorul îi recunoaște ca bot-i înainte să posteze ceva",
  ], { fontSize: 13 }), {
    x: 0.4, y: 1.05, w: 9.2, h: 2.20,
    fontFace: F_BODY, fontSize: 13, color: DARK,
    align: "left", valign: "top",
  });

  addBlock(s, "De ce? Motiv tehnic, nu conceptual",
    [
      "Metadata generată sintetic nu se aliniază cu distribuțiile din Cresci-2017 (dataset din 2017).",
      "Detectorul nu îi 'vede' — îi respinge pe baza distribuției statistice a features-urilor.",
      "",
      "Concluzie: cursa co-evolutivă clasificator–generator necesită date actuale și re-antrenare continuă.",
    ],
    { x: 0.4, y: 3.40, w: 9.2, h: 1.80, bodySize: 11 }
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 15 – SECTION: Concluzii
// ─────────────────────────────────────────────────────────────────────────────
addSectionSlide("Concluzii", "Și demonstrație live");

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 16 – Concluzii
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  addLightBg(s);
  addContentTitle(s, "Concluzii");

  s.addText(bullets([
    "Costul producerii unei identități false s-a prăbușit (fracțiuni de cent)",
    "Costul detectării NU a scăzut în același ritm — asimetrie fundamentală",
    "Cazul României arată că această asimetrie are consecințe electorale reale",
  ], { fontSize: 14 }), {
    x: 0.4, y: 1.05, w: 9.2, h: 2.40,
    fontFace: F_BODY, fontSize: 14, color: DARK,
    align: "left", valign: "top",
  });

  addBlock(s, "Direcții viitoare",
    [
      "• Evaluare cross-dataset ca standard minim obligatoriu",
      "• Date actualizate (post-2020) pentru a reflecta bot-ii de Generația 3",
      "• Semnale comportamentale și relaționale (grafuri de interacțiune) în locul metadatei statice",
    ],
    { x: 0.4, y: 3.65, w: 9.2, h: 1.55, bodySize: 12 }
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 17 – Demonstrație live
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  addBlueBg(s);

  s.addText("Demo: simulatorul din Experimentul 2", {
    x: 0.6, y: 2.40, w: 8.8, h: 0.90,
    fontFace: F_TITLE, fontSize: 32, bold: true,
    color: YELLOW, align: "center", valign: "middle",
  });
  s.addText([
    { text: "Crearea unui bot, generarea conținutului", options: { breakLine: true } },
    { text: "și scanarea cu detectorul BiLSTM" },
  ], {
    x: 0.6, y: 3.45, w: 8.8, h: 0.80,
    fontFace: F_BODY, fontSize: 16,
    color: WHITE, align: "center",
  });

  if (fs.existsSync(LOGO_CS))
    s.addImage({ path: LOGO_CS, x: 4.1, y: 5.50, w: 1.8, h: 1.8 });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 18 – CONTACT
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  addBlueBg(s);

  if (fs.existsSync(LOGO_CS))
    s.addImage({ path: LOGO_CS, x: 0.4, y: 1.60, w: 2.00, h: 2.00 });

  // Vertical rule
  s.addShape("rect", {
    x: 3.0, y: 1.60, w: 0.04, h: 3.40,
    fill: { color: WHITE }, line: { color: WHITE },
  });

  s.addText("FACULTATEA DE MATEMATICĂ ȘI INFORMATICĂ", {
    x: 3.30, y: 1.65, w: 6.30, h: 0.40,
    fontFace: F_TITLE, fontSize: 11, bold: true,
    color: WHITE, align: "left",
  });
  s.addText("UNIVERSITATEA BABEȘ-BOLYAI", {
    x: 3.30, y: 2.10, w: 6.30, h: 0.38,
    fontFace: F_TITLE, fontSize: 11,
    color: WHITE, align: "left",
  });
  s.addText([
    { text: "1 Mihail Kogălniceanu Street", options: { breakLine: true } },
    { text: "Cluj-Napoca, Cluj, România" },
  ], {
    x: 3.30, y: 2.65, w: 6.30, h: 0.75,
    fontFace: F_BODY, fontSize: 11,
    color: WHITE, align: "left",
  });
  s.addText("www.cs.ubbcluj.ro", {
    x: 3.30, y: 3.55, w: 6.30, h: 0.38,
    fontFace: F_BODY, fontSize: 12,
    color: YELLOW, align: "left",
  });

  s.addText("Murariu Tudor Cristian  ·  tudor.cristian.murariu.w@gmail.com", {
    x: 0.4, y: 6.80, w: 9.2, h: 0.38,
    fontFace: F_BODY, fontSize: 10,
    color: WHITE, align: "center",
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// WRITE FILE
// ─────────────────────────────────────────────────────────────────────────────
const OUT = path.join(__dirname, "prezentare_disertatie.pptx");
pres.writeFile({ fileName: OUT })
  .then(() => console.log("OK: " + OUT))
  .catch(e  => { console.error("ERR:", e); process.exit(1); });
