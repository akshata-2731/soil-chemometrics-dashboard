# -*- coding: utf-8 -*-
"""
================================================================================
2D SPECTRAL VISION & DEEP LEARNING BENCHMARK (49-FOLD LOOCV ACROSS ALL 12 NUTRIENTS)
================================================================================
Implements the exact experimental setup recommended in the 5 uploaded research slides:

Representations & Models Evaluated:
  1. Raw 21-D + PLSR (Chemometric baseline)
  2. Raw 21-D + SVR (Non-linear kernel baseline)
  3. Raw 21-D + Tiny 1D-CNN (Neural baseline)
  4. GASF (21x21) + Tiny 2D-CNN (Gramian Angular Summation Field)
  5. GADF (21x21) + Tiny 2D-CNN (Gramian Angular Difference Field)
  6. CWT (21x21) + Tiny 2D-CNN (Continuous Wavelet Scalogram)
  7. MTF (21x21) + Tiny 2D-CNN (Markov Transition Field)
  8. Raw + GASF + Fusion CNN (Complementary Information)
  9. Raw + GASF + GADF + Full Fusion CNN (Full Spectral Representation)
 10. GAF + Attention CNN (Spatial & Channel Attention + Global Pooling)

Evaluation Metrics:
  - RMSE (Root Mean Squared Error)
  - MAE (Mean Absolute Error)
  - R^2 (Coefficient of Determination)
  - RPD (Residual Prediction Deviation = SD / RMSE)
  - Ratio Value Accuracy (%): min(A, P) / max(A, P) * 100%
  - Range Value Accuracy (%): (1 - RMSE / Range) * 100%
  - ISO 17025 Class Accuracy (%)

Output:
  - 'Spectral_2D_Vision_DeepLearning_LOOCV_Benchmark.xlsx'
================================================================================
"""

import os
import sys
import time
import warnings
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd
import numpy as np
import pywt
from sklearn.model_selection import LeaveOneOut
from sklearn.cross_decomposition import PLSRegression
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import torch
import torch.nn as nn
import torch.optim as optim

warnings.filterwarnings('ignore')
torch.manual_seed(42)
np.random.seed(42)

# Soil fertility classification rules
CLASS_RULES = {
    'OC%': {'Low': (0.1, 0.5), 'Med': (0.5, 0.75), 'High': (0.75, 2.0)},
    'N Kg/ha': {'Low': (50, 280), 'Med': (280, 560)},
    'P2O5': {'Low': (2, 22.9), 'Med': (22.9, 56.3), 'High': (56.3, 120)},
    'K2O': {'Low': (50, 144), 'Med': (144, 336), 'High': (336, 800)},
    'SO4': {'Low': (2, 10), 'Med': (10, 20), 'High': (20, 250)},
    'Fe (ppm)': {'Low': (1, 4.5), 'Med': (4.5, 10), 'High': (10, 50)},
    'Mn (ppm)': {'Low': (0.1, 2), 'Med': (2, 4), 'High': (4, 25)},
    'Cu (ppm)': {'Low': (0.1, 0.2), 'Med': (0.2, 0.4), 'High': (0.4, 10)},
    'Zn (ppm)': {'Low': (0.1, 0.6), 'Med': (0.6, 1.2), 'High': (1.2, 10)},
    'B (ppm)': {'Low': (0.1, 0.5), 'Med': (0.5, 1.0), 'High': (1.0, 10)},
    'Ca (meq)': {'Deficient': (1, 6), 'Sufficient': (6, 100)},
    'Mg (meq)': {'Deficient': (0, 4), 'Sufficient': (4, 50)}
}

SHEET_MAPPING = {
    'OC%': 'OC',
    'Ca (meq)': 'Ca meq',
    'Mg (meq)': 'Mg meq',
    'N Kg/ha': 'N Kg_ha',
    'P2O5': 'P2O5',
    'K2O': 'K2O',
    'SO4': 'SO4',
    'Fe (ppm)': 'Fe ppm',
    'Mn (ppm)': 'Mn ppm',
    'Cu (ppm)': 'Cu ppm',
    'Zn (ppm)': 'Zn ppm',
    'B (ppm)': 'B ppm'
}

def assign_class(val, rules):
    if pd.isna(val): return np.nan
    for label, (low, high) in rules.items():
        if low <= val <= high: return label
    min_diff = float('inf')
    best_label = np.nan
    for label, (low, high) in rules.items():
        if val < low and (low - val) < min_diff:
            min_diff = low - val
            best_label = label
        elif val > high and (val - high) < min_diff:
            min_diff = val - high
            best_label = label
    return best_label

def get_boundary_cutoffs(rules):
    cutoffs = set()
    for _, (low, high) in rules.items():
        cutoffs.add(low)
        cutoffs.add(high)
    return [c for c in cutoffs if c not in [0, 0.1, 1, 2, 50, 100, 120, 250, 800]]

def compute_ratio_accuracy(act_v, pred_v):
    if act_v == 0 and pred_v == 0: return 100.0
    if act_v <= 0 or pred_v <= 0: return 0.0
    return (min(act_v, pred_v) / max(act_v, pred_v)) * 100.0

# ------------------------------------------------------------------------------
# 2D SPECTRAL COMPUTER VISION ENCODERS (GASF, GADF, MTF, CWT)
# ------------------------------------------------------------------------------
def compute_gasf_gadf(X_raw):
    """Encodes 21-D spectrum into 21x21 GASF and GADF matrices."""
    N, D = X_raw.shape
    X_min = X_raw.min(axis=1, keepdims=True)
    X_max = X_raw.max(axis=1, keepdims=True)
    X_norm = (X_raw - X_min) / (X_max - X_min + 1e-6) * 2.0 - 1.0
    X_norm = np.clip(X_norm, -1.0, 1.0)
    phi = np.arccos(X_norm) # (N, 21)

    GASF = np.zeros((N, D, D), dtype=np.float32)
    GADF = np.zeros((N, D, D), dtype=np.float32)

    for i in range(N):
        p = phi[i]
        GASF[i] = np.cos(p[:, None] + p[None, :])
        GADF[i] = np.sin(p[:, None] - p[None, :])
    return GASF, GADF

def compute_mtf(X_raw, n_bins=4):
    """Encodes 21-D spectrum into 21x21 Markov Transition Field (MTF)."""
    N, D = X_raw.shape
    MTF = np.zeros((N, D, D), dtype=np.float32)
    for i in range(N):
        x = X_raw[i]
        q_edges = np.quantile(x, np.linspace(0, 1, n_bins + 1)[1:-1])
        q = np.digitize(x, q_edges)
        W = np.zeros((n_bins, n_bins), dtype=np.float32)
        for k in range(D - 1):
            W[q[k], q[k+1]] += 1.0
        row_sums = W.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        W = W / row_sums
        MTF[i] = W[q[:, None], q[None, :]]
    return MTF

def compute_cwt(X_raw):
    """Encodes 21-D spectrum into 21x21 Continuous Wavelet Transform (CWT) Scalogram."""
    N, D = X_raw.shape
    CWT = np.zeros((N, D, D), dtype=np.float32)
    scales = np.arange(1, D + 1)
    for i in range(N):
        coefs, _ = pywt.cwt(X_raw[i], scales=scales, wavelet='morl')
        # Normalize scalogram per sample
        c_min, c_max = coefs.min(), coefs.max()
        if c_max > c_min:
            coefs = (coefs - c_min) / (c_max - c_min) * 2.0 - 1.0
        CWT[i] = coefs.astype(np.float32)
    return CWT

# ------------------------------------------------------------------------------
# NEURAL ARCHITECTURES (Tiny 1D-CNN, Tiny 2D-CNN, Fusion, GAF+Attention)
# ------------------------------------------------------------------------------
class Tiny1DCNN(nn.Module):
    def __init__(self, in_dim=21):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv1d(1, 8, kernel_size=3, padding=1),
            nn.BatchNorm1d(8),
            nn.ReLU(),
            nn.Conv1d(8, 16, kernel_size=3, padding=1),
            nn.BatchNorm1d(16),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 1)
        )
    def forward(self, x):
        # x: (B, 21) -> (B, 1, 21)
        return self.net(x.unsqueeze(1)).squeeze(-1)

class Tiny2DCNN(nn.Module):
    def __init__(self, in_channels=1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_channels, 8, kernel_size=3, padding=1),
            nn.BatchNorm2d(8),
            nn.ReLU(),
            nn.Conv2d(8, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 1)
        )
    def forward(self, x):
        return self.net(x).squeeze(-1)

class FusionCNN(nn.Module):
    def __init__(self, img_channels=1, raw_dim=21):
        super().__init__()
        self.cnn2d = nn.Sequential(
            nn.Conv2d(img_channels, 8, kernel_size=3, padding=1),
            nn.BatchNorm2d(8),
            nn.ReLU(),
            nn.Conv2d(8, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten()
        )
        self.mlp1d = nn.Sequential(
            nn.Linear(raw_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU()
        )
        self.head = nn.Sequential(
            nn.Linear(16 + 8, 8),
            nn.ReLU(),
            nn.Linear(8, 1)
        )
    def forward(self, img, raw):
        f2d = self.cnn2d(img)
        f1d = self.mlp1d(raw)
        fused = torch.cat([f2d, f1d], dim=1)
        return self.head(fused).squeeze(-1)

class SpatialAttention(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Conv2d(2, 1, kernel_size=3, padding=1)
        self.sigmoid = nn.Sigmoid()
    def forward(self, x):
        avg_out = torch.mean(x, dim=1, keepdim=True)
        max_out, _ = torch.max(x, dim=1, keepdim=True)
        scale = torch.cat([avg_out, max_out], dim=1)
        return x * self.sigmoid(self.conv(scale))

class ChannelAttention(nn.Module):
    def __init__(self, in_planes, ratio=4):
        super().__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(in_planes, in_planes // ratio, bias=False),
            nn.ReLU(),
            nn.Linear(in_planes // ratio, in_planes, bias=False)
        )
        self.sigmoid = nn.Sigmoid()
    def forward(self, x):
        b, c, _, _ = x.size()
        avg_out = self.fc(self.avg_pool(x).view(b, c)).view(b, c, 1, 1)
        max_out = self.fc(self.max_pool(x).view(b, c)).view(b, c, 1, 1)
        return x * self.sigmoid(avg_out + max_out)

class GAFAttentionCNN(nn.Module):
    """Slide 2: GAF -> 2-3 conv blocks -> channel/spatial attention -> global pooling -> regression"""
    def __init__(self, in_channels=2):
        super().__init__()
        self.block1 = nn.Sequential(
            nn.Conv2d(in_channels, 8, kernel_size=3, padding=1),
            nn.BatchNorm2d(8),
            nn.ReLU()
        )
        self.block2 = nn.Sequential(
            nn.Conv2d(8, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU()
        )
        self.ca = ChannelAttention(16, ratio=4)
        self.sa = SpatialAttention()
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 1)
        )
    def forward(self, x):
        x = self.block1(x)
        x = self.block2(x)
        x = self.ca(x)
        x = self.sa(x)
        x = self.pool(x)
        return self.head(x).squeeze(-1)

# ------------------------------------------------------------------------------
# FAST TORCH TRAINING HELPER
# ------------------------------------------------------------------------------
def train_and_eval_nn(model, X_train, y_train, X_test, epochs=25, lr=0.01, is_fusion=False, raw_tr=None, raw_te=None):
    criterion = nn.MSELoss()
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-3)
    
    # Target normalization
    y_mean = float(y_train.mean())
    y_std = float(y_train.std()) if y_train.std() > 1e-4 else 1.0
    y_tr_norm = torch.tensor((y_train - y_mean) / y_std, dtype=torch.float32)

    model.train()
    for _ in range(epochs):
        optimizer.zero_grad()
        if is_fusion:
            pred = model(X_train, raw_tr)
        else:
            pred = model(X_train)
        loss = criterion(pred.squeeze(), y_tr_norm)
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        if is_fusion:
            test_norm = model(X_test, raw_te).squeeze().item()
        else:
            test_norm = model(X_test).squeeze().item()
    pred_val = test_norm * y_std + y_mean
    return float(pred_val)

# ------------------------------------------------------------------------------
# MAIN BENCHMARK ENGINE
# ------------------------------------------------------------------------------
def main():
    t_start = time.time()
    print("=" * 80)
    print("2D SPECTRAL VISION & DEEP LEARNING BENCHMARK (49-FOLD LOOCV)")
    print("Implementing exact setups from uploaded research slides (GASF, GADF, CWT, MTF, Attention)")
    print("=" * 80)

    script_dir = r"c:\Users\akash\Downloads\Soil Data"
    data_file = os.path.join(script_dir, 'data.xlsx')
    output_excel = os.path.join(script_dir, 'Spectral_2D_Vision_DeepLearning_LOOCV_Benchmark.xlsx')

    df = pd.read_excel(data_file)
    spec_cols = [c for c in df.columns if c.startswith('nm_')]
    loo = LeaveOneOut()

    model_keys = [
        ("M1_PLSR", "Raw 21-D | PLSR (Chemometric baseline)"),
        ("M2_SVR", "Raw 21-D | SVR (Non-linear kernel baseline)"),
        ("M3_Tiny1D_CNN", "Raw 21-D | Tiny 1D-CNN (Neural baseline)"),
        ("M4_GASF_CNN", "GASF 21x21 | Tiny 2D-CNN (Angular relationship)"),
        ("M5_GADF_CNN", "GADF 21x21 | Tiny 2D-CNN (Difference relationship)"),
        ("M6_CWT_CNN", "CWT 21x21 | Tiny 2D-CNN (Wavelet scalogram)"),
        ("M7_MTF_CNN", "MTF 21x21 | Tiny 2D-CNN (Transition structure)"),
        ("M8_Fusion_GASF", "Raw + GASF | Fusion CNN (Complementary)"),
        ("M9_Full_Fusion", "Raw + GASF + GADF | Full Fusion CNN"),
        ("M10_GAF_Attention", "GAF + Attention CNN (Spatial & Channel Attn)")
    ]

    macro_results = {k: [] for k, _ in model_keys}
    detailed_sheets = {}

    for target, sheet_name in SHEET_MAPPING.items():
        t0 = time.time()
        rules = CLASS_RULES[target]
        cutoffs = get_boundary_cutoffs(rules)

        s_clean = df[target].astype(str).str.strip().str.replace('l ', '1').str.replace('l', '1')
        s_numeric = pd.to_numeric(s_clean, errors='coerce')
        valid_mask = s_numeric.notnull()
        df_target = df[valid_mask].copy()
        df_target[target] = s_numeric[valid_mask]

        valid_indices = df_target.index.values
        X_raw = df_target[spec_cols].values.astype(np.float32)
        y_cont = df_target[target].values.astype(np.float32)
        n_valid = len(y_cont)
        val_range = float(y_cont.max() - y_cont.min())
        y_std = float(y_cont.std())
        y_class = np.array([assign_class(v, rules) for v in y_cont])

        # Generate 2D computer vision representations
        GASF, GADF = compute_gasf_gadf(X_raw)
        MTF = compute_mtf(X_raw, n_bins=4)
        CWT = compute_cwt(X_raw)
        GAF_2ch = np.stack([GASF, GADF], axis=1) # (N, 2, 21, 21)

        T_gasf = torch.tensor(GASF, dtype=torch.float32).unsqueeze(1)
        T_gadf = torch.tensor(GADF, dtype=torch.float32).unsqueeze(1)
        T_cwt = torch.tensor(CWT, dtype=torch.float32).unsqueeze(1)
        T_mtf = torch.tensor(MTF, dtype=torch.float32).unsqueeze(1)
        T_gaf2 = torch.tensor(GAF_2ch, dtype=torch.float32)

        # Predictions dictionary for all 10 models
        preds = {k: np.zeros(n_valid, dtype=np.float32) for k, _ in model_keys}

        # 49-Fold LOOCV Loop
        for tr, te in loo.split(X_raw):
            idx_te = te[0]
            y_tr = y_cont[tr]

            # Scaler for raw 1D spectra
            sc = StandardScaler().fit(X_raw[tr])
            X_tr_s = sc.transform(X_raw[tr])
            X_te_s = sc.transform(X_raw[te])

            # 1. Raw 21-D + PLSR
            pls = PLSRegression(n_components=min(4, X_raw.shape[1])).fit(X_tr_s, y_tr)
            preds["M1_PLSR"][idx_te] = max(float(pls.predict(X_te_s).flatten()[0]), 1e-3)

            # 2. Raw 21-D + SVR
            svr = SVR(kernel='rbf', C=50.0, epsilon=0.05).fit(X_tr_s, y_tr)
            preds["M2_SVR"][idx_te] = max(float(svr.predict(X_te_s).flatten()[0]), 1e-3)

            # PyTorch Tensors for this fold
            t_raw_tr = torch.tensor(X_tr_s, dtype=torch.float32)
            t_raw_te = torch.tensor(X_te_s, dtype=torch.float32)

            t_gasf_tr = T_gasf[tr]
            t_gasf_te = T_gasf[te]

            t_gadf_tr = T_gadf[tr]
            t_gadf_te = T_gadf[te]

            t_cwt_tr = T_cwt[tr]
            t_cwt_te = T_cwt[te]

            t_mtf_tr = T_mtf[tr]
            t_mtf_te = T_mtf[te]

            t_gaf2_tr = T_gaf2[tr]
            t_gaf2_te = T_gaf2[te]

            # 3. Raw 21-D + Tiny 1D-CNN
            m3 = Tiny1DCNN(in_dim=21)
            preds["M3_Tiny1D_CNN"][idx_te] = max(train_and_eval_nn(m3, t_raw_tr, y_tr, t_raw_te), 1e-3)

            # 4. GASF 21x21 + Tiny 2D-CNN
            m4 = Tiny2DCNN(in_channels=1)
            preds["M4_GASF_CNN"][idx_te] = max(train_and_eval_nn(m4, t_gasf_tr, y_tr, t_gasf_te), 1e-3)

            # 5. GADF 21x21 + Tiny 2D-CNN
            m5 = Tiny2DCNN(in_channels=1)
            preds["M5_GADF_CNN"][idx_te] = max(train_and_eval_nn(m5, t_gadf_tr, y_tr, t_gadf_te), 1e-3)

            # 6. CWT 21x21 + Tiny 2D-CNN
            m6 = Tiny2DCNN(in_channels=1)
            preds["M6_CWT_CNN"][idx_te] = max(train_and_eval_nn(m6, t_cwt_tr, y_tr, t_cwt_te), 1e-3)

            # 7. MTF 21x21 + Tiny 2D-CNN
            m7 = Tiny2DCNN(in_channels=1)
            preds["M7_MTF_CNN"][idx_te] = max(train_and_eval_nn(m7, t_mtf_tr, y_tr, t_mtf_te), 1e-3)

            # 8. Raw + GASF Fusion CNN
            m8 = FusionCNN(img_channels=1, raw_dim=21)
            preds["M8_Fusion_GASF"][idx_te] = max(train_and_eval_nn(m8, t_gasf_tr, y_tr, t_gasf_te, is_fusion=True, raw_tr=t_raw_tr, raw_te=t_raw_te), 1e-3)

            # 9. Full Fusion (Raw + GASF + GADF)
            m9 = FusionCNN(img_channels=2, raw_dim=21)
            preds["M9_Full_Fusion"][idx_te] = max(train_and_eval_nn(m9, t_gaf2_tr, y_tr, t_gaf2_te, is_fusion=True, raw_tr=t_raw_tr, raw_te=t_raw_te), 1e-3)

            # 10. GAF + Attention CNN
            m10 = GAFAttentionCNN(in_channels=2)
            preds["M10_GAF_Attention"][idx_te] = max(train_and_eval_nn(m10, t_gaf2_tr, y_tr, t_gaf2_te), 1e-3)

        # Compute metrics for each model on this nutrient
        nutrient_metrics = {}
        for k, name in model_keys:
            p_v = preds[k]
            rmse = float(np.sqrt(mean_squared_error(y_cont, p_v)))
            mae = float(mean_absolute_error(y_cont, p_v))
            r2 = float(r2_score(y_cont, p_v))
            rpd = float(y_std / (rmse + 1e-6))
            range_acc = float((1.0 - (rmse / val_range)) * 100.0) if val_range > 0 else 0.0
            ratios = np.array([compute_ratio_accuracy(a, p) for a, p in zip(y_cont, p_v)])
            pred_classes = np.array([assign_class(p, rules) for p in p_v])
            strict_match = (y_class == pred_classes)
            iso_match = [act_c == pr_c or any(abs(act_v - b) / b <= 0.15 for b in cutoffs) for act_v, act_c, pr_c in zip(y_cont, y_class, pred_classes)]
            strict_acc = float(np.mean(strict_match) * 100.0)
            iso_acc = float(np.mean(iso_match) * 100.0)

            macro_results[k].append({
                'Target': sheet_name,
                'Full Name': target,
                'Samples': n_valid,
                'RMSE': round(rmse, 3),
                'MAE': round(mae, 3),
                'R2': round(r2, 3),
                'RPD': round(rpd, 2),
                'Ratio Acc (%)': round(ratios.mean(), 2),
                'Range Acc (%)': round(range_acc, 2),
                'ISO Class Acc (%)': round(iso_acc, 2)
            })
            nutrient_metrics[k] = {
                'rmse': rmse, 'mae': mae, 'r2': r2, 'rpd': rpd,
                'ratio': ratios.mean(), 'range_acc': range_acc, 'iso_acc': iso_acc,
                'ratios': ratios, 'pred_classes': pred_classes, 'iso_match': iso_match
            }

        # Build detailed sheet dataframe
        sample_ids = [f"Sample_{i+1}" for i in valid_indices]
        sheet_df = pd.DataFrame({
            'Sample ID': sample_ids,
            'Actual Value': np.round(y_cont, 2),
            'Actual Class': y_class
        })
        for k, name in model_keys:
            short_k = k.replace('M', 'M').replace('_', ' ')
            sheet_df[f'{short_k} Pred'] = np.round(preds[k], 2)
            sheet_df[f'{short_k} Ratio %'] = np.round(nutrient_metrics[k]['ratios'], 2)

        detailed_sheets[sheet_name] = sheet_df
        elapsed = time.time() - t0
        best_model_this_tgt = min(model_keys, key=lambda x: nutrient_metrics[x[0]]['rmse'])
        print(f"[{sheet_name:8s}] N={n_valid:2d} | Best: {best_model_this_tgt[0]} (RMSE={nutrient_metrics[best_model_this_tgt[0]]['rmse']:.3f}, R2={nutrient_metrics[best_model_this_tgt[0]]['r2']:.2f}, RPD={nutrient_metrics[best_model_this_tgt[0]]['rpd']:.2f}) [{elapsed:.1f}s]")

    # Macro Table Across All 10 Models
    macro_summary_rows = []
    for k, name in model_keys:
        df_k = pd.DataFrame(macro_results[k])
        macro_summary_rows.append({
            'Model Key': k,
            'Model & Representation': name,
            'Mean RMSE': round(df_k['RMSE'].mean(), 3),
            'Mean MAE': round(df_k['MAE'].mean(), 3),
            'Mean R2': round(df_k['R2'].mean(), 3),
            'Mean RPD': round(df_k['RPD'].mean(), 2),
            'Range Value Acc (%)': round(df_k['Range Acc (%)'].mean(), 2),
            'Ratio Value Acc (%)': round(df_k['Ratio Acc (%)'].mean(), 2),
            'ISO Class Acc (%)': round(df_k['ISO Class Acc (%)'].mean(), 2)
        })

    df_macro = pd.DataFrame(macro_summary_rows)
    print("\n" + "=" * 90)
    print("MACRO BENCHMARK: 2D SPECTRAL VISION & DEEP LEARNING (49-FOLD LOOCV):")
    print(df_macro.to_string(index=False))
    print("=" * 90)

    # Export to Excel
    print(f"\nWriting comprehensive workbook to: {output_excel}")
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        df_macro.to_excel(writer, sheet_name='Macro_Comparison', index=False, startrow=2)
        for s_name, e_df in detailed_sheets.items():
            e_df.to_excel(writer, sheet_name=s_name, index=False, startrow=2)

    wb = openpyxl.load_workbook(output_excel)

    header_font = Font(name='Segoe UI', size=11, bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')
    title_font = Font(name='Segoe UI', size=13, bold=True, color='FFFFFF')
    title_fill = PatternFill(start_color='0D233A', end_color='0D233A', fill_type='solid')

    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )

    # Style sheet 1: Macro_Comparison
    ws_macro = wb['Macro_Comparison']
    ws_macro.merge_cells('A1:I1')
    t_cell = ws_macro['A1']
    t_cell.value = "2D SPECTRAL COMPUTER VISION & DEEP LEARNING (49-FOLD LOOCV BENCHMARK)"
    t_cell.font = title_font
    t_cell.fill = title_fill
    t_cell.alignment = Alignment(horizontal='center', vertical='center')
    ws_macro.row_dimensions[1].height = 28
    ws_macro.row_dimensions[3].height = 24

    for col in range(1, 10):
        c = ws_macro.cell(row=3, column=col)
        c.font = header_font
        c.fill = header_fill
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

    for row in range(4, ws_macro.max_row + 1):
        for col in range(1, 10):
            cell = ws_macro.cell(row=row, column=col)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal='center', vertical='center')

    for col in ws_macro.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max(len(str(cell.value or '')) for cell in col)
        ws_macro.column_dimensions[col_letter].width = max(max_len + 4, 13)

    # Style individual nutrient sheets
    for s_name in SHEET_MAPPING.values():
        ws = wb[s_name]
        ws.merge_cells(f'A1:{get_column_letter(ws.max_column)}1')
        tc = ws['A1']
        tc.value = f"SAMPLE-BY-SAMPLE LOOCV ACTUAL VS PREDICTED: {s_name.upper()}"
        tc.font = title_font
        tc.fill = title_fill
        tc.alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[1].height = 28
        ws.row_dimensions[3].height = 24

        for col in range(1, ws.max_column + 1):
            c = ws.cell(row=3, column=col)
            c.font = header_font
            c.fill = header_fill
            c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

        for row in range(4, ws.max_row + 1):
            for col in range(1, ws.max_column + 1):
                cell = ws.cell(row=row, column=col)
                cell.border = thin_border
                cell.alignment = Alignment(horizontal='center', vertical='center')

        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            max_len = max(len(str(cell.value or '')) for cell in col)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 11)

    wb.save(output_excel)
    print(f"Successfully generated: {output_excel}")
    total_time = time.time() - t_start
    print(f"Total LOOCV execution time: {total_time:.1f} seconds")

if __name__ == '__main__':
    main()
