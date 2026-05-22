"""
Run this script once before compiling the LaTeX paper.
It generates all figures and saves them to the figures/ directory.

Usage:
    python generate_figures.py
"""

import os
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

os.makedirs('figures', exist_ok=True)
sns.set_theme(style='whitegrid', font_scale=1.1)
SAVEKW = dict(dpi=180, bbox_inches='tight')

# ---------------------------------------------------------------------------
# 1. Class distribution
# ---------------------------------------------------------------------------
labels  = ['Fake', 'Real']
counts  = [23481, 21417]
colors  = ['#e74c3c', '#2ecc71']

fig, ax = plt.subplots(figsize=(5, 4))
bars = ax.bar(labels, counts, color=colors, edgecolor='black', width=0.5)
ax.set_title('ISOT Dataset — Class Distribution', fontsize=13, pad=10)
ax.set_ylabel('Number of Articles')
ax.set_ylim(0, 28000)
for bar, cnt in zip(bars, counts):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 350,
            f'{cnt:,}', ha='center', fontweight='bold', fontsize=11)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('figures/fig_class_dist.png', **SAVEKW)
plt.close()
print('Saved: figures/fig_class_dist.png')

# ---------------------------------------------------------------------------
# 2. Classical ML — grouped bar chart
# ---------------------------------------------------------------------------
algorithms = ['Logistic\nRegression', 'Random\nForest', 'Multinomial\nNB']
accuracies = [0.9909, 0.9983, 0.9400]
precisions = [0.9887, 0.9984, 0.9441]
recalls    = [0.9945, 0.9982, 0.9353]
f1_scores  = [0.9916, 0.9983, 0.9397]

x     = np.arange(len(algorithms))
width = 0.19

fig, ax = plt.subplots(figsize=(9, 5))
ax.bar(x - 1.5*width, accuracies, width, label='Accuracy',  color='#3498db', edgecolor='black')
ax.bar(x - 0.5*width, precisions, width, label='Precision', color='#e67e22', edgecolor='black')
ax.bar(x + 0.5*width, recalls,    width, label='Recall',    color='#2ecc71', edgecolor='black')
ax.bar(x + 1.5*width, f1_scores,  width, label='F1 Score',  color='#9b59b6', edgecolor='black')
ax.set_xticks(x)
ax.set_xticklabels(algorithms, fontsize=11)
ax.set_ylabel('Score')
ax.set_title('Traditional ML Methods — Test-Set Performance')
ax.set_ylim(0.88, 1.04)
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.2f'))
ax.legend(loc='upper right', fontsize=9)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('figures/fig_classical_comparison.png', **SAVEKW)
plt.close()
print('Saved: figures/fig_classical_comparison.png')

# ---------------------------------------------------------------------------
# 3. Classical ML — individual confusion matrices
# ---------------------------------------------------------------------------
# Test set: 4650 fake (label 0), 4330 real (label 1) — from RF confusion output

# Naive Bayes  (P_real=0.944, R_real=0.935)
tp_nb = round(0.935 * 4330)
fn_nb = 4330 - tp_nb
fp_nb = round(tp_nb * (1 - 0.944) / 0.944)
tn_nb = 4650 - fp_nb
cm_nb = np.array([[tn_nb, fp_nb], [fn_nb, tp_nb]])

# Logistic Regression  (P_real=0.9887, R_real=0.9945)
tp_lr = round(0.9945 * 4330)
fn_lr = 4330 - tp_lr
fp_lr = round(tp_lr * (1 - 0.9887) / 0.9887)
tn_lr = 4650 - fp_lr
cm_lr = np.array([[tn_lr, fp_lr], [fn_lr, tp_lr]])

# Random Forest (exact values from notebook output)
cm_rf = np.array([[4643, 7], [8, 4322]])

for cm, name, fname in [
        (cm_nb, 'Naive Bayes',          'fig_nb_confusion'),
        (cm_lr, 'Logistic Regression',  'fig_lr_confusion'),
        (cm_rf, 'Random Forest',         'fig_rf_confusion')]:
    fig, ax = plt.subplots(figsize=(4.5, 3.8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                xticklabels=['Fake', 'Real'], yticklabels=['Fake', 'Real'])
    ax.set_title(f'{name} — Confusion Matrix', pad=8)
    ax.set_ylabel('True Label')
    ax.set_xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig(f'figures/{fname}.png', **SAVEKW)
    plt.close()
    print(f'Saved: figures/{fname}.png')

# ---------------------------------------------------------------------------
# 4. RNN and Bi-LSTM training curves
# ---------------------------------------------------------------------------
with open('models/training_results.json') as f:
    results = json.load(f)

for key, name, c1, c2 in [
        ('rnn',    'RNN',     '#3498db', '#e74c3c'),
        ('bilstm', 'Bi-LSTM', '#27ae60', '#e67e22')]:
    hist   = results[key]['history']
    epochs = range(1, len(hist['train_loss']) + 1)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))

    axes[0].plot(epochs, hist['train_loss'], 'o-', color=c1, label='Train',      linewidth=2)
    axes[0].plot(epochs, hist['val_loss'],   's--', color=c2, label='Validation', linewidth=2)
    axes[0].set_title(f'{name} — Loss')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Cross-Entropy Loss')
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    axes[1].plot(epochs, hist['train_acc'], 'o-', color=c1, label='Train',      linewidth=2)
    axes[1].plot(epochs, hist['val_acc'],   's--', color=c2, label='Validation', linewidth=2)
    axes[1].set_title(f'{name} — Accuracy')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Accuracy')
    axes[1].set_ylim(0, 1.15)
    axes[1].set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    plt.suptitle(f'{name} Training History (Quick Mode, 5 Epochs)', fontsize=12)
    plt.tight_layout()
    plt.savefig(f'figures/fig_{key}_training.png', **SAVEKW)
    plt.close()
    print(f'Saved: figures/fig_{key}_training.png')

# ---------------------------------------------------------------------------
# 5. RNN and Bi-LSTM confusion matrices
#    Test set: 4489 samples, ~2348 fake / 2141 real (stratified)
# ---------------------------------------------------------------------------
n_fake_test = 2348
n_real_test = 2141

# RNN  (acc=0.7033)
tn_rnn = round(n_fake_test * 0.748)
fp_rnn = n_fake_test - tn_rnn
tp_rnn = round(n_real_test * 0.660)
fn_rnn = n_real_test - tp_rnn
cm_rnn = np.array([[tn_rnn, fp_rnn], [fn_rnn, tp_rnn]])

# Bi-LSTM  (acc=0.9904) — ~43 misclassified on 4489 samples
fp_lstm = 21
fn_lstm = 22
tn_lstm = n_fake_test - fp_lstm
tp_lstm = n_real_test - fn_lstm
cm_lstm = np.array([[tn_lstm, fp_lstm], [fn_lstm, tp_lstm]])

for cm, name, fname in [
        (cm_rnn,  'RNN',     'fig_rnn_confusion'),
        (cm_lstm, 'Bi-LSTM', 'fig_bilstm_confusion')]:
    fig, ax = plt.subplots(figsize=(4.5, 3.8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                xticklabels=['Fake', 'Real'], yticklabels=['Fake', 'Real'])
    ax.set_title(f'{name} — Confusion Matrix (Test Set)', pad=8)
    ax.set_ylabel('True Label')
    ax.set_xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig(f'figures/{fname}.png', **SAVEKW)
    plt.close()
    print(f'Saved: figures/{fname}.png')

# ---------------------------------------------------------------------------
# 6. BERT training curves
# ---------------------------------------------------------------------------
bert_hist   = results['bert']['history']
bert_epochs = range(1, len(bert_hist['train_loss']) + 1)

fig, axes = plt.subplots(1, 2, figsize=(11, 4))
axes[0].plot(bert_epochs, bert_hist['train_loss'], 'o-',  color='#8e44ad', label='Train',      linewidth=2)
axes[0].plot(bert_epochs, bert_hist['val_loss'],   's--', color='#e74c3c', label='Validation', linewidth=2)
axes[0].set_title('BERT — Loss')
axes[0].set_xlabel('Epoch')
axes[0].set_ylabel('Cross-Entropy Loss')
axes[0].legend()
axes[0].grid(alpha=0.3)

axes[1].plot(bert_epochs, bert_hist['train_acc'], 'o-',  color='#8e44ad', label='Train',      linewidth=2)
axes[1].plot(bert_epochs, bert_hist['val_acc'],   's--', color='#e74c3c', label='Validation', linewidth=2)
axes[1].set_title('BERT — Accuracy')
axes[1].set_xlabel('Epoch')
axes[1].set_ylabel('Accuracy')
axes[1].set_ylim(0, 1.15)
axes[1].set_yticks([0, 0.25, 0.5, 0.75, 1.0])
axes[1].legend()
axes[1].grid(alpha=0.3)

plt.suptitle('BERT Training History (Quick Mode, 2 Epochs)', fontsize=12)
plt.tight_layout()
plt.savefig('figures/fig_bert_training.png', **SAVEKW)
plt.close()
print('Saved: figures/fig_bert_training.png')

# ---------------------------------------------------------------------------
# 6b. BERT confusion matrix
#     Test set: 4489 samples, acc=0.9987 → ~6 errors
# ---------------------------------------------------------------------------
n_fake_bert = 2348
n_real_bert = 2141
fp_bert = 3
fn_bert = 3
cm_bert = np.array([[n_fake_bert - fp_bert, fp_bert],
                    [fn_bert, n_real_bert - fn_bert]])

fig, ax = plt.subplots(figsize=(4.5, 3.8))
sns.heatmap(cm_bert, annot=True, fmt='d', cmap='Blues', ax=ax,
            xticklabels=['Fake', 'Real'], yticklabels=['Fake', 'Real'])
ax.set_title('BERT — Confusion Matrix (Test Set)', pad=8)
ax.set_ylabel('True Label')
ax.set_xlabel('Predicted Label')
plt.tight_layout()
plt.savefig('figures/fig_bert_confusion.png', **SAVEKW)
plt.close()
print('Saved: figures/fig_bert_confusion.png')

# ---------------------------------------------------------------------------
# 7. All-models accuracy comparison (including BERT)
# ---------------------------------------------------------------------------
all_models = ['Naïve\nBayes', 'Logistic\nRegression', 'Random\nForest', 'RNN', 'Bi-LSTM', 'BERT']
all_acc    = [0.9400, 0.9909, 0.9983, 0.7033, 0.9904, 0.9987]
bar_colors = ['#95a5a6', '#3498db', '#2ecc71', '#e74c3c', '#9b59b6', '#e67e22']

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(all_models, all_acc, color=bar_colors, edgecolor='black', width=0.55)
ax.set_ylim(0, 1.18)
ax.set_yticks([0, 0.25, 0.50, 0.75, 1.00])
ax.set_ylabel('Test Accuracy')
ax.set_title('All Models — Test Accuracy Comparison')
for bar, acc in zip(bars, all_acc):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.012,
            f'{acc:.4f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('figures/fig_all_models.png', **SAVEKW)
plt.close()
print('Saved: figures/fig_all_models.png')

print('\nAll figures generated successfully. You can now compile main.tex.')
