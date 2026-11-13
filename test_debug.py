import sys
import json
import numpy as np
sys.path.append(".")
from logics.implementations.logic_utils import extract_bands, get_indices, get_calibration_vectors, euclidean, idw_predict
with open("calibration/calibration.json", "r") as f:
    d = json.load(f)["OC"]
nutrient = "OC"
indices = get_indices(nutrient)
min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
sample_vec = np.array([1, 2, 3, 4, 5])
vals = [0.1, 1.0, 2.0]

sample_fp = np.tanh(sample_vec / 1000)
min_fp = np.tanh(min_vec / 1000)
mid_fp = np.tanh(mid_vec / 1000)
max_fp = np.tanh(max_vec / 1000)
d_min_fp = euclidean(sample_fp, min_fp) + 1e-10
d_mid_fp = euclidean(sample_fp, mid_fp) + 1e-10
d_max_fp = euclidean(sample_fp, max_fp) + 1e-10
pred1 = idw_predict([d_min_fp, d_mid_fp, d_max_fp], vals, power=1.5)
V = mid_vec - min_vec
S = sample_vec - min_vec
alpha = np.clip(np.dot(S, V) / (np.dot(V, V) + 1e-10), 0, 1)
pred2 = vals[0] + alpha * (vals[2] - vals[0])
votes = {'LOW': 0, 'MID': 0, 'HIGH': 0}
for i in range(len(indices)):
    d_min_i = abs(sample_vec[i] - min_vec[i])
    d_mid_i = abs(sample_vec[i] - mid_vec[i])
    d_max_i = abs(sample_vec[i] - max_vec[i])
    if d_min_i <= d_mid_i and d_min_i <= d_max_i: votes['LOW'] += 1
    elif d_mid_i <= d_min_i and d_mid_i <= d_max_i: votes['MID'] += 1
    else: votes['HIGH'] += 1
total = sum(votes.values())
pred3 = (votes['LOW']*vals[0] + votes['MID']*vals[1] + votes['HIGH']*vals[2]) / total if total > 0 else vals[1]
n_bands = len(indices)
spread = np.abs(max_vec - min_vec) + 1e-10
weights = spread / spread.sum()
sample_idx = np.sum(sample_vec * weights)
min_idx = np.sum(min_vec * weights)
max_idx = np.sum(max_vec * weights)
if max_idx - min_idx > 1e-10:
    t = (sample_idx - min_idx) / (max_idx - min_idx)
    t = np.clip(t, 0, 1)
    pred4 = vals[0] + t * (vals[2] - vals[0])
else: pred4 = vals[1]
ladder_values = np.linspace(vals[0], vals[2], 50)
min_log = np.log(min_vec + 1e-10)
max_log = np.log(max_vec + 1e-10)
synth_spectra = [np.exp((1-t)*min_log + t*max_log) for t in np.linspace(0, 1, 50)]
distances = [euclidean(sample_vec, synth) + 1e-10 for synth in synth_spectra]
nearest_idx = np.argsort(distances)[:3]
w = 1 / np.array(distances)[nearest_idx]
pred5 = np.sum(w * np.array(ladder_values)[nearest_idx]) / np.sum(w)

print([pred1, pred2, pred3, pred4, pred5])
