"""
Standalone BERT fine-tuning script for fake news classification.
Saves the model and tokenizer to models/bert_model/ and updates
models/training_results.json alongside the RNN/LSTM entries.
"""

import sys, os, json, random
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import (BertTokenizerFast, BertForSequenceClassification,
                          get_linear_schedule_with_warmup)
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report
from tqdm import tqdm

# -- Reproducibility ----------------------------------------------------------
def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

set_seed(42)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f'Device: {device}')
if device.type == 'cuda':
    print(f'GPU: {torch.cuda.get_device_name(0)}')

QUICK_MODE = '--quick' in sys.argv

if QUICK_MODE:
    print('Running in QUICK MODE (CPU-friendly, ~20-40 min)')
    TRAIN_SUBSET = 2_000
    NUM_EPOCHS   = 2
    MAX_LEN      = 128
    BATCH_SIZE   = 16
    LR           = 2e-5
else:
    print('Running in FULL MODE (GPU recommended)')
    TRAIN_SUBSET = 12_000
    NUM_EPOCHS   = 3
    MAX_LEN      = 256
    BATCH_SIZE   = 16
    LR           = 2e-5

MODEL_NAME      = 'bert-base-uncased'
MODEL_SAVE_PATH = 'models/bert_model'
os.makedirs(MODEL_SAVE_PATH, exist_ok=True)

# -- Data loading -------------------------------------------------------------
print('\nLoading data...')
fake_df = pd.read_csv('dataset/Fake.csv')
true_df = pd.read_csv('dataset/True.csv')
fake_df['label'] = 0
true_df['label'] = 1

df = pd.concat([fake_df, true_df], ignore_index=True)
df['content'] = df['title'].fillna('') + ' ' + df['text'].fillna('')
df = df[['content', 'label']].dropna().reset_index(drop=True)
print(f'Total samples: {len(df)}')

# -- Train / val / test split (same seed as RNN/LSTM scripts) -----------------
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
    train_texts  = train_texts[idx]
    train_labels = train_labels[idx]
    print(f'Using {TRAIN_SUBSET} training samples.')

print(f'Train / Val / Test: {len(train_texts)} / {len(val_texts)} / {len(test_texts)}')

# -- Tokenizer ----------------------------------------------------------------
print('\nLoading tokenizer...')
tokenizer = BertTokenizerFast.from_pretrained(MODEL_NAME)

# -- Dataset ------------------------------------------------------------------
class FakeNewsBertDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len=MAX_LEN):
        self.encodings = tokenizer(
            list(texts),
            max_length=max_len,
            truncation=True,
            padding='max_length',
            return_tensors='pt'
        )
        self.labels = torch.tensor(labels, dtype=torch.long)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return {
            'input_ids':      self.encodings['input_ids'][idx],
            'attention_mask': self.encodings['attention_mask'][idx],
            'label':          self.labels[idx]
        }

print('Encoding training set...')
train_ds = FakeNewsBertDataset(train_texts, train_labels, tokenizer)
print('Encoding validation set...')
val_ds   = FakeNewsBertDataset(val_texts,   val_labels,   tokenizer)
print('Encoding test set...')
test_ds  = FakeNewsBertDataset(test_texts,  test_labels,  tokenizer)

train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False)
test_loader  = DataLoader(test_ds,  batch_size=BATCH_SIZE, shuffle=False)
print(f'Batches -- train: {len(train_loader)}  val: {len(val_loader)}  test: {len(test_loader)}')

# -- Model --------------------------------------------------------------------
print('\nLoading pre-trained BERT...')
model = BertForSequenceClassification.from_pretrained(
    MODEL_NAME, num_labels=2,
    output_attentions=False, output_hidden_states=False
).to(device)

total_params = sum(p.numel() for p in model.parameters())
print(f'Total parameters: {total_params:,}')

# -- Training helpers ---------------------------------------------------------
def train_epoch(model, loader, optimiser, scheduler):
    model.train()
    total_loss, all_preds, all_labels = 0.0, [], []
    for batch in tqdm(loader, desc='  train', leave=False):
        input_ids      = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels         = batch['label'].to(device)
        optimiser.zero_grad()
        outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
        outputs.loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimiser.step()
        scheduler.step()
        total_loss += outputs.loss.item()
        all_preds.extend(outputs.logits.argmax(1).cpu().tolist())
        all_labels.extend(labels.cpu().tolist())
    return total_loss / len(loader), accuracy_score(all_labels, all_preds)


def eval_epoch(model, loader):
    model.eval()
    total_loss, all_preds, all_labels = 0.0, [], []
    with torch.no_grad():
        for batch in loader:
            input_ids      = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels         = batch['label'].to(device)
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            total_loss += outputs.loss.item()
            all_preds.extend(outputs.logits.argmax(1).cpu().tolist())
            all_labels.extend(labels.cpu().tolist())
    return total_loss / len(loader), accuracy_score(all_labels, all_preds), all_preds, all_labels

# -- Training loop ------------------------------------------------------------
CHECKPOINT_PATH = 'models/bert_checkpoint.pt'

optimiser   = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)
total_steps  = len(train_loader) * NUM_EPOCHS
warmup_steps = total_steps // 10
scheduler   = get_linear_schedule_with_warmup(
    optimiser, num_warmup_steps=warmup_steps, num_training_steps=total_steps
)

history      = {'train_loss': [], 'val_loss': [], 'train_acc': [], 'val_acc': []}
best_acc     = 0.0
best_state   = None
start_epoch  = 1

# Resume from checkpoint if one exists
if os.path.exists(CHECKPOINT_PATH):
    print(f'\nFound checkpoint at {CHECKPOINT_PATH} — resuming...')
    ckpt = torch.load(CHECKPOINT_PATH, map_location=device)
    model.load_state_dict(ckpt['model_state'])
    optimiser.load_state_dict(ckpt['optimiser_state'])
    scheduler.load_state_dict(ckpt['scheduler_state'])
    history     = ckpt['history']
    best_acc    = ckpt['best_acc']
    best_state  = ckpt['best_state']
    start_epoch = ckpt['epoch'] + 1
    print(f'Resuming from epoch {start_epoch}/{NUM_EPOCHS}')
else:
    print(f'\n{"=" * 60}')
    print(f' Training BERT ({MODEL_NAME})')
    print(f'{"=" * 60}')

for epoch in range(start_epoch, NUM_EPOCHS + 1):
    print(f'\n{"=" * 60}')
    print(f' Epoch {epoch}/{NUM_EPOCHS}')
    print(f'{"=" * 60}')
    tr_loss, tr_acc       = train_epoch(model, train_loader, optimiser, scheduler)
    print(f'  Validating...')
    vl_loss, vl_acc, _, _ = eval_epoch(model, val_loader)

    for k, v in zip(history.keys(), [tr_loss, vl_loss, tr_acc, vl_acc]):
        history[k].append(v)

    if vl_acc > best_acc:
        best_acc   = vl_acc
        best_state = {k: v.clone() for k, v in model.state_dict().items()}

    print(f'  Epoch {epoch:2d}/{NUM_EPOCHS} | '
          f'train loss={tr_loss:.4f} acc={tr_acc:.4f} | '
          f'val   loss={vl_loss:.4f} acc={vl_acc:.4f}')

    # Save checkpoint after every epoch
    torch.save({
        'epoch':           epoch,
        'model_state':     model.state_dict(),
        'optimiser_state': optimiser.state_dict(),
        'scheduler_state': scheduler.state_dict(),
        'history':         history,
        'best_acc':        best_acc,
        'best_state':      best_state,
    }, CHECKPOINT_PATH)
    print(f'  Checkpoint saved → {CHECKPOINT_PATH}')

model.load_state_dict(best_state)
print(f'  Best val accuracy: {best_acc:.4f}')

# Clean up checkpoint once fully trained
if os.path.exists(CHECKPOINT_PATH):
    os.remove(CHECKPOINT_PATH)
    print('Checkpoint removed (training complete).')

# -- Test evaluation ----------------------------------------------------------
_, test_acc, test_preds, test_true = eval_epoch(model, test_loader)
test_f1 = f1_score(test_true, test_preds, average='macro')

print(f'\n-- BERT Test Results --')
print(f'Accuracy={test_acc:.4f}  F1={test_f1:.4f}')
print(classification_report(test_true, test_preds, target_names=['Fake', 'Real']))

# -- Save model + tokenizer immediately ---------------------------------------
model.save_pretrained(MODEL_SAVE_PATH)
tokenizer.save_pretrained(MODEL_SAVE_PATH)
print(f'Saved: {MODEL_SAVE_PATH}/')

# -- Update training_results.json ---------------------------------------------
try:
    with open('models/training_results.json') as f:
        all_results = json.load(f)
except FileNotFoundError:
    all_results = {}

all_results['bert'] = {
    'test_acc': test_acc,
    'test_f1':  test_f1,
    'history':  history,
    'hyperparams': {
        'model_name':   MODEL_NAME,
        'max_len':      MAX_LEN,
        'batch_size':   BATCH_SIZE,
        'num_epochs':   NUM_EPOCHS,
        'lr':           LR,
        'train_subset': TRAIN_SUBSET
    }
}

with open('models/training_results.json', 'w') as f:
    json.dump(all_results, f, indent=2)
print('Updated: models/training_results.json')
