"""
detector_service.py
-------------------
Loads the trained Multimodal BiLSTM (Experiment 1) and runs inference
on generated bot accounts.

Feature engineering mirrors train_bilstm.py exactly.
The StandardScalers are re-fitted on the full Cresci-2017 dataset at
first call (the saved .pt checkpoint does not include scaler state).
"""
import os
from datetime import datetime

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler

# ── Paths (relative to this file: webapp/backend/services/) ──────────────────
_HERE            = os.path.dirname(os.path.abspath(__file__))
BOT_DETECTION    = os.path.abspath(os.path.join(_HERE, "..", "..", "..", "..", "bot-detection"))
MODEL_PATH       = os.path.join(BOT_DETECTION, "models", "bilstm_best.pt")
DATA_PATH        = os.path.join(BOT_DETECTION, "data",   "cresci2017.csv")

# ── Feature groups (must match train_bilstm.py) ───────────────────────────────
FEATURE_GROUPS = [
    ["followers_count", "friends_count",  "listed_count",   "ff_ratio"],
    ["statuses_count",  "favourites_count", "statuses_per_day", "favourites_per_day"],
    ["verified",        "default_profile", "default_profile_image", "geo_enabled"],
    ["account_age_days","activity_ratio",  "network_ratio",  "engagement_ratio"],
]
NUMERIC_GROUPS = [0, 1, 3]


# ── Model definition (must match train_bilstm.py) ────────────────────────────
class MultimodalBotDetector(nn.Module):
    def __init__(self, meta_input=4, meta_hidden=128, meta_layers=2,
                 text_dim=384, text_proj=128, dropout=0.3):
        super().__init__()
        self.bilstm = nn.LSTM(
            input_size=meta_input, hidden_size=meta_hidden,
            num_layers=meta_layers, batch_first=True, bidirectional=True,
            dropout=dropout if meta_layers > 1 else 0.0,
        )
        lstm_out = meta_hidden * 2
        self.attention = nn.Sequential(
            nn.Linear(lstm_out, 32), nn.Tanh(), nn.Linear(32, 1)
        )
        self.text_branch = nn.Sequential(
            nn.Linear(text_dim, text_proj), nn.LayerNorm(text_proj),
            nn.ReLU(), nn.Dropout(dropout),
        )
        fused = lstm_out + text_proj
        self.classifier = nn.Sequential(
            nn.Linear(fused, 128), nn.ReLU(),
            nn.Dropout(dropout), nn.Linear(128, 1), nn.Sigmoid(),
        )

    def forward(self, meta_x, text_emb):
        out, _   = self.bilstm(meta_x)
        weights  = torch.softmax(self.attention(out), dim=1)
        meta_rep = (out * weights).sum(dim=1)
        text_rep = self.text_branch(text_emb)
        return self.classifier(torch.cat([meta_rep, text_rep], dim=1)).squeeze(-1)


# ── Lazy globals ──────────────────────────────────────────────────────────────
_model   = None
_scalers = None
_device  = None


def _load():
    global _model, _scalers, _device
    if _model is not None:
        return

    _device = "cuda" if torch.cuda.is_available() else "cpu"

    _model = MultimodalBotDetector()
    state  = torch.load(MODEL_PATH, map_location=_device, weights_only=True)
    _model.load_state_dict(state)
    _model.to(_device)
    _model.eval()

    # Re-fit scalers on full dataset (approximation — scalers were not saved)
    df      = pd.read_csv(DATA_PATH, low_memory=False)
    _scalers = {}
    for g_idx, cols in enumerate(FEATURE_GROUPS):
        if g_idx in NUMERIC_GROUPS:
            mat = np.zeros((len(df), len(cols)), dtype=np.float32)
            for j, col in enumerate(cols):
                if col in df.columns:
                    mat[:, j] = df[col].fillna(0).clip(lower=0).values
            mat = np.log1p(mat)
            sc  = StandardScaler().fit(mat)
            _scalers[f"group_{g_idx}"] = sc

    print(f"[Detector] Ready on {_device}. Scalers fitted on {len(df):,} accounts.")


def _build_features(bot, post_texts: list):
    """Return (meta_seq [1,4,4], text_emb [1,384]) tensors for a single bot."""
    age = max(1, (datetime.utcnow() - bot.created_at).days)

    row = {
        "followers_count":       float(bot.followers_count),
        "friends_count":         float(bot.friends_count),
        "listed_count":          float(bot.listed_count),
        "ff_ratio":              bot.followers_count / (bot.friends_count + 1),
        "statuses_count":        float(bot.statuses_count),
        "favourites_count":      float(bot.favourites_count),
        "statuses_per_day":      bot.statuses_count  / age,
        "favourites_per_day":    bot.favourites_count / age,
        "verified":              float(bot.verified),
        "default_profile":       float(bot.default_profile),
        "default_profile_image": float(bot.default_profile_image),
        "geo_enabled":           float(bot.geo_enabled),
        "account_age_days":      float(age),
        "activity_ratio":        bot.statuses_count  / (bot.favourites_count + 1),
        "network_ratio":         bot.followers_count / (bot.listed_count + 1),
        "engagement_ratio":      bot.listed_count    / (bot.followers_count + 1),
    }

    seqs = []
    for g_idx, cols in enumerate(FEATURE_GROUPS):
        mat = np.array([[row.get(c, 0.0) for c in cols]], dtype=np.float32)
        if g_idx in NUMERIC_GROUPS:
            mat = np.log1p(np.clip(mat, 0, None))
            key = f"group_{g_idx}"
            if key in _scalers:
                mat = _scalers[key].transform(mat).astype(np.float32)
        seqs.append(mat)
    meta_seq = np.stack(seqs, axis=1)   # (1, 4, 4)

    # Text embedding from post content
    if post_texts:
        try:
            from sentence_transformers import SentenceTransformer
            st   = SentenceTransformer("all-MiniLM-L6-v2")
            embs = st.encode(post_texts[:50], convert_to_numpy=True,
                             show_progress_bar=False)
            text_emb = embs.mean(axis=0, keepdims=True)
        except Exception:
            text_emb = np.zeros((1, 384), dtype=np.float32)
    else:
        text_emb = np.zeros((1, 384), dtype=np.float32)

    return meta_seq, text_emb


def detect_bot(bot, post_texts: list) -> tuple:
    """Run the BiLSTM detector. Returns (score: float, label: str)."""
    _load()
    meta_seq, text_emb = _build_features(bot, post_texts)

    with torch.no_grad():
        score = _model(
            torch.FloatTensor(meta_seq).to(_device),
            torch.FloatTensor(text_emb).to(_device),
        ).item()

    return round(score, 4), "bot" if score >= 0.5 else "human"
