"""
download_data.py
----------------
Downloads the Cresci-2017 Twitter bot-detection dataset and builds
two artefacts used by the training pipeline:

  data/cresci2017.csv        - per-account metadata features + labels
  data/cresci2017_tweets.csv - raw tweet text per account (for EDA)
  data/text_embeddings.npy   - per-account mean sentence embedding (N x 384)

Each category zip inside cresci-2017.csv.zip contains a users.csv
(account metadata) and, where available, a tweets.csv (tweet text).
Sentence embeddings are computed with frozen all-MiniLM-L6-v2 and
averaged across a user's tweets.  Accounts with no tweet data get a
zero vector.

Usage
-----
    python download_data.py
    python download_data.py --output_dir data --skip_embeddings
"""

import argparse, io, os, sys, zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

SEED = 42
MAX_TWEETS_PER_USER = 50

PRIMARY_URL = (
    "https://botometer.osome.iu.edu/bot-repository/datasets/"
    "cresci-2017/cresci-2017.csv.zip"
)

BOT_CATEGORIES = {
    "social_spambots_1", "social_spambots_2", "social_spambots_3",
    "traditional_spambots_1", "traditional_spambots_2",
    "traditional_spambots_3", "traditional_spambots_4", "fake_followers",
}
HUMAN_CATEGORIES = {"genuine_accounts"}
SKIP_CATEGORIES  = {"crowdflower_results"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _find_col(df: pd.DataFrame, candidates: list) -> str | None:
    """Return the first matching column name (case-insensitive)."""
    lower_map = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None


# ── Download and extract ──────────────────────────────────────────────────────

def download_and_extract(url: str):
    """
    Download the outer zip and extract users.csv + tweets.csv for every
    labelled category.  Returns (users_df, tweets_df).
    """
    print(f"[*] Downloading Cresci-2017 ...")
    r = requests.get(url, timeout=300)
    r.raise_for_status()
    print("    Download complete.")

    user_frames, tweet_frames = [], []

    with zipfile.ZipFile(io.BytesIO(r.content)) as outer:
        inner_zips = sorted(n for n in outer.namelist() if n.endswith(".csv.zip"))
        print(f"    Found {len(inner_zips)} category zips.\n")

        for inner_name in inner_zips:
            base = inner_name.split("/")[-1].replace(".csv.zip", "")

            if base in SKIP_CATEGORIES:
                continue
            if base in BOT_CATEGORIES:
                label, label_str = 1, "bot"
            elif base in HUMAN_CATEGORIES:
                label, label_str = 0, "human"
            else:
                print(f"    Unknown category: {base} -- skipping.")
                continue

            with outer.open(inner_name) as fh:
                with zipfile.ZipFile(io.BytesIO(fh.read())) as inner:
                    all_files   = inner.namelist()
                    user_files  = [f for f in all_files
                                   if "user" in f.lower() and f.endswith(".csv")]
                    tweet_files = [f for f in all_files
                                   if "tweet" in f.lower() and f.endswith(".csv")]

                    # ── Users ──────────────────────────────────────────────
                    if not user_files:
                        print(f"    {base}: no users.csv -- skipping.")
                        continue
                    with inner.open(user_files[0]) as f:
                        df_u = pd.read_csv(f, low_memory=False)
                        df_u["category"]     = base
                        df_u["account_type"] = label_str
                        user_frames.append(df_u)
                        n_users = len(df_u)

                    # ── Tweets ─────────────────────────────────────────────
                    n_tweets = 0
                    if tweet_files:
                        with inner.open(tweet_files[0]) as f:
                            df_t = pd.read_csv(f, low_memory=False, encoding='latin-1')
                        uid_col  = _find_col(df_t, ["user_id", "userid", "author_id"])
                        text_col = _find_col(df_t, ["text", "full_text", "tweet_text"])
                        if uid_col and text_col:
                            df_t = (df_t[[uid_col, text_col]]
                                    .rename(columns={uid_col: "user_id", text_col: "text"}))
                            df_t["label"] = label
                            tweet_frames.append(df_t)
                            n_tweets = len(df_t)
                        else:
                            print(f"    {base}: tweets.csv has no recognisable text column.")

                    tag = f"{n_tweets:>7,} tweets" if n_tweets else "no tweets.csv"
                    print(f"    {base:<36s}  {n_users:5,} users   {tag}")

    users_df  = pd.concat(user_frames,  ignore_index=True) if user_frames  else None
    tweets_df = pd.concat(tweet_frames, ignore_index=True) if tweet_frames else None
    return users_df, tweets_df


# ── Feature engineering ───────────────────────────────────────────────────────

def engineer_metadata(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Label
    df["label"] = df["account_type"].apply(
        lambda x: 1 if str(x).lower() == "bot" else 0
    )

    # Account age relative to dataset collection date
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
        ref = pd.Timestamp("2017-01-01", tz="UTC")
        df["account_age_days"] = (ref - df["created_at"]).dt.days.clip(lower=1)
    else:
        df["account_age_days"] = 365

    # Raw counts -- fill missing with 0
    for col in ["followers_count", "friends_count", "statuses_count",
                "favourites_count", "listed_count"]:
        df[col] = (df[col].fillna(0).clip(lower=0)
                   if col in df.columns
                   else pd.Series(0, index=df.index))

    # First-order ratios
    df["ff_ratio"]           = df["followers_count"] / (df["friends_count"]   + 1)
    df["statuses_per_day"]   = df["statuses_count"]  / df["account_age_days"]
    df["favourites_per_day"] = df["favourites_count"] / df["account_age_days"]

    # Second-order ratios (used in derived feature group)
    df["activity_ratio"]    = df["statuses_count"]  / (df["favourites_count"] + 1)
    df["network_ratio"]     = df["followers_count"] / (df["listed_count"]     + 1)
    df["engagement_ratio"]  = df["listed_count"]    / (df["followers_count"]  + 1)

    # Binary profile flags
    for col in ["verified", "default_profile", "default_profile_image", "geo_enabled"]:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)
        else:
            df[col] = 0

    return df


# ── Sentence embeddings ───────────────────────────────────────────────────────

def compute_embeddings(users_df: pd.DataFrame, tweets_df, output_dir: str) -> np.ndarray:
    """
    Compute per-user average sentence embeddings using all-MiniLM-L6-v2.
    Returns an (N, 384) float32 array; rows with no tweet data are zeros.
    """
    import torch
    from sentence_transformers import SentenceTransformer

    N, DIM = len(users_df), 384
    embeddings = np.zeros((N, DIM), dtype=np.float32)

    if tweets_df is None or len(tweets_df) == 0:
        print("[!] No tweet data found -- using zero embeddings.")
        return embeddings

    # Map user_id -> row index in users_df
    uid_col = _find_col(users_df, ["id", "user_id", "userid"])
    if uid_col is None:
        print("[!] No user-ID column in users_df -- using zero embeddings.")
        return embeddings

    uid_to_idx = {uid: i for i, uid in enumerate(users_df[uid_col])}
    grouped    = tweets_df.groupby("user_id")["text"].apply(list).to_dict()
    matched    = [uid for uid in grouped if uid in uid_to_idx]
    print(f"[*] {len(matched):,} / {N:,} users matched to tweet data.")

    # Build flat list of tweets with back-reference to user row
    flat_texts, lengths, row_idxs = [], [], []
    for uid in matched:
        texts = [str(t).strip() for t in grouped[uid]
                 if pd.notna(t) and str(t).strip()][:MAX_TWEETS_PER_USER]
        if not texts:
            continue
        flat_texts.extend(texts)
        lengths.append(len(texts))
        row_idxs.append(uid_to_idx[uid])

    total = len(flat_texts)
    print(f"[*] Encoding {total:,} tweets with all-MiniLM-L6-v2 ...")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"    Device: {device}")
    st_model = SentenceTransformer("all-MiniLM-L6-v2", device=device)

    BATCH = 512
    all_embs = []
    for i in range(0, total, BATCH):
        batch = flat_texts[i : i + BATCH]
        with torch.no_grad():
            emb = st_model.encode(batch, convert_to_numpy=True, show_progress_bar=False)
        all_embs.append(emb)
        pct = (i + len(batch)) / total * 100
        print(f"    {i + len(batch):>7,} / {total:,}  ({pct:.1f}%)", end="\r")
    print()

    stacked = np.vstack(all_embs)   # (total_tweets, 384)

    ptr = 0
    for row_idx, length in zip(row_idxs, lengths):
        embeddings[row_idx] = stacked[ptr : ptr + length].mean(axis=0)
        ptr += length

    covered = int((np.abs(embeddings).sum(axis=1) > 0).sum())
    print(f"[OK] {covered:,} / {N:,} users have non-zero embeddings.")
    return embeddings


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Download and prepare Cresci-2017")
    parser.add_argument("--output_dir",      default="data")
    parser.add_argument("--skip_embeddings", action="store_true",
                        help="Skip sentence embedding step (metadata only)")
    args = parser.parse_args()

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    meta_path   = os.path.join(args.output_dir, "cresci2017.csv")
    emb_path    = os.path.join(args.output_dir, "text_embeddings.npy")
    tweets_path = os.path.join(args.output_dir, "cresci2017_tweets.csv")

    need_emb = not args.skip_embeddings and not os.path.exists(emb_path)

    if os.path.exists(meta_path) and not need_emb:
        print(f"[OK] Data already at {args.output_dir}/ -- delete files to re-run.")
        df = pd.read_csv(meta_path)
        print(f"    {len(df):,} accounts | {df['label'].value_counts().to_dict()}")
        return

    # Re-use existing metadata if we only need to redo embeddings
    if os.path.exists(meta_path) and need_emb:
        print("[*] Metadata exists; computing embeddings only ...")
        users_df  = pd.read_csv(meta_path)
        tweets_df = pd.read_csv(tweets_path) if os.path.exists(tweets_path) else None
    else:
        # Full download
        users_df, tweets_df = download_and_extract(PRIMARY_URL)
        if users_df is None:
            print("[!] Download failed.  Exiting.")
            sys.exit(1)

        print("\n[*] Engineering metadata features ...")
        users_df = engineer_metadata(users_df)
        users_df.to_csv(meta_path, index=False)
        counts = users_df["label"].value_counts()
        print(f"[OK] Metadata saved: {len(users_df):,} accounts | "
              f"Human={counts.get(0,0):,}  Bot={counts.get(1,0):,}")

        if tweets_df is not None:
            tweets_df.to_csv(tweets_path, index=False)
            print(f"[OK] Tweets saved:   {len(tweets_df):,} tweets")

    # Embeddings
    if not args.skip_embeddings:
        print()
        emb = compute_embeddings(users_df, tweets_df, args.output_dir)
        np.save(emb_path, emb)
        print(f"[OK] Embeddings saved: shape={emb.shape}  path={emb_path}")
    else:
        print("[*] Skipping embedding computation (--skip_embeddings).")


if __name__ == "__main__":
    main()
