# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from scipy.signal import ricker, cwt

print("Testing mathematical preprocessing modules...")

# Test 1: FOD
def fractional_derivative(X, alpha=0.5, K=5):
    N, D = X.shape
    w = np.zeros(K)
    w[0] = 1.0
    for k in range(1, K):
        w[k] = w[k-1] * (k - 1 - alpha) / k
    w = (-1) ** np.arange(K) * w
    
    X_fod = np.zeros_like(X)
    for i in range(N):
        x = X[i]
        for t in range(D):
            val = 0.0
            for k in range(min(t + 1, K)):
                val += w[k] * x[t - k]
            X_fod[i, t] = val
    return X_fod

X_dummy = np.random.rand(10, 21)
X_fod = fractional_derivative(X_dummy, alpha=0.5)
assert X_fod.shape == (10, 21)
print("FOD OK!")

# Test 2: MSC
def msc(X_train, X_test=None):
    ref = np.mean(X_train, axis=0)
    X_train_msc = np.zeros_like(X_train)
    for i in range(len(X_train)):
        poly = np.polyfit(ref, X_train[i], deg=1)
        X_train_msc[i] = (X_train[i] - poly[1]) / (poly[0] if abs(poly[0]) > 1e-6 else 1.0)
    if X_test is not None:
        X_test_msc = np.zeros_like(X_test)
        for i in range(len(X_test)):
            poly = np.polyfit(ref, X_test[i], deg=1)
            X_test_msc[i] = (X_test[i] - poly[1]) / (poly[0] if abs(poly[0]) > 1e-6 else 1.0)
        return X_train_msc, X_test_msc
    return X_train_msc

X_tr_msc, X_te_msc = msc(X_dummy[:7], X_dummy[7:])
assert X_tr_msc.shape == (7, 21) and X_te_msc.shape == (3, 21)
print("MSC OK!")

# Test 3: CWT
def cwt_features(X, widths=[2, 4, 8]):
    feats = []
    for i in range(len(X)):
        cwt_mat = cwt(X[i], ricker, widths) # len(widths) x D
        feats.append(np.hstack([X[i], cwt_mat.flatten()]))
    return np.array(feats)

X_cwt = cwt_features(X_dummy)
print(f"CWT features shape: {X_cwt.shape}")

print("All preprocessing tests passed successfully!")
