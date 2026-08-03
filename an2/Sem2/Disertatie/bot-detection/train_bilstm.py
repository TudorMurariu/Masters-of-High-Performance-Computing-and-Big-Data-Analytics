"""
train_bilstm.py  --  Multimodal Bot Detection
----------------------------------------------
Trains a two-branch bidirectional LSTM that fuses account metadata
and tweet-text embeddings for bot/human classification.

  Metadata branch  : BiLSTM + self-attention over 4 feature groups  -> 256-d
  Text branch      : linear projection of 384-d sentence embedding  -> 128-d
  Fusion           : concatenate [256, 128] -> classifier -> binary output

Inputs
------
  data/cresci2017.csv        - account metadata + labels
  data/text_embeddings.npy   - per-account 384-d sentence embeddings

Outputs
-------
  models/bilstm_best.pt
  results/metrics.json
  results/training_curves.{png,pdf}
  results/confusion_matrix.{png,pdf}
  results/class_distribution.{png,pdf}
  results/feature_distributions.{png,pdf}
  results/binary_features.{png,pdf}
  results/tweet_coverage.{png,pdf}
  results/embedding_pca.{png,pdf}

Usage
-----
    python train_bilstm.py
    python train_bilstm.py --epochs 30 --batch_size 64
"""

import argparse, json, os, sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, f1_score, classification_report, confusion_matrix,
)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

SEED = 42
torch.manual_seed(SEED)
np.random.seed(SEED)

# ── Feature groups (4 timesteps x 4 features each) ───────────────────────────
FEATURE_GROUPS = [
    # t=0  Network scale
    ["followers_count", "friends_count", "listed_count", "ff_ratio"],
    # t=1  Activity scale
    ["statuses_count", "favourites_count", "statuses_per_day", "favourites_per_day"],
    # t=2  Profile flags  (binary -- no log / normalisation)
    ["verified", "default_profile", "default_profile_image", "geo_enabled"],
    # t=3  Derived ratios
    ["account_age_days", "activity_ratio", "network_ratio", "engagement_ratio"],
]
NUMERIC_GROUPS = [0, 1, 3]
BINARY_GROUPS  = [2]


# ── Dataset ───────────────────────────────────────────────────────────────────

class CresciDataset(Dataset):
    def __init__(self, meta_seq: np.ndarray, text_emb: np.ndarray, labels: np.ndarray):
        self.meta = torch.FloatTensor(meta_seq)
        self.text = torch.FloatTensor(text_emb)
        self.y    = torch.FloatTensor(labels)

    def __len__(self):
        return len(self.y)

    def __getitem__(self, i):
        return self.meta[i], self.text[i], self.y[i]


# ── Model ─────────────────────────────────────────────────────────────────────

class MultimodalBotDetector(nn.Module):
    """
    Metadata branch  : BiLSTM(4 steps, 4 features) -> self-attention -> 256-d
    Text branch      : Linear(384 -> text_proj) + LayerNorm + ReLU  -> 128-d
    Fusion           : concat(256 + 128 = 384) -> MLP -> sigmoid
    """

    def __init__(
        self,
        meta_input  : int   = 4,
        meta_hidden : int   = 128,
        meta_layers : int   = 2,
        text_dim    : int   = 384,
        text_proj   : int   = 128,
        dropout     : float = 0.3,
    ):
        super().__init__()

        # Metadata branch
        self.bilstm = nn.LSTM(
            input_size    = meta_input,
            hidden_size   = meta_hidden,
            num_layers    = meta_layers,
            batch_first   = True,
            bidirectional = True,
            dropout       = dropout if meta_layers > 1 else 0.0,
        )
        lstm_out = meta_hidden * 2      # 256

        self.attention = nn.Sequential(
            nn.Linear(lstm_out, 32),
            nn.Tanh(),
            nn.Linear(32, 1),
        )

        # Text branch
        self.text_branch = nn.Sequential(
            nn.Linear(text_dim, text_proj),
            nn.LayerNorm(text_proj),
            nn.ReLU(),
            nn.Dropout(dropout),
        )

        # Fusion classifier
        fused = lstm_out + text_proj    # 384
        self.classifier = nn.Sequential(
            nn.Linear(fused, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, 1),
            nn.Sigmoid(),
        )

    def forward(self, meta_x: torch.Tensor, text_emb: torch.Tensor) -> torch.Tensor:
        lstm_out, _ = self.bilstm(meta_x)
        weights     = torch.softmax(self.attention(lstm_out), dim=1)
        meta_repr   = (lstm_out * weights).sum(dim=1)
        text_repr   = self.text_branch(text_emb)
        fused       = torch.cat([meta_repr, text_repr], dim=1)
        return self.classifier(fused).squeeze(-1)


# ── Feature matrix ────────────────────────────────────────────────────────────

def build_feature_matrix(df: pd.DataFrame, scalers=None, fit: bool = False):
    new_scalers = {} if fit else (scalers or {})
    seqs = []
    for g_idx, cols in enumerate(FEATURE_GROUPS):
        mat = np.zeros((len(df), len(cols)), dtype=np.float32)
        for j, col in enumerate(cols):
            if col in df.columns:
                mat[:, j] = df[col].fillna(0).values.astype(np.float32)
        if g_idx in NUMERIC_GROUPS:
            mat = np.log1p(np.clip(mat, 0, None))
            key = f"group_{g_idx}"
            if fit:
                sc = StandardScaler()
                mat = sc.fit_transform(mat).astype(np.float32)
                new_scalers[key] = sc
            elif key in new_scalers:
                mat = new_scalers[key].transform(mat).astype(np.float32)
        seqs.append(mat)
    return np.stack(seqs, axis=1), new_scalers   # (N, 4, 4)


def f1_macro(y_true, y_pred):
    return f1_score(y_true, y_pred, average="macro", zero_division=0)


# ── EDA plots ─────────────────────────────────────────────────────────────────

def plot_eda(df: pd.DataFrame, embeddings: np.ndarray, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    plt.rcParams.update({"font.size": 11})
    C = {"Human": "#4C72B0", "Bot": "#DD8452"}

    # 1. Class distribution
    fig, ax = plt.subplots(figsize=(6, 4))
    counts = df["label"].value_counts().sort_index()
    bars = ax.bar(["Human", "Bot"], counts.values,
                  color=[C["Human"], C["Bot"]], edgecolor="white")
    for bar, v in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 60,
                f"{v:,}", ha="center", va="bottom", fontsize=10)
    ax.set_ylabel("Accounts")
    ax.set_title("Class Distribution -- Cresci-2017")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(out_dir, f"class_distribution.{ext}"), dpi=150)
    plt.close(fig)
    print("[OK] class_distribution")

    # 2. Numeric feature distributions
    feats = ["followers_count", "friends_count", "statuses_count",
             "ff_ratio", "statuses_per_day"]
    fig, axes = plt.subplots(1, len(feats), figsize=(18, 4))
    for ax, feat in zip(axes, feats):
        for lbl, name in [(0, "Human"), (1, "Bot")]:
            vals = np.log1p(df.loc[df["label"]==lbl, feat].fillna(0).clip(lower=0))
            ax.hist(vals, bins=40, alpha=0.6, label=name,
                    color=C[name], edgecolor="none")
        ax.set_title(feat.replace("_", " "), fontsize=9)
        ax.set_xlabel("log(1+x)")
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Count")
    axes[-1].legend(title="Class", fontsize=8)
    fig.suptitle("Numeric Feature Distributions by Class", y=1.01)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(out_dir, f"feature_distributions.{ext}"),
                    dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("[OK] feature_distributions")

    # 3. Binary flags
    bin_cols = ["verified", "default_profile", "default_profile_image", "geo_enabled"]
    fig, axes = plt.subplots(1, 4, figsize=(14, 4))
    for ax, col in zip(axes, bin_cols):
        for lbl, name in [(0, "Human"), (1, "Bot")]:
            sub  = df[df["label"] == lbl]
            rate = sub[col].mean() if col in df.columns else 0.0
            ax.bar(name, rate, color=C[name], edgecolor="white")
        ax.set_ylim(0, 1)
        ax.set_title(col.replace("_", " "), fontsize=9)
        ax.set_ylabel("Proportion")
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Binary Profile Flags by Class", y=1.01)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(out_dir, f"binary_features.{ext}"),
                    dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("[OK] binary_features")

    # 4. Tweet coverage per category
    if "category" in df.columns:
        has_emb = (np.abs(embeddings).sum(axis=1) > 0)
        tmp = df.copy(); tmp["has_embed"] = has_emb
        coverage = tmp.groupby("category")["has_embed"].mean().sort_values()
        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.barh(coverage.index, coverage.values * 100,
                       color="#55A868", edgecolor="white")
        for bar, v in zip(bars, coverage.values * 100):
            ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                    f"{v:.0f}%", va="center", fontsize=9)
        ax.set_xlabel("Users with tweet embeddings (%)")
        ax.set_title("Tweet Coverage by Category")
        ax.set_xlim(0, 120)
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        for ext in ("png", "pdf"):
            fig.savefig(os.path.join(out_dir, f"tweet_coverage.{ext}"),
                        dpi=150, bbox_inches="tight")
        plt.close(fig)
        print("[OK] tweet_coverage")

    # 5. PCA of text embeddings
    nonzero = np.abs(embeddings).sum(axis=1) > 0
    if nonzero.sum() > 100:
        from sklearn.decomposition import PCA
        idx = np.where(nonzero)[0]
        rng = np.random.default_rng(SEED)
        sample = rng.choice(idx, size=min(3000, len(idx)), replace=False)
        pca    = PCA(n_components=2, random_state=SEED)
        coords = pca.fit_transform(embeddings[sample])
        labels = df["label"].values[sample]

        fig, ax = plt.subplots(figsize=(8, 6))
        for lbl, name in [(0, "Human"), (1, "Bot")]:
            m = labels == lbl
            ax.scatter(coords[m, 0], coords[m, 1], c=C[name],
                       label=name, alpha=0.4, s=12, linewidths=0)
        ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)")
        ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)")
        ax.set_title("PCA of Mean Tweet Sentence Embeddings")
        ax.legend(title="Class", markerscale=2)
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        for ext in ("png", "pdf"):
            fig.savefig(os.path.join(out_dir, f"embedding_pca.{ext}"), dpi=150)
        plt.close(fig)
        print("[OK] embedding_pca")


# ── Training / eval loops ─────────────────────────────────────────────────────

def train_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss, ys, ps = 0.0, [], []
    for meta_x, text_x, y in loader:
        meta_x, text_x, y = meta_x.to(device), text_x.to(device), y.to(device)
        optimizer.zero_grad()
        pred = model(meta_x, text_x)
        loss = criterion(pred, y)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        total_loss += loss.item() * len(y)
        ys.extend(y.cpu().tolist())
        ps.extend((pred.detach().cpu().numpy() > 0.5).astype(int).tolist())
    n = len(ys)
    return total_loss / n, accuracy_score(ys, ps), f1_macro(ys, ps)


@torch.no_grad()
def eval_epoch(model, loader, criterion, device):
    model.eval()
    total_loss, ys, ps = 0.0, [], []
    for meta_x, text_x, y in loader:
        meta_x, text_x, y = meta_x.to(device), text_x.to(device), y.to(device)
        pred = model(meta_x, text_x)
        total_loss += criterion(pred, y).item() * len(y)
        ys.extend(y.cpu().tolist())
        ps.extend((pred.cpu().numpy() > 0.5).astype(int).tolist())
    n = len(ys)
    return total_loss / n, accuracy_score(ys, ps), f1_macro(ys, ps)


# ── Result plots ──────────────────────────────────────────────────────────────

def plot_curves(history: dict, out_dir: str):
    epochs = range(1, len(history["train_loss"]) + 1)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    ax1.plot(epochs, history["train_loss"], label="Train",     color="#4C72B0")
    ax1.plot(epochs, history["val_loss"],   label="Val",       color="#DD8452", linestyle="--")
    ax1.set_title("Loss"); ax1.set_xlabel("Epoch"); ax1.set_ylabel("BCE Loss")
    ax1.legend(); ax1.spines[["top", "right"]].set_visible(False)

    ax2.plot(epochs, history["train_f1"],  label="Train F1",  color="#4C72B0")
    ax2.plot(epochs, history["val_f1"],    label="Val F1",    color="#DD8452", linestyle="--")
    ax2.plot(epochs, history["train_acc"], label="Train Acc", color="#4C72B0", alpha=0.35, linestyle=":")
    ax2.plot(epochs, history["val_acc"],   label="Val Acc",   color="#DD8452", alpha=0.35, linestyle=":")
    ax2.set_title("F1 Score and Accuracy"); ax2.set_xlabel("Epoch"); ax2.set_ylabel("Score")
    ax2.set_ylim(0.85, 1.01); ax2.legend(fontsize=8)
    ax2.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(out_dir, f"training_curves.{ext}"), dpi=150)
    plt.close(fig)
    print("[OK] training_curves")


def plot_cm(y_true, y_pred, out_dir: str):
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=["Human", "Bot"],
                yticklabels=["Human", "Bot"], ax=ax)
    ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix -- Test Set")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(out_dir, f"confusion_matrix.{ext}"), dpi=150)
    plt.close(fig)
    print("[OK] confusion_matrix")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir",   default="data")
    parser.add_argument("--epochs",     type=int,   default=25)
    parser.add_argument("--batch_size", type=int,   default=64)
    parser.add_argument("--lr",         type=float, default=5e-4)
    parser.add_argument("--hidden",     type=int,   default=128)
    parser.add_argument("--text_proj",  type=int,   default=128)
    parser.add_argument("--dropout",    type=float, default=0.3)
    args = parser.parse_args()

    Path("models").mkdir(exist_ok=True)
    Path("results").mkdir(exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Device : {device}")
    if device.type == "cuda":
        print(f"    GPU    : {torch.cuda.get_device_name(0)}")

    # Load data
    meta_path = os.path.join(args.data_dir, "cresci2017.csv")
    emb_path  = os.path.join(args.data_dir, "text_embeddings.npy")
    if not os.path.exists(meta_path):
        print(f"[!] {meta_path} not found. Run download_data.py first.")
        sys.exit(1)

    print(f"\n[*] Loading data ...")
    df = pd.read_csv(meta_path)
    print(f"    {len(df):,} accounts | {df['label'].value_counts().to_dict()}")

    if os.path.exists(emb_path):
        embeddings = np.load(emb_path).astype(np.float32)
        covered = int((np.abs(embeddings).sum(axis=1) > 0).sum())
        print(f"    Embeddings : {embeddings.shape}  ({covered:,} non-zero)")
    else:
        print(f"    [!] {emb_path} not found -- using zero embeddings.")
        embeddings = np.zeros((len(df), 384), dtype=np.float32)

    # EDA
    print("\n[*] Generating EDA plots ...")
    plot_eda(df, embeddings, "results")

    # Feature matrix and splits
    labels = df["label"].values.astype(np.float32)
    idx    = np.arange(len(df))
    train_idx, temp_idx = train_test_split(
        idx, test_size=0.30, stratify=labels, random_state=SEED)
    val_idx, test_idx   = train_test_split(
        temp_idx, test_size=2/3, stratify=labels[temp_idx], random_state=SEED)

    X_all, scalers = build_feature_matrix(df, fit=True)
    E_all = embeddings

    X_tr, X_va, X_te = X_all[train_idx], X_all[val_idx], X_all[test_idx]
    E_tr, E_va, E_te = E_all[train_idx], E_all[val_idx], E_all[test_idx]
    y_tr, y_va, y_te = labels[train_idx], labels[val_idx], labels[test_idx]

    print(f"\n    Train : {len(y_tr):,} | Val : {len(y_va):,} | Test : {len(y_te):,}")

    class_counts   = np.bincount(y_tr.astype(int))
    sample_weights = (1.0 / class_counts)[y_tr.astype(int)]
    sampler        = WeightedRandomSampler(sample_weights, len(sample_weights), replacement=True)

    train_loader = DataLoader(CresciDataset(X_tr, E_tr, y_tr),
                              batch_size=args.batch_size, sampler=sampler)
    val_loader   = DataLoader(CresciDataset(X_va, E_va, y_va), batch_size=256, shuffle=False)
    test_loader  = DataLoader(CresciDataset(X_te, E_te, y_te), batch_size=256, shuffle=False)

    # Model
    model = MultimodalBotDetector(
        meta_hidden=args.hidden, text_proj=args.text_proj, dropout=args.dropout,
    ).to(device)
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"\n[*] Model : Multimodal BiLSTM+Attention | Params : {n_params:,}")

    criterion = nn.BCELoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="max", factor=0.5, patience=3, verbose=False)

    best_val_f1 = 0.0
    ckpt_path   = "models/bilstm_best.pt"
    history     = {k: [] for k in
                   ["train_loss","val_loss","train_acc","val_acc","train_f1","val_f1"]}

    hdr = (f" {'Epoch':>5}  {'TrLoss':>9}  {'TrAcc':>8}  {'TrF1':>8}"
           f"  {'VaLoss':>9}  {'VaAcc':>8}  {'VaF1':>8}")
    print(f"\n{hdr}\n{'-'*len(hdr)}")

    for epoch in range(1, args.epochs + 1):
        tr_loss, tr_acc, tr_f1 = train_epoch(model, train_loader, criterion, optimizer, device)
        va_loss, va_acc, va_f1 = eval_epoch(model, val_loader,   criterion, device)
        scheduler.step(va_f1)

        for k, v in zip(
            ["train_loss","val_loss","train_acc","val_acc","train_f1","val_f1"],
            [tr_loss, va_loss, tr_acc, va_acc, tr_f1, va_f1]
        ):
            history[k].append(v)

        marker = ""
        if va_f1 > best_val_f1:
            best_val_f1 = va_f1
            torch.save(model.state_dict(), ckpt_path)
            marker = " * best"

        print(f" {epoch:5d}  {tr_loss:9.4f}  {tr_acc:8.4f}  {tr_f1:8.4f}"
              f"  {va_loss:9.4f}  {va_acc:8.4f}  {va_f1:8.4f}{marker}")

    # Evaluate best checkpoint
    print(f"\n[*] Loading best checkpoint (val F1 = {best_val_f1:.4f}) ...")
    model.load_state_dict(torch.load(ckpt_path, map_location=device))
    te_loss, te_acc, te_f1 = eval_epoch(model, test_loader, criterion, device)

    model.eval()
    all_y, all_p = [], []
    with torch.no_grad():
        for meta_x, text_x, y in test_loader:
            preds = (model(meta_x.to(device), text_x.to(device))
                     .cpu().numpy() > 0.5).astype(int)
            all_y.extend(y.numpy().astype(int).tolist())
            all_p.extend(preds.tolist())

    print(f"\n{'='*52}")
    print(f"  Test Accuracy : {te_acc:.4f}")
    print(f"  Test F1-macro : {te_f1:.4f}")
    print(f"{'='*52}")
    print("\nClassification Report:")
    print(classification_report(all_y, all_p, target_names=["Human", "Bot"]))

    metrics = {
        "model":         "Multimodal BiLSTM + Attention",
        "dataset":       "cresci-2017",
        "text_branch":   "all-MiniLM-L6-v2 (frozen)",
        "epochs":        args.epochs,
        "test_accuracy": round(float(te_acc), 4),
        "test_f1_macro": round(float(te_f1), 4),
        "best_val_f1":   round(float(best_val_f1), 4),
        "history":       history,
    }
    with open("results/metrics.json", "w") as fh:
        json.dump(metrics, fh, indent=2)
    print("\n[OK] Metrics saved  -> results/metrics.json")

    plot_curves(history, "results")
    plot_cm(all_y, all_p, "results")
    print("\n[OK] Training complete!")


if __name__ == "__main__":
    main()
