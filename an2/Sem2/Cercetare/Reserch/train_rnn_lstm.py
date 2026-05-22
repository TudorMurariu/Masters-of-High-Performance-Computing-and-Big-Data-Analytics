"""
Standalone training script for RNN and Bi-LSTM fake news classifiers.
Saves trained models and vocabulary to the models/ directory.

Usage:
    python train_rnn_lstm.py              # full training (GPU recommended)
    python train_rnn_lstm.py --quick      # CPU-friendly: smaller model, 5k samples
"""

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
import re
import pickle
import os
import json
from collections import Counter
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report
from tqdm import tqdm
import random

# -- Reproducibility ----------------------------------------------------------─
def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

set_seed(42)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f'Device: {device}')

import sys
QUICK_MODE = '--quick' in sys.argv

if QUICK_MODE:
    print('Running in QUICK MODE (CPU-friendly, ~5–10 min)')
    MAX_VOCAB    = 15_000
    MAX_LEN      = 150     # shorter sequences = much faster LSTM
    BATCH_SIZE   = 128
    NUM_EPOCHS   = 5
    EMBED_DIM    = 64
    HIDDEN_DIM   = 128
    NUM_LAYERS   = 1
    DROPOUT      = 0.3
    LR           = 1e-3
    TRAIN_SUBSET = 2_000   # use 2k samples for fast iteration
else:
    print('Running in FULL MODE (GPU recommended)')
    MAX_VOCAB    = 20_000
    MAX_LEN      = 400
    BATCH_SIZE   = 64
    NUM_EPOCHS   = 8
    EMBED_DIM    = 128
    HIDDEN_DIM   = 256
    NUM_LAYERS   = 2
    DROPOUT      = 0.3
    LR           = 1e-3
    TRAIN_SUBSET = None

# -- Data loading --------------------------------------------------------------
print('\nLoading data...')
fake_df = pd.read_csv('dataset/Fake.csv')
true_df = pd.read_csv('dataset/True.csv')
fake_df['label'] = 0
true_df['label'] = 1

df = pd.concat([fake_df, true_df], ignore_index=True)
df['content'] = df['title'].fillna('') + ' ' + df['text'].fillna('')
df = df[['content', 'label']].dropna().reset_index(drop=True)

# -- Preprocessing ------------------------------------------------------------─
def preprocess(text):
    text = text.lower()
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'[^a-z\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

print('Preprocessing text...')
df['content'] = df['content'].apply(preprocess)

# FIX: drop rows where text is empty after cleaning
before = len(df)
df = df[df['content'].str.len() > 0].reset_index(drop=True)
print(f'Removed {before - len(df)} empty rows. Remaining: {len(df)}')

# -- Train / val / test split --------------------------------------------------
train_texts, tmp_texts, train_labels, tmp_labels = train_test_split(
    df['content'].values, df['label'].values,
    test_size=0.2, random_state=42, stratify=df['label'].values
)
val_texts, test_texts, val_labels, test_labels = train_test_split(
    tmp_texts, tmp_labels,
    test_size=0.5, random_state=42, stratify=tmp_labels
)
if TRAIN_SUBSET and TRAIN_SUBSET < len(train_texts):
    idx = np.random.choice(len(train_texts), TRAIN_SUBSET, replace=False)
    train_texts, train_labels = train_texts[idx], train_labels[idx]
    print(f'Using {TRAIN_SUBSET} training samples (quick mode).')
print(f'Train / Val / Test : {len(train_texts)} / {len(val_texts)} / {len(test_texts)}')

# -- Vocabulary ----------------------------------------------------------------
class Vocabulary:
    def __init__(self, max_vocab=MAX_VOCAB):
        self.max_vocab = max_vocab
        self.word2idx  = {'<PAD>': 0, '<UNK>': 1}
        self.idx2word  = {0: '<PAD>', 1: '<UNK>'}

    def build(self, texts):
        counter = Counter()
        for text in texts:
            counter.update(text.split())
        for word, _ in counter.most_common(self.max_vocab - 2):
            idx = len(self.word2idx)
            self.word2idx[word] = idx
            self.idx2word[idx]  = word

    def encode(self, text):
        return [self.word2idx.get(w, 1) for w in text.split()]

    def __len__(self):
        return len(self.word2idx)

print('Building vocabulary...')
vocab = Vocabulary()
vocab.build(train_texts)
print(f'Vocabulary size: {len(vocab)}')

# -- Dataset ------------------------------------------------------------------─
class FakeNewsDataset(Dataset):
    def __init__(self, texts, labels, vocab, max_len=MAX_LEN):
        self.sequences = []
        self.labels    = []
        for text, label in zip(texts, labels):
            seq = vocab.encode(text)[:max_len]
            if len(seq) > 0:          # FIX: skip zero-length sequences
                self.sequences.append(seq)
                self.labels.append(label)
        self.labels = torch.tensor(self.labels, dtype=torch.long)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.sequences[idx], self.labels[idx]


def collate_fn(batch):
    seqs, labels = zip(*batch)
    lengths = torch.tensor([len(s) for s in seqs], dtype=torch.long)
    max_len = lengths.max().item()
    padded  = torch.zeros(len(seqs), max_len, dtype=torch.long)
    for i, s in enumerate(seqs):
        padded[i, :len(s)] = torch.tensor(s, dtype=torch.long)
    return padded, lengths, torch.stack(labels)


train_ds = FakeNewsDataset(train_texts, train_labels, vocab)
val_ds   = FakeNewsDataset(val_texts,   val_labels,   vocab)
test_ds  = FakeNewsDataset(test_texts,  test_labels,  vocab)

train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,  collate_fn=collate_fn)
val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False, collate_fn=collate_fn)
test_loader  = DataLoader(test_ds,  batch_size=BATCH_SIZE, shuffle=False, collate_fn=collate_fn)
print(f'Batches — train: {len(train_loader)}  val: {len(val_loader)}  test: {len(test_loader)}')

# -- Model definitions --------------------------------------------------------─
class RNNClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim=EMBED_DIM, hidden_dim=HIDDEN_DIM,
                 num_layers=NUM_LAYERS, num_classes=2, dropout=DROPOUT):
        super().__init__()
        self.embedding  = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.rnn        = nn.RNN(embed_dim, hidden_dim, num_layers=num_layers,
                                 batch_first=True,
                                 dropout=dropout if num_layers > 1 else 0,
                                 nonlinearity='tanh')
        self.dropout    = nn.Dropout(dropout)
        self.classifier = nn.Linear(hidden_dim, num_classes)

    def forward(self, x, lengths):
        emb    = self.dropout(self.embedding(x))
        packed = nn.utils.rnn.pack_padded_sequence(
            emb, lengths.cpu(), batch_first=True, enforce_sorted=False)
        _, hidden = self.rnn(packed)
        out = self.dropout(hidden[-1])
        return self.classifier(out)


class LSTMClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim=EMBED_DIM, hidden_dim=HIDDEN_DIM,
                 num_layers=NUM_LAYERS, num_classes=2, dropout=DROPOUT,
                 bidirectional=True):
        super().__init__()
        self.embedding     = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm          = nn.LSTM(embed_dim, hidden_dim, num_layers=num_layers,
                                     batch_first=True,
                                     dropout=dropout if num_layers > 1 else 0,
                                     bidirectional=bidirectional)
        self.dropout       = nn.Dropout(dropout)
        factor             = 2 if bidirectional else 1
        self.classifier    = nn.Linear(hidden_dim * factor, num_classes)
        self.bidirectional = bidirectional

    def forward(self, x, lengths):
        emb    = self.dropout(self.embedding(x))
        packed = nn.utils.rnn.pack_padded_sequence(
            emb, lengths.cpu(), batch_first=True, enforce_sorted=False)
        _, (hidden, _) = self.lstm(packed)
        if self.bidirectional:
            out = torch.cat([hidden[-2], hidden[-1]], dim=1)
        else:
            out = hidden[-1]
        return self.classifier(self.dropout(out))

# -- Training helpers ----------------------------------------------------------
def train_epoch(model, loader, optimiser, criterion):
    model.train()
    total_loss, preds, trues = 0.0, [], []
    for seqs, lengths, labels in tqdm(loader, desc='  train', leave=False):
        seqs, labels = seqs.to(device), labels.to(device)
        optimiser.zero_grad()
        logits = model(seqs, lengths)
        loss   = criterion(logits, labels)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimiser.step()
        total_loss += loss.item()
        preds.extend(logits.argmax(1).cpu().tolist())
        trues.extend(labels.cpu().tolist())
    return total_loss / len(loader), accuracy_score(trues, preds)


def eval_epoch(model, loader, criterion):
    model.eval()
    total_loss, preds, trues = 0.0, [], []
    with torch.no_grad():
        for seqs, lengths, labels in loader:
            seqs, labels = seqs.to(device), labels.to(device)
            logits = model(seqs, lengths)
            total_loss += criterion(logits, labels).item()
            preds.extend(logits.argmax(1).cpu().tolist())
            trues.extend(labels.cpu().tolist())
    return total_loss / len(loader), accuracy_score(trues, preds), preds, trues


def train_model(model, name):
    optimiser = torch.optim.Adam(model.parameters(), lr=LR)
    criterion = nn.CrossEntropyLoss()
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimiser, mode='min', patience=2, factor=0.5)

    history    = {'train_loss': [], 'val_loss': [], 'train_acc': [], 'val_acc': []}
    best_acc   = 0.0
    best_state = None

    print(f'\n{"=" * 60}')
    print(f' Training {name}')
    print(f'{"=" * 60}')

    for epoch in range(1, NUM_EPOCHS + 1):
        tr_loss, tr_acc       = train_epoch(model, train_loader, optimiser, criterion)
        vl_loss, vl_acc, _, _ = eval_epoch(model, val_loader, criterion)
        scheduler.step(vl_loss)

        for k, v in zip(history.keys(), [tr_loss, vl_loss, tr_acc, vl_acc]):
            history[k].append(v)

        if vl_acc > best_acc:
            best_acc  = vl_acc
            best_state = {k: v.clone() for k, v in model.state_dict().items()}

        print(f'  Epoch {epoch:2d}/{NUM_EPOCHS} | '
              f'train loss={tr_loss:.4f} acc={tr_acc:.4f} | '
              f'val   loss={vl_loss:.4f} acc={vl_acc:.4f}')

    model.load_state_dict(best_state)
    print(f'  Best val accuracy: {best_acc:.4f}')
    return history

# -- Train, evaluate, and save each model immediately after it finishes -------
os.makedirs('models', exist_ok=True)
criterion  = nn.CrossEntropyLoss()
all_results = {}

# Save vocab once upfront so it's available even if a model crashes mid-training
with open('models/vocab.pkl', 'wb') as f:
    pickle.dump(vocab, f)
print('Saved: models/vocab.pkl')

for model, name, fname in [
    (RNNClassifier(vocab_size=len(vocab)).to(device),  'RNN',    'rnn_model.pt'),
    (LSTMClassifier(vocab_size=len(vocab)).to(device), 'Bi-LSTM', 'lstm_model.pt'),
]:
    history = train_model(model, name)

    # Evaluate on test set immediately
    _, acc, preds, trues = eval_epoch(model, test_loader, criterion)
    f1 = f1_score(trues, preds, average='macro')

    print(f'\n-- {name} Test Results --')
    print(f'Accuracy={acc:.4f}  F1={f1:.4f}')
    print(classification_report(trues, preds, target_names=['Fake', 'Real']))

    # Save model weights immediately
    torch.save(model.state_dict(), f'models/{fname}')
    print(f'Saved: models/{fname}')

    all_results[name.lower().replace('-', '')] = {
        'test_acc': acc, 'test_f1': f1, 'history': history
    }

# Save combined results JSON
all_results['hyperparams'] = {
    'vocab_size': len(vocab), 'max_len': MAX_LEN, 'embed_dim': EMBED_DIM,
    'hidden_dim': HIDDEN_DIM, 'num_layers': NUM_LAYERS, 'dropout': DROPOUT,
    'batch_size': BATCH_SIZE, 'num_epochs': NUM_EPOCHS, 'lr': LR
}
with open('models/training_results.json', 'w') as f:
    json.dump(all_results, f, indent=2)
print('Saved: models/training_results.json')
