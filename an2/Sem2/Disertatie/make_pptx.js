// BotFarm Defense Presentation — PptxGenJS generator
// Run: node make_pptx.js
"use strict";

const pptxgen = require("pptxgenjs");
const path    = require("path");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";          // 10 × 5.625 inches
pres.author = "Murariu Tudor Cristian";
pres.title  = "Social Media Bots in the Age of Generative AI";

// ── Palette ──────────────────────────────────────────────────────────────────
const C = {
  bg      : "0f172a",   // slate-900
  card    : "1e293b",   // slate-800
  blue    : "3b82f6",   // blue-500
  blueDark: "1d4ed8",   // blue-700
  blueDeep: "1e3a5f",   // custom deep-blue
  text    : "e2e8f0",   // slate-200
  muted   : "94a3b8",   // slate-400
  faint   : "475569",   // slate-600
  white   : "FFFFFF",
  green   : "22c55e",   // green-500
  amber   : "f59e0b",   // amber-500
  red     : "ef4444",   // red-500
  purple  : "8b5cf6",   // violet-500
};

// ── Helpers ──────────────────────────────────────────────────────────────────
function slide(bg) {
  const s = pres.addSlide();
  s.background = { color: bg || C.bg };
  return s;
}

// Thin blue accent line just below a title (avoids "bar across top" look)
function titleAccent(s, y) {
  s.addShape(pres.ShapeType.rect, {
    x: 0.5, y: y !== undefined ? y : 0.82, w: 0.8, h: 0.04,
    fill: { color: C.blue }, line: { color: C.blue, width: 0 },
  });
}

// ─── SLIDE 1 — TITLE ────────────────────────────────────────────────────────
{
  const s = slide();

  // Background circles (decorative)
  s.addShape(pres.ShapeType.ellipse, {
    x: 7.5, y: -1.4, w: 4.2, h: 4.2,
    fill: { color: C.blueDeep, transparency: 40 },
    line: { color: C.blueDeep, width: 0 },
  });
  s.addShape(pres.ShapeType.ellipse, {
    x: 8.5, y: -0.5, w: 2.2, h: 2.2,
    fill: { color: C.blueDark, transparency: 55 },
    line: { color: C.blueDark, width: 0 },
  });
  s.addShape(pres.ShapeType.ellipse, {
    x: -0.5, y: 3.8, w: 2.5, h: 2.5,
    fill: { color: C.blueDeep, transparency: 60 },
    line: { color: C.blueDeep, width: 0 },
  });

  // Vertical blue accent bar
  s.addShape(pres.ShapeType.rect, {
    x: 0.55, y: 1.3, w: 0.07, h: 1.85,
    fill: { color: C.blue }, line: { color: C.blue, width: 0 },
  });

  // Title lines
  s.addText("Social Media Bots", {
    x: 0.78, y: 1.18, w: 7.8, h: 0.9,
    fontSize: 44, bold: true, color: C.white, fontFace: "Calibri",
    align: "left", margin: 0,
  });
  s.addText("in the Age of Generative AI", {
    x: 0.78, y: 2.0, w: 7.8, h: 0.65,
    fontSize: 28, bold: false, color: C.blue, fontFace: "Calibri",
    align: "left", margin: 0,
  });

  // Divider
  s.addShape(pres.ShapeType.rect, {
    x: 0.78, y: 2.82, w: 6.5, h: 0.025,
    fill: { color: C.faint }, line: { color: C.faint, width: 0 },
  });

  s.addText("Master's Dissertation Defense", {
    x: 0.78, y: 2.96, w: 8, h: 0.38,
    fontSize: 16, color: C.muted, fontFace: "Calibri",
    align: "left", margin: 0,
  });
  s.addText("Murariu Tudor Cristian", {
    x: 0.78, y: 3.4, w: 8, h: 0.42,
    fontSize: 18, bold: true, color: C.text, fontFace: "Calibri",
    align: "left", margin: 0,
  });
  s.addText("Babeș-Bolyai University  ·  Faculty of Mathematics and Computer Science  ·  2025", {
    x: 0.78, y: 3.85, w: 8.6, h: 0.35,
    fontSize: 12.5, color: C.muted, fontFace: "Calibri",
    align: "left", margin: 0,
  });
}

// ─── SLIDE 2 — WHY BOTS MATTER ───────────────────────────────────────────────
{
  const s = slide();

  s.addText("Why Bots Matter", {
    x: 0.5, y: 0.28, w: 9, h: 0.62,
    fontSize: 30, bold: true, color: C.white, fontFace: "Calibri",
    align: "left", margin: 0,
  });

  const bullets = [
    "~15% of Twitter/X accounts are estimated to be automated bots (Varol et al., 2017)",
    "Bot networks amplify disinformation, manipulate trending topics, and influence elections",
    "The Internet Research Agency ran 3,000+ bot accounts during the 2016 US election (Mueller, 2019)",
    "Generative AI has dramatically lowered the cost of creating convincing fake identities",
    "The arms race between bot creation and bot detection is accelerating",
  ];

  s.addText(
    bullets.map((t, i) => ({
      text: t,
      options: { bullet: { type: "bullet" }, breakLine: i < bullets.length - 1, paraSpaceAfter: 10 },
    })),
    {
      x: 0.55, y: 1.08, w: 9.0, h: 4.3,
      fontSize: 16, color: C.text, fontFace: "Calibri",
      align: "left", valign: "top",
    }
  );
}

// ─── SLIDE 3 — TWO EXPERIMENTS ───────────────────────────────────────────────
{
  const s = slide();

  s.addText("Two Experiments, One Question", {
    x: 0.5, y: 0.28, w: 9.2, h: 0.62,
    fontSize: 30, bold: true, color: C.white, fontFace: "Calibri",
    align: "left", margin: 0,
  });

  // Left card — Detection
  s.addShape(pres.ShapeType.rect, {
    x: 0.45, y: 1.1, w: 4.3, h: 3.7,
    fill: { color: C.card }, line: { color: C.blue, width: 1.5 },
  });
  s.addShape(pres.ShapeType.rect, {
    x: 0.45, y: 1.1, w: 4.3, h: 0.06,
    fill: { color: C.blue }, line: { color: C.blue, width: 0 },
  });
  s.addText("Experiment 1 — Detection", {
    x: 0.6, y: 1.18, w: 4.0, h: 0.42,
    fontSize: 14.5, bold: true, color: C.blue, fontFace: "Calibri", margin: 0,
  });
  s.addText(
    [
      { text: "Can we detect bots from metadata + post content?", options: { bullet: { type: "bullet" }, breakLine: true, paraSpaceAfter: 6 } },
      { text: "Dataset: Cresci-2017 (13,240 labeled Twitter accounts)", options: { bullet: { type: "bullet" }, breakLine: true, paraSpaceAfter: 6 } },
      { text: "Model: Multimodal BiLSTM + Self-Attention", options: { bullet: { type: "bullet" }, paraSpaceAfter: 6 } },
    ],
    {
      x: 0.6, y: 1.65, w: 4.05, h: 3.0,
      fontSize: 13.5, color: C.text, fontFace: "Calibri", valign: "top",
    }
  );

  // Right card — Generation
  s.addShape(pres.ShapeType.rect, {
    x: 5.25, y: 1.1, w: 4.3, h: 3.7,
    fill: { color: C.card }, line: { color: C.purple, width: 1.5 },
  });
  s.addShape(pres.ShapeType.rect, {
    x: 5.25, y: 1.1, w: 4.3, h: 0.06,
    fill: { color: C.purple }, line: { color: C.purple, width: 0 },
  });
  s.addText("Experiment 2 — Generation", {
    x: 5.4, y: 1.18, w: 4.0, h: 0.42,
    fontSize: 14.5, bold: true, color: C.purple, fontFace: "Calibri", margin: 0,
  });
  s.addText(
    [
      { text: "How convincing can AI-powered bots become?", options: { bullet: { type: "bullet" }, breakLine: true, paraSpaceAfter: 6 } },
      { text: "Built a full bot farm simulator using open-source generative models", options: { bullet: { type: "bullet" }, breakLine: true, paraSpaceAfter: 6 } },
      { text: "Tested the detector against the generated bots", options: { bullet: { type: "bullet" }, paraSpaceAfter: 6 } },
    ],
    {
      x: 5.4, y: 1.65, w: 4.05, h: 3.0,
      fontSize: 13.5, color: C.text, fontFace: "Calibri", valign: "top",
    }
  );

  // Bottom quote
  s.addText('“Build the attacker. Build the defender. Test them against each other.”', {
    x: 0.45, y: 4.98, w: 9.1, h: 0.38,
    fontSize: 12.5, italic: true, color: C.muted, fontFace: "Calibri",
    align: "center", margin: 0,
  });
}

// ─── SLIDE 4 — DATASET ───────────────────────────────────────────────────────
{
  const s = slide();

  s.addText("Cresci-2017 — The Benchmark", {
    x: 0.5, y: 0.28, w: 9.2, h: 0.62,
    fontSize: 30, bold: true, color: C.white, fontFace: "Calibri",
    align: "left", margin: 0,
  });

  const bullets = [
    "13,240 labeled Twitter accounts — human-verified genuine users + 5 bot categories",
    "Bot categories: Social spambots (×3), Traditional spambots, Fake followers",
    "Class imbalance: 2.8 bots per 1 human account → handled with weighted random sampling",
    "Features per account: 16 metadata fields (followers, posting rate, profile flags…) + up to 50 tweets",
    "Known limitation: temporal sampling bias — bots and humans collected at different times",
  ];

  s.addText(
    bullets.map((t, i) => ({
      text: t,
      options: { bullet: { type: "bullet" }, breakLine: i < bullets.length - 1, paraSpaceAfter: 9 },
    })),
    {
      x: 0.55, y: 1.1, w: 6.7, h: 4.2,
      fontSize: 14.5, color: C.text, fontFace: "Calibri",
      align: "left", valign: "top",
    }
  );

  // Stat cards (right column)
  const stats = [
    { val: "13,240", label: "Labeled accounts", color: C.blue,  y: 1.15 },
    { val: "2.8×",    label: "More bots than humans", color: C.amber, y: 2.55 },
    { val: "77%",    label: "Accounts with tweets", color: C.green, y: 3.95 },
  ];
  stats.forEach(({ val, label, color, y }) => {
    s.addShape(pres.ShapeType.rect, {
      x: 7.55, y, w: 2.1, h: 1.2,
      fill: { color: C.card }, line: { color, width: 1.5 },
    });
    s.addText(val, {
      x: 7.55, y: y + 0.06, w: 2.1, h: 0.7,
      fontSize: 28, bold: true, color, fontFace: "Calibri",
      align: "center", margin: 0,
    });
    s.addText(label, {
      x: 7.55, y: y + 0.78, w: 2.1, h: 0.32,
      fontSize: 11, color: C.muted, fontFace: "Calibri",
      align: "center", margin: 0,
    });
  });
}

// ─── SLIDE 5 — ARCHITECTURE ──────────────────────────────────────────────────
{
  const s = slide();

  s.addText("Multimodal BiLSTM + Self-Attention", {
    x: 0.5, y: 0.28, w: 9.2, h: 0.62,
    fontSize: 30, bold: true, color: C.white, fontFace: "Calibri",
    align: "left", margin: 0,
  });

  // Left — Metadata Branch
  s.addShape(pres.ShapeType.rect, {
    x: 0.4, y: 1.1, w: 4.3, h: 3.0,
    fill: { color: C.card }, line: { color: C.blue, width: 1.5 },
  });
  s.addShape(pres.ShapeType.rect, {
    x: 0.4, y: 1.1, w: 4.3, h: 0.05,
    fill: { color: C.blue }, line: { color: C.blue, width: 0 },
  });
  s.addText("Metadata Branch", {
    x: 0.55, y: 1.17, w: 4.0, h: 0.4,
    fontSize: 14, bold: true, color: C.blue, fontFace: "Calibri", margin: 0,
  });
  s.addText(
    [
      { text: "16 features grouped into 4 thematic sequences:", options: { bullet: false, breakLine: true } },
      { text: "network scale / activity / flags / ratios", options: { bullet: false, italic: true, color: C.muted, breakLine: true, paraSpaceAfter: 5 } },
      { text: "2-layer Bidirectional LSTM (hidden 128)", options: { bullet: { type: "bullet" }, breakLine: true, paraSpaceAfter: 5 } },
      { text: "Self-attention layer → 256-d representation", options: { bullet: { type: "bullet" }, paraSpaceAfter: 5 } },
    ],
    {
      x: 0.55, y: 1.62, w: 4.05, h: 2.35,
      fontSize: 13, color: C.text, fontFace: "Calibri", valign: "top",
    }
  );

  // Right — Text Branch
  s.addShape(pres.ShapeType.rect, {
    x: 5.3, y: 1.1, w: 4.3, h: 3.0,
    fill: { color: C.card }, line: { color: C.purple, width: 1.5 },
  });
  s.addShape(pres.ShapeType.rect, {
    x: 5.3, y: 1.1, w: 4.3, h: 0.05,
    fill: { color: C.purple }, line: { color: C.purple, width: 0 },
  });
  s.addText("Text Branch", {
    x: 5.45, y: 1.17, w: 4.0, h: 0.4,
    fontSize: 14, bold: true, color: C.purple, fontFace: "Calibri", margin: 0,
  });
  s.addText(
    [
      { text: "Up to 50 tweets per account", options: { bullet: { type: "bullet" }, breakLine: true, paraSpaceAfter: 5 } },
      { text: "all-MiniLM-L6-v2 (transformer, frozen)", options: { bullet: { type: "bullet" }, breakLine: true, paraSpaceAfter: 5 } },
      { text: "Mean-pooled across tweets", options: { bullet: { type: "bullet" }, breakLine: true, paraSpaceAfter: 5 } },
      { text: "384-d → projected to 128-d", options: { bullet: { type: "bullet" }, paraSpaceAfter: 5 } },
    ],
    {
      x: 5.45, y: 1.62, w: 4.05, h: 2.35,
      fontSize: 13, color: C.text, fontFace: "Calibri", valign: "top",
    }
  );

  // Fusion box
  s.addShape(pres.ShapeType.rect, {
    x: 1.8, y: 4.27, w: 6.4, h: 1.05,
    fill: { color: "0d2218" }, line: { color: C.green, width: 1.5 },
  });
  s.addText("Fusion  →  Concatenate [256-d + 128-d]  →  2-layer MLP  →  Sigmoid", {
    x: 1.85, y: 4.34, w: 6.3, h: 0.38,
    fontSize: 13, bold: true, color: C.green, fontFace: "Calibri",
    align: "center", margin: 0,
  });
  s.addText("Total: 639,682 trainable parameters", {
    x: 1.85, y: 4.72, w: 6.3, h: 0.3,
    fontSize: 11, color: C.muted, fontFace: "Calibri",
    align: "center", margin: 0,
  });
}

// ─── SLIDE 6 — RESULTS ───────────────────────────────────────────────────────
{
  const s = slide();

  s.addText("Results — 99.2% Accuracy on Cresci-2017", {
    x: 0.5, y: 0.28, w: 9.2, h: 0.62,
    fontSize: 28, bold: true, color: C.white, fontFace: "Calibri",
    align: "left", margin: 0,
  });

  // Big stat cards
  const stats = [
    { val: "99.2%", label: "Test Accuracy",  color: C.green  },
    { val: "99.0%", label: "Macro F1 Score", color: C.blue   },
    { val: "25",    label: "Training Epochs", color: C.amber  },
  ];
  stats.forEach(({ val, label, color }, i) => {
    const x = 0.4 + i * 3.1;
    s.addShape(pres.ShapeType.rect, {
      x, y: 1.12, w: 2.85, h: 1.25,
      fill: { color: C.card }, line: { color, width: 1.5 },
    });
    s.addText(val, {
      x: x + 0.05, y: 1.17, w: 2.75, h: 0.74,
      fontSize: 36, bold: true, color, fontFace: "Calibri",
      align: "center", margin: 0,
    });
    s.addText(label, {
      x: x + 0.05, y: 1.91, w: 2.75, h: 0.3,
      fontSize: 11, color: C.muted, fontFace: "Calibri",
      align: "center", margin: 0,
    });
  });

  // Comparison table
  const hFill = { color: "162844" };
  const rFill = { color: C.card };
  const gFill = { color: "0d2a0d" };

  const rows = [
    [
      { text: "System",    options: { bold: true, color: C.blue,  fill: hFill } },
      { text: "Method",    options: { bold: true, color: C.blue,  fill: hFill } },
      { text: "Accuracy",  options: { bold: true, color: C.blue,  fill: hFill, align: "center" } },
      { text: "F1",        options: { bold: true, color: C.blue,  fill: hFill, align: "center" } },
    ],
    [
      { text: "Botometer (Varol et al., 2017)", options: { color: C.text,  fill: rFill } },
      { text: "Random Forest (1,200+ features)", options: { color: C.muted, fill: rFill } },
      { text: "~95%", options: { color: C.text, fill: rFill, align: "center" } },
      { text: "~94%", options: { color: C.text, fill: rFill, align: "center" } },
    ],
    [
      { text: "LSTM + content",         options: { color: C.text,  fill: rFill } },
      { text: "LSTM, text + metadata",  options: { color: C.muted, fill: rFill } },
      { text: "~96%", options: { color: C.text, fill: rFill, align: "center" } },
      { text: "~95%", options: { color: C.text, fill: rFill, align: "center" } },
    ],
    [
      { text: "BiLSTM+Att (metadata only)", options: { color: C.text,  fill: rFill } },
      { text: "Bi-LSTM + attention",        options: { color: C.muted, fill: rFill } },
      { text: "98.6%", options: { color: C.text, fill: rFill, align: "center" } },
      { text: "98.3%", options: { color: C.text, fill: rFill, align: "center" } },
    ],
    [
      { text: "BiLSTM+Att — OURS",          options: { bold: true, color: C.green, fill: gFill } },
      { text: "Metadata + tweet embeddings", options: {              color: C.green, fill: gFill } },
      { text: "99.2%", options: { bold: true, color: C.green, fill: gFill, align: "center" } },
      { text: "99.0%", options: { bold: true, color: C.green, fill: gFill, align: "center" } },
    ],
  ];

  s.addTable(rows, {
    x: 0.4, y: 2.56, w: 9.2,
    colW: [2.85, 3.1, 1.6, 1.65],
    border: { pt: 0.5, color: "334155" },
    fontFace: "Calibri",
    fontSize: 12,
  });

  s.addText("Adding tweet embeddings raises F1 by 0.7 points over the metadata-only baseline", {
    x: 0.4, y: 5.2, w: 9.2, h: 0.28,
    fontSize: 11, italic: true, color: C.muted, fontFace: "Calibri",
    align: "center", margin: 0,
  });
}

// ─── SLIDE 7 — AI STACK ──────────────────────────────────────────────────────
{
  const s = slide();

  s.addText("Building a Convincing Bot — The AI Stack", {
    x: 0.5, y: 0.28, w: 9.2, h: 0.62,
    fontSize: 30, bold: true, color: C.white, fontFace: "Calibri",
    align: "left", margin: 0,
  });

  const cols = [
    {
      color: C.blue, label: "TEXT & CHAT",
      title: "Llama 3.1 8B", sub: "via Ollama (local)",
      bullets: [
        "Profile generation (username, bio, stats)",
        "Post writing (280-char tweets)",
        "Live DM conversations with memory",
      ],
    },
    {
      color: C.purple, label: "PROFILE PHOTOS",
      title: "Dreamshaper-8", sub: "Stable Diffusion 1.5",
      bullets: [
        "Photorealistic portraits",
        "Persona-specific prompts",
        "5–10 sec on RTX 4060",
        "Defeats GAN-face detectors",
      ],
    },
    {
      color: C.amber, label: "VIDEO POSTS",
      title: "LTX-Video", sub: "Lightricks, 2024",
      bullets: [
        "Text-to-video, 49 frames @ 16fps",
        "Persona-specific scene prompts",
        "Runs locally on consumer GPU",
      ],
    },
  ];

  cols.forEach(({ color, label, title, sub, bullets }, i) => {
    const x = 0.4 + i * 3.2;
    s.addShape(pres.ShapeType.rect, {
      x, y: 1.1, w: 2.98, h: 4.25,
      fill: { color: C.card }, line: { color, width: 1.5 },
    });
    s.addShape(pres.ShapeType.rect, {
      x, y: 1.1, w: 2.98, h: 0.05,
      fill: { color }, line: { color, width: 0 },
    });
    s.addText(label, {
      x: x + 0.14, y: 1.18, w: 2.7, h: 0.3,
      fontSize: 9.5, bold: true, color, fontFace: "Calibri",
      charSpacing: 1.5, margin: 0,
    });
    s.addText(title, {
      x: x + 0.14, y: 1.5, w: 2.7, h: 0.52,
      fontSize: 19, bold: true, color: C.white, fontFace: "Calibri", margin: 0,
    });
    s.addText(sub, {
      x: x + 0.14, y: 2.0, w: 2.7, h: 0.3,
      fontSize: 11, italic: true, color: C.muted, fontFace: "Calibri", margin: 0,
    });
    s.addShape(pres.ShapeType.rect, {
      x: x + 0.14, y: 2.38, w: 2.6, h: 0.02,
      fill: { color: "334155" }, line: { color: "334155", width: 0 },
    });
    s.addText(
      bullets.map((t, bi) => ({
        text: t,
        options: { bullet: { type: "bullet" }, breakLine: bi < bullets.length - 1, paraSpaceAfter: 5 },
      })),
      {
        x: x + 0.14, y: 2.46, w: 2.7, h: 2.82,
        fontSize: 12.5, color: C.text, fontFace: "Calibri", valign: "top",
      }
    );
  });
}

// ─── SLIDE 8 — SIMULATOR ─────────────────────────────────────────────────────
{
  const s = slide();

  s.addText("BotFarm Simulator — Feature Overview", {
    x: 0.5, y: 0.28, w: 9.2, h: 0.62,
    fontSize: 30, bold: true, color: C.white, fontFace: "Calibri",
    align: "left", margin: 0,
  });

  const bullets = [
    "6 persona types: General, Political, Sports, News, Influencer, Conspiracy",
    "Each persona has a system prompt that shapes all generated content",
    "AI-generated profile picture per bot (Dreamshaper-8, ∼5–10 s on GPU)",
    "Automated post scheduling — from 5 seconds to hours between posts",
    "Video post generation (LTX-Video) with graceful text-only fallback",
    "Live DM chat — Llama maintains persona across entire conversation",
    "Full web interface: Feed, Profile, Admin dashboard, Bot Detector",
  ];

  s.addText(
    bullets.map((t, i) => ({
      text: t,
      options: { bullet: { type: "bullet" }, breakLine: i < bullets.length - 1, paraSpaceAfter: 8 },
    })),
    {
      x: 0.55, y: 1.1, w: 6.2, h: 4.3,
      fontSize: 14.5, color: C.text, fontFace: "Calibri",
      align: "left", valign: "top",
    }
  );

  // Persona color chips
  const personas = [
    { label: "General",    color: "6366f1" },
    { label: "Political",  color: C.red    },
    { label: "Sports",     color: C.green  },
    { label: "News",       color: C.amber  },
    { label: "Influencer", color: "ec4899" },
    { label: "Conspiracy", color: C.purple },
  ];
  personas.forEach(({ label, color }, i) => {
    const row = Math.floor(i / 2);
    const col = i % 2;
    const x = 7.0 + col * 1.52;
    const y = 1.15 + row * 0.9;
    s.addShape(pres.ShapeType.rect, {
      x, y, w: 1.38, h: 0.68,
      fill: { color, transparency: 65 }, line: { color, width: 1 },
    });
    s.addText(label, {
      x, y, w: 1.38, h: 0.68,
      fontSize: 12, bold: true, color: C.white, fontFace: "Calibri",
      align: "center", valign: "middle", margin: 0,
    });
  });
}

// ─── SLIDE 9 — DETECTION GAP ─────────────────────────────────────────────────
{
  const s = slide();

  s.addText("The Detection Gap", {
    x: 0.5, y: 0.28, w: 9.2, h: 0.62,
    fontSize: 30, bold: true, color: C.white, fontFace: "Calibri",
    align: "left", margin: 0,
  });

  const points = [
    {
      num: "01", color: C.blue, head: "Profile Photos",
      body: "Diffusion-generated faces carry no GAN artefacts. Classifiers trained on GAN images drop to near-random performance on diffusion outputs (Corvi et al., 2023; Ojha et al., 2023).",
    },
    {
      num: "02", color: C.purple, head: "Writing Quality",
      body: "Llama 3.1 produces grammatically correct, topically coherent posts. Keyword filters and simple language models find nothing anomalous.",
    },
    {
      num: "03", color: C.amber, head: "Conversational Depth",
      body: "The bot sustains coherent multi-turn conversations, recalls prior context, and never breaks persona — indistinguishable from a human in a DM exchange.",
    },
  ];

  points.forEach(({ num, color, head, body }, i) => {
    const y = 1.12 + i * 1.3;
    s.addShape(pres.ShapeType.rect, {
      x: 0.45, y, w: 0.56, h: 0.56,
      fill: { color }, line: { color, width: 0 },
    });
    s.addText(num, {
      x: 0.45, y, w: 0.56, h: 0.56,
      fontSize: 14, bold: true, color: C.bg, fontFace: "Calibri",
      align: "center", valign: "middle", margin: 0,
    });
    s.addText(head, {
      x: 1.15, y: y + 0.02, w: 3.5, h: 0.4,
      fontSize: 15.5, bold: true, color, fontFace: "Calibri", margin: 0,
    });
    s.addText(body, {
      x: 1.15, y: y + 0.44, w: 8.4, h: 0.75,
      fontSize: 13, color: C.text, fontFace: "Calibri", margin: 0,
    });
  });

  // Bottom callout
  s.addShape(pres.ShapeType.rect, {
    x: 0.45, y: 5.06, w: 9.1, h: 0.37,
    fill: { color: C.card }, line: { color: C.faint, width: 0.75 },
  });
  s.addText('“The remaining signals are statistical and behavioural, not perceptual.”', {
    x: 0.45, y: 5.06, w: 9.1, h: 0.37,
    fontSize: 12.5, italic: true, color: C.muted, fontFace: "Calibri",
    align: "center", valign: "middle", margin: 0,
  });
}

// ─── SLIDE 10 — CLOSING THE LOOP ─────────────────────────────────────────────
{
  const s = slide();

  s.addText("How Detectable Are Our Own Bots?", {
    x: 0.5, y: 0.28, w: 9.2, h: 0.62,
    fontSize: 30, bold: true, color: C.white, fontFace: "Calibri",
    align: "left", margin: 0,
  });

  const bullets = [
    "The BiLSTM detector is integrated directly into the simulator",
    "After a bot accumulates posts, its metadata + post history is passed to the classifier",
    "Result: most generated bots are flagged with >90% bot confidence",
    "Why? Metadata ratios do not match the Cresci-2017 training distribution",
    "The classifier was trained on 2017-era bots — different statistical fingerprint than AI-generated content",
    "Detection degrades over time — this is expected and honest",
  ];

  s.addText(
    bullets.map((t, i) => ({
      text: t,
      options: { bullet: { type: "bullet" }, breakLine: i < bullets.length - 1, paraSpaceAfter: 7 },
    })),
    {
      x: 0.55, y: 1.1, w: 9.1, h: 3.5,
      fontSize: 14.5, color: C.text, fontFace: "Calibri",
      align: "left", valign: "top",
    }
  );

  // Takeaway box
  s.addShape(pres.ShapeType.rect, {
    x: 0.45, y: 4.72, w: 9.1, h: 0.7,
    fill: { color: "0d1526" }, line: { color: C.blue, width: 1.5 },
  });
  s.addText([
    { text: "“The classifier and the generator are in an adversarial co-evolutionary loop.  ", options: { italic: true, color: C.blue } },
    { text: "Right now, the generator is moving faster.”", options: { italic: true, color: C.blue } },
  ], {
    x: 0.5, y: 4.75, w: 9.0, h: 0.65,
    fontSize: 13, fontFace: "Calibri",
    align: "center", valign: "middle", margin: 0,
  });
}

// ─── SLIDE 11 — CONCLUSIONS ──────────────────────────────────────────────────
{
  const s = slide();

  s.addText("Key Findings", {
    x: 0.5, y: 0.28, w: 9.2, h: 0.62,
    fontSize: 30, bold: true, color: C.white, fontFace: "Calibri",
    align: "left", margin: 0,
  });

  // Left — What we showed
  s.addShape(pres.ShapeType.rect, {
    x: 0.4, y: 1.1, w: 4.5, h: 4.2,
    fill: { color: C.card }, line: { color: C.green, width: 1.5 },
  });
  s.addShape(pres.ShapeType.rect, {
    x: 0.4, y: 1.1, w: 4.5, h: 0.05,
    fill: { color: C.green }, line: { color: C.green, width: 0 },
  });
  s.addText("What we showed", {
    x: 0.55, y: 1.18, w: 4.2, h: 0.38,
    fontSize: 14, bold: true, color: C.green, fontFace: "Calibri", margin: 0,
  });
  s.addText(
    [
      { text: "A compact BiLSTM + sentence-embedding model exceeds published baselines on Cresci-2017 (99.2% accuracy)", options: { bullet: { type: "bullet" }, breakLine: true, paraSpaceAfter: 10 } },
      { text: "Open-source generative models produce all layers of a fake identity — text, image, video, conversation — on consumer hardware", options: { bullet: { type: "bullet" }, breakLine: true, paraSpaceAfter: 10 } },
      { text: "Perceptual detection of AI-generated bots is increasingly unreliable; statistical and behavioural signals remain informative", options: { bullet: { type: "bullet" }, paraSpaceAfter: 10 } },
    ],
    {
      x: 0.55, y: 1.62, w: 4.2, h: 3.55,
      fontSize: 13, color: C.text, fontFace: "Calibri", valign: "top",
    }
  );

  // Right — Limitations
  s.addShape(pres.ShapeType.rect, {
    x: 5.1, y: 1.1, w: 4.5, h: 4.2,
    fill: { color: C.card }, line: { color: C.amber, width: 1.5 },
  });
  s.addShape(pres.ShapeType.rect, {
    x: 5.1, y: 1.1, w: 4.5, h: 0.05,
    fill: { color: C.amber }, line: { color: C.amber, width: 0 },
  });
  s.addText("Limitations & future work", {
    x: 5.25, y: 1.18, w: 4.2, h: 0.38,
    fontSize: 14, bold: true, color: C.amber, fontFace: "Calibri", margin: 0,
  });
  s.addText(
    [
      { text: "Cresci-2017 has temporal sampling bias — cross-dataset evaluation is the natural next step", options: { bullet: { type: "bullet" }, breakLine: true, paraSpaceAfter: 10 } },
      { text: "The detector predates modern AI-generated bots — retraining on synthetic data would likely improve detection", options: { bullet: { type: "bullet" }, breakLine: true, paraSpaceAfter: 10 } },
      { text: "Video quality and generation speed will improve rapidly (Sora, Runway Gen-3, Kling AI)", options: { bullet: { type: "bullet" }, paraSpaceAfter: 10 } },
    ],
    {
      x: 5.25, y: 1.62, w: 4.2, h: 3.55,
      fontSize: 13, color: C.text, fontFace: "Calibri", valign: "top",
    }
  );
}

// ─── SLIDE 12 — THANK YOU ────────────────────────────────────────────────────
{
  const s = slide();

  // Background circles
  s.addShape(pres.ShapeType.ellipse, {
    x: -1.2, y: -1.2, w: 4.5, h: 4.5,
    fill: { color: C.blueDeep, transparency: 55 },
    line: { color: C.blueDeep, width: 0 },
  });
  s.addShape(pres.ShapeType.ellipse, {
    x: 8.2, y: 3.2, w: 3.5, h: 3.5,
    fill: { color: C.blueDark, transparency: 65 },
    line: { color: C.blueDark, width: 0 },
  });

  s.addText("Thank You", {
    x: 0.5, y: 1.15, w: 9, h: 1.0,
    fontSize: 50, bold: true, color: C.white, fontFace: "Calibri",
    align: "center", margin: 0,
  });
  s.addText("Questions welcome", {
    x: 0.5, y: 2.12, w: 9, h: 0.48,
    fontSize: 21, color: C.blue, fontFace: "Calibri",
    align: "center", margin: 0,
  });

  // Divider
  s.addShape(pres.ShapeType.rect, {
    x: 3.0, y: 2.78, w: 4, h: 0.025,
    fill: { color: C.faint }, line: { color: C.faint, width: 0 },
  });

  s.addText([
    { text: "Dissertation:  ", options: { bold: true, color: C.muted } },
    { text: "Social Media Bots in the Age of Generative AI", options: { color: C.text } },
  ], {
    x: 0.8, y: 2.95, w: 8.4, h: 0.42,
    fontSize: 13, fontFace: "Calibri", align: "center", valign: "middle", margin: 0,
  });
  s.addText([
    { text: "Models:  ", options: { bold: true, color: C.muted } },
    { text: "Llama 3.1 8B  ·  Dreamshaper-8  ·  LTX-Video  ·  all-MiniLM-L6-v2", options: { color: C.text } },
  ], {
    x: 0.8, y: 3.37, w: 8.4, h: 0.42,
    fontSize: 13, fontFace: "Calibri", align: "center", valign: "middle", margin: 0,
  });

  s.addText("Murariu Tudor Cristian  ·  Babeș-Bolyai University  ·  2025", {
    x: 0.5, y: 4.9, w: 9, h: 0.38,
    fontSize: 12, color: C.muted, fontFace: "Calibri",
    align: "center", margin: 0,
  });
}

// ─── SLIDE 13 — DEMO ─────────────────────────────────────────────────────────
{
  const s = slide();

  // Glow behind text (added first = behind)
  s.addShape(pres.ShapeType.ellipse, {
    x: 1.5, y: 0.8, w: 7, h: 3.2,
    fill: { color: C.blueDark, transparency: 82 },
    line: { color: C.blueDark, width: 0 },
  });

  s.addText("DEMO", {
    x: 0, y: 1.1, w: 10, h: 2.8,
    fontSize: 130, bold: true, color: C.white, fontFace: "Calibri",
    align: "center", valign: "middle", margin: 0,
    charSpacing: 20,
  });

  s.addText("BotFarm Simulator — live demonstration", {
    x: 0.5, y: 4.5, w: 9, h: 0.45,
    fontSize: 16, color: C.muted, fontFace: "Calibri",
    align: "center", margin: 0,
  });
}

// ─── Write file ──────────────────────────────────────────────────────────────
const OUT = path.join(
  "C:\\Users\\Tudor\\Desktop\\Masters of High Performance Computing and Big Data Analytics\\an2\\Sem2\\Disertatie",
  "BotFarm_Defense_Presentation.pptx"
);

pres.writeFile({ fileName: OUT })
  .then(() => console.log("OK  →  " + OUT))
  .catch(err => { console.error("ERR:", err); process.exit(1); });
