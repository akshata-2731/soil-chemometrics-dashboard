import numpy as np
import math
from scipy.spatial.distance import euclidean, cityblock, mahalanobis, cosine, braycurtis
from scipy.stats import pearsonr, spearmanr, entropy
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

NUTRIENT_CONFIG = {
    "OC": {"vals": [0.1, 1.0, 2.0], "indices": [6, 7, 18, 19, 20]},
    "N":  {"vals": [50, 350, 850], "indices": [0, 2, 5, 16]},
    "P":  {"vals": [0.916, 170, 366.4], "indices": [0, 4, 5, 14]},
    "K":  {"vals": [2, 500, 960], "indices": [0, 4, 5, 14]},
    "Ca": {"vals": [1, 60, 120], "indices": [3, 12, 16, 18]},
    "Mg": {"vals": [1, 30, 60], "indices": [1, 3, 6, 12]},
    "S":  {"vals": [10, 120, 250], "indices": [0, 1, 17, 18]},
    "Fe": {"vals": [1, 25, 50], "indices": [0, 1, 2, 3, 4]},
    "Mn": {"vals": [0.5, 12, 25], "indices": [13, 15, 17, 18]},
    "Cu": {"vals": [0.1, 5, 10], "indices": [4, 9, 16, 18]},
    "Zn": {"vals": [0.1, 5, 10], "indices": [5, 10, 14, 18]},
    "B":  {"vals": [0.1, 5, 10], "indices": [6, 7, 16]},
}

def extract_bands(spectrum, indices, use_all=False):
    if indices is None or use_all:
        return np.array(spectrum)
    return np.array([spectrum[i] for i in indices])

def get_blank(d, nutrient):
    blank_key = f'{nutrient.lower()}_blank'
    return d.get(blank_key, None)

def blank_correct(spectrum, blank):
    if blank is not None and len(blank) > 0:
        return np.array(spectrum) - np.array(blank)
    return np.array(spectrum)

def get_calibration_vectors(d, indices, use_all=False):
    min_spectrum = d.get('min', np.zeros(21))
    mid_spectrum = d.get('mid', np.zeros(21))
    max_spectrum = d.get('max', np.zeros(21))
    if use_all:
        return np.array(min_spectrum), np.array(mid_spectrum), np.array(max_spectrum)
    return extract_bands(min_spectrum, indices), extract_bands(mid_spectrum, indices), extract_bands(max_spectrum, indices)

def get_vals(nutrient):
    if nutrient in NUTRIENT_CONFIG:
        return NUTRIENT_CONFIG[nutrient]['vals']
    return [0, 0, 0]

def get_indices(nutrient):
    if nutrient in NUTRIENT_CONFIG:
        return NUTRIENT_CONFIG[nutrient]['indices']
    return list(range(21))

def idw_predict(distances, vals, power=1.0):
    weights = [1/(d**power + 1e-10) for d in distances]
    total_w = sum(weights)
    if total_w == 0:
        return vals[1]
    return sum(w*v for w,v in zip(weights, vals)) / total_w

def logic1_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
    sample_vec = extract_bands(sample, indices)
    if blank is not None:
        blank_vec = extract_bands(blank, indices)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    d_min = euclidean(sample_vec, min_vec) + 1e-10
    d_mid = euclidean(sample_vec, mid_vec) + 1e-10
    d_max = euclidean(sample_vec, max_vec) + 1e-10
    return idw_predict([d_min, d_mid, d_max], vals, power=1.0)

def logic2_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
    sample_vec = extract_bands(sample, indices)
    if blank is not None:
        blank_vec = extract_bands(blank, indices)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    d_min = cityblock(sample_vec, min_vec) + 1e-10
    d_mid = cityblock(sample_vec, mid_vec) + 1e-10
    d_max = cityblock(sample_vec, max_vec) + 1e-10
    return idw_predict([d_min, d_mid, d_max], vals, power=2.0)

def logic3_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
    sample_vec = extract_bands(sample, indices)
    if blank is not None:
        blank_vec = extract_bands(blank, indices)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    sim_min = max(0, 1 - cosine(sample_vec, min_vec)) + 1e-10
    sim_mid = max(0, 1 - cosine(sample_vec, mid_vec)) + 1e-10
    sim_max = max(0, 1 - cosine(sample_vec, max_vec)) + 1e-10
    total = sim_min + sim_mid + sim_max
    return (sim_min*vals[0] + sim_mid*vals[1] + sim_max*vals[2]) / total

def logic4_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices, use_all=True)
    sample_vec = extract_bands(sample, indices, use_all=True)
    if blank is not None:
        blank_vec = np.array(blank)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    cal_matrix = np.array([min_vec, mid_vec, max_vec])
    cov = np.cov(cal_matrix.T)
    inv_cov = np.linalg.pinv(cov + np.eye(len(cov))*1e-10)
    try:
        d_min = mahalanobis(sample_vec, min_vec, inv_cov) + 1e-10
        d_mid = mahalanobis(sample_vec, mid_vec, inv_cov) + 1e-10
        d_max = mahalanobis(sample_vec, max_vec, inv_cov) + 1e-10
    except:
        d_min = euclidean(sample_vec, min_vec) + 1e-10
        d_mid = euclidean(sample_vec, mid_vec) + 1e-10
        d_max = euclidean(sample_vec, max_vec) + 1e-10
    return idw_predict([d_min, d_mid, d_max], vals, power=1.5)

def logic5_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
    sample_vec = extract_bands(sample, indices)
    if blank is not None:
        blank_vec = extract_bands(blank, indices)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    def spectral_angle(a, b):
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return np.pi/2
        cos_angle = np.dot(a, b) / (norm_a * norm_b)
        cos_angle = np.clip(cos_angle, -1, 1)
        return np.arccos(cos_angle)
    d_min = spectral_angle(sample_vec, min_vec) + 1e-10
    d_mid = spectral_angle(sample_vec, mid_vec) + 1e-10
    d_max = spectral_angle(sample_vec, max_vec) + 1e-10
    return idw_predict([d_min, d_mid, d_max], vals, power=1.5)

def logic6_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices, use_all=True)
    sample_vec = extract_bands(sample, indices, use_all=True)
    if blank is not None:
        blank_vec = np.array(blank)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    try:
        corr_min = pearsonr(sample_vec, min_vec)[0]
        corr_mid = pearsonr(sample_vec, mid_vec)[0]
        corr_max = pearsonr(sample_vec, max_vec)[0]
    except:
        corr_min = corr_mid = corr_max = 0
    d_min = 1/(max(0, corr_min) + 1e-10)
    d_mid = 1/(max(0, corr_mid) + 1e-10)
    d_max = 1/(max(0, corr_max) + 1e-10)
    return idw_predict([d_min, d_mid, d_max], vals, power=1.5)

def logic7_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices, use_all=True)
    sample_vec = extract_bands(sample, indices, use_all=True)
    if blank is not None:
        blank_vec = np.array(blank)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    try:
        corr_min = spearmanr(sample_vec, min_vec)[0]
        corr_mid = spearmanr(sample_vec, mid_vec)[0]
        corr_max = spearmanr(sample_vec, max_vec)[0]
    except:
        corr_min = corr_mid = corr_max = 0
    d_min = 1/(max(0, corr_min) + 1e-10)
    d_mid = 1/(max(0, corr_mid) + 1e-10)
    d_max = 1/(max(0, corr_max) + 1e-10)
    return idw_predict([d_min, d_mid, d_max], vals, power=1.5)

def logic8_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
    sample_vec = extract_bands(sample, indices)
    if blank is not None:
        blank_vec = extract_bands(blank, indices)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    def canberra_distance(a, b):
        return np.sum(np.abs(a - b) / (np.abs(a) + np.abs(b) + 1e-10))
    d_min = canberra_distance(sample_vec, min_vec) + 1e-10
    d_mid = canberra_distance(sample_vec, mid_vec) + 1e-10
    d_max = canberra_distance(sample_vec, max_vec) + 1e-10
    return idw_predict([d_min, d_mid, d_max], vals, power=1.5)

def logic9_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
    sample_vec = extract_bands(sample, indices)
    if blank is not None:
        blank_vec = extract_bands(blank, indices)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    d_min = braycurtis(sample_vec, min_vec) + 1e-10
    d_mid = braycurtis(sample_vec, mid_vec) + 1e-10
    d_max = braycurtis(sample_vec, max_vec) + 1e-10
    sim_min = 1 - d_min
    sim_mid = 1 - d_mid
    sim_max = 1 - d_max
    d_min = 1/(sim_min + 1e-10)
    d_mid = 1/(sim_mid + 1e-10)
    d_max = 1/(sim_max + 1e-10)
    return idw_predict([d_min, d_mid, d_max], vals, power=1.0)

def logic10_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
    sample_vec = extract_bands(sample, indices)
    if blank is not None:
        blank_vec = extract_bands(blank, indices)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    votes = {'LOW': 0, 'MID': 0, 'HIGH': 0}
    for i in range(len(indices)):
        d_min = abs(sample_vec[i] - min_vec[i])
        d_mid = abs(sample_vec[i] - mid_vec[i])
        d_max = abs(sample_vec[i] - max_vec[i])
        if d_min <= d_mid and d_min <= d_max:
            votes['LOW'] += 1
        elif d_mid <= d_min and d_mid <= d_max:
            votes['MID'] += 1
        else:
            votes['HIGH'] += 1
    total = sum(votes.values())
    if total == 0: return vals[1]
    return (votes['LOW']*vals[0] + votes['MID']*vals[1] + votes['HIGH']*vals[2]) / total

def logic11_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
    sample_vec = extract_bands(sample, indices)
    if blank is not None:
        blank_vec = extract_bands(blank, indices)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    spread = np.abs(max_vec - min_vec) + 1e-10
    weights = spread / spread.sum()
    vote_weights = {'LOW': 0, 'MID': 0, 'HIGH': 0}
    for i in range(len(indices)):
        d_min = abs(sample_vec[i] - min_vec[i])
        d_mid = abs(sample_vec[i] - mid_vec[i])
        d_max = abs(sample_vec[i] - max_vec[i])
        total = d_min + d_mid + d_max
        vote_weights['LOW'] += weights[i] * (1 - d_min/total)
        vote_weights['MID'] += weights[i] * (1 - d_mid/total)
        vote_weights['HIGH'] += weights[i] * (1 - d_max/total)
    total_weight = sum(vote_weights.values())
    if total_weight == 0: return vals[1]
    return (vote_weights['LOW']*vals[0] + vote_weights['MID']*vals[1] + vote_weights['HIGH']*vals[2]) / total_weight

def logic12_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
    sample_vec = extract_bands(sample, indices)
    if blank is not None:
        blank_vec = extract_bands(blank, indices)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    V = mid_vec - min_vec
    S = sample_vec - min_vec
    dot_product = np.dot(S, V)
    norm_sq = np.dot(V, V)
    if norm_sq == 0: return vals[1]
    alpha = np.clip(dot_product / norm_sq, 0, 1)
    return vals[0] + alpha * (vals[2] - vals[0])

def logic13_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
    sample_vec = extract_bands(sample, indices)
    if blank is not None:
        blank_vec = extract_bands(blank, indices)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    V1 = mid_vec - min_vec
    V1_norm = V1 / (np.linalg.norm(V1) + 1e-10)
    V2 = max_vec - min_vec
    V2 = V2 - np.dot(V2, V1_norm) * V1_norm
    V2_norm = V2 / (np.linalg.norm(V2) + 1e-10)
    S = sample_vec - min_vec
    alpha = np.dot(S, V1_norm)
    beta = np.dot(S, V2_norm)
    total = abs(alpha) + abs(beta) + 1e-10
    return (abs(alpha) * vals[1] + abs(beta) * vals[2]) / total

def logic14_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
    sample_vec = extract_bands(sample, indices)
    if blank is not None:
        blank_vec = extract_bands(blank, indices)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    V = mid_vec - min_vec
    S = sample_vec - min_vec
    alpha = np.clip(np.dot(S, V) / (np.dot(V, V) + 1e-10), 0, 1)
    proj_pred = vals[0] + alpha * (vals[2] - vals[0])
    V_norm = V / (np.linalg.norm(V) + 1e-10)
    proj_length = np.dot(S, V_norm)
    orth_dist = np.linalg.norm(S - proj_length * V_norm)
    confidence = 1 / (1 + orth_dist)
    d_min = euclidean(sample_vec, min_vec) + 1e-10
    d_mid = euclidean(sample_vec, mid_vec) + 1e-10
    d_max = euclidean(sample_vec, max_vec) + 1e-10
    idw_pred = idw_predict([d_min, d_mid, d_max], vals, power=1.0)
    return confidence * proj_pred + (1 - confidence) * idw_pred

def logic15_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
    sample_vec = extract_bands(sample, indices)
    if blank is not None:
        blank_vec = extract_bands(blank, indices)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    V1 = mid_vec - min_vec
    S1 = sample_vec - min_vec
    alpha1 = np.clip(np.dot(S1, V1) / (np.dot(V1, V1) + 1e-10), 0, 1)
    pred1 = vals[0] + alpha1 * (vals[1] - vals[0])
    V2 = max_vec - mid_vec
    S2 = sample_vec - mid_vec
    alpha2 = np.clip(np.dot(S2, V2) / (np.dot(V2, V2) + 1e-10), 0, 1)
    pred2 = vals[1] + alpha2 * (vals[2] - vals[1])
    V3 = max_vec - min_vec
    S3 = sample_vec - min_vec
    alpha3 = np.clip(np.dot(S3, V3) / (np.dot(V3, V3) + 1e-10), 0, 1)
    pred3 = vals[0] + alpha3 * (vals[2] - vals[0])
    return np.mean([pred1, pred2, pred3])

def logic16_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
    sample_vec = extract_bands(sample, indices)
    if blank is not None:
        blank_vec = extract_bands(blank, indices)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    spread = np.abs(max_vec - min_vec) + 1e-10
    weights = spread / spread.sum()
    sample_idx = np.sum(sample_vec * weights)
    min_idx = np.sum(min_vec * weights)
    mid_idx = np.sum(mid_vec * weights)
    max_idx = np.sum(max_vec * weights)
    if max_idx - min_idx > 1e-10:
        t = (sample_idx - min_idx) / (max_idx - min_idx)
    else: t = 0.5
    t = np.clip(t, 0, 1)
    if t <= 0.5:
        return vals[0] + (t / 0.5) * (vals[1] - vals[0])
    else:
        return vals[1] + ((t - 0.5) / 0.5) * (vals[2] - vals[1])

def logic17_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
    sample_vec = extract_bands(sample, indices)
    if blank is not None:
        blank_vec = extract_bands(blank, indices)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    weights = np.abs(max_vec - min_vec) / (np.abs(max_vec - min_vec).sum() + 1e-10)
    try:
        corr_sample_min = pearsonr(sample_vec, min_vec)[0]
        corr_sample_mid = pearsonr(sample_vec, mid_vec)[0]
        corr_sample_max = pearsonr(sample_vec, max_vec)[0]
        corr_weights = np.array([abs(corr_sample_min), abs(corr_sample_mid), abs(corr_sample_max)])
        corr_weights = corr_weights / (corr_weights.sum() + 1e-10)
    except:
        corr_weights = np.ones(3) / 3
    sample_idx = np.sum(sample_vec * weights)
    min_idx = np.sum(min_vec * weights)
    mid_idx = np.sum(mid_vec * weights)
    max_idx = np.sum(max_vec * weights)
    if max_idx - min_idx > 1e-10: t = (sample_idx - min_idx) / (max_idx - min_idx)
    else: t = 0.5
    t = np.clip(t, 0, 1)
    sni_pred = vals[0] + t * (vals[2] - vals[0])
    corr_pred = (corr_weights[0]*vals[0] + corr_weights[1]*vals[1] + corr_weights[2]*vals[2])
    return 0.6 * sni_pred + 0.4 * corr_pred

def logic18_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
    sample_vec = extract_bands(sample, indices)
    if blank is not None:
        blank_vec = extract_bands(blank, indices)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    def compute_ratios(signal):
        ratios = []
        for i in range(len(signal)-1):
            for j in range(i+1, len(signal)):
                if signal[j] > 0: ratios.append(signal[i] / signal[j])
        return np.mean(ratios) if ratios else 0
    sample_ratio = compute_ratios(sample_vec)
    min_ratio = compute_ratios(min_vec)
    mid_ratio = compute_ratios(mid_vec)
    max_ratio = compute_ratios(max_vec)
    d_min = abs(sample_ratio - min_ratio) + 1e-10
    d_mid = abs(sample_ratio - mid_ratio) + 1e-10
    d_max = abs(sample_ratio - max_ratio) + 1e-10
    return idw_predict([d_min, d_mid, d_max], vals, power=2.0)

def logic19_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
    sample_vec = extract_bands(sample, indices)
    if blank is not None:
        blank_vec = extract_bands(blank, indices)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    sample_log = np.log(np.maximum(sample_vec, 0) + 1e-10)
    min_log = np.log(np.maximum(min_vec, 0) + 1e-10)
    mid_log = np.log(np.maximum(mid_vec, 0) + 1e-10)
    max_log = np.log(np.maximum(max_vec, 0) + 1e-10)
    d_min = euclidean(sample_log, min_log) + 1e-10
    d_mid = euclidean(sample_log, mid_log) + 1e-10
    d_max = euclidean(sample_log, max_log) + 1e-10
    return idw_predict([d_min, d_mid, d_max], vals, power=1.0)

def logic20_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
    sample_vec = extract_bands(sample, indices)
    if blank is not None:
        blank_vec = extract_bands(blank, indices)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    if len(sample_vec) < 3: return vals[1]
    r1 = sample_vec[0] / (sample_vec[-1] + 1e-10)
    r2 = sample_vec[1] / (sample_vec[-2] + 1e-10) if len(sample_vec) >= 2 else 0
    r3 = sample_vec[2] / (sample_vec[-3] + 1e-10) if len(sample_vec) >= 3 else 0
    sample_avg = np.mean([r1, r2, r3])
    min_ratios = np.array([min_vec[0]/(min_vec[-1]+1e-10), min_vec[1]/(min_vec[-2]+1e-10) if len(min_vec)>=2 else 0, min_vec[2]/(min_vec[-3]+1e-10) if len(min_vec)>=3 else 0])
    min_avg = np.mean(min_ratios)
    max_ratios = np.array([max_vec[0]/(max_vec[-1]+1e-10), max_vec[1]/(max_vec[-2]+1e-10) if len(max_vec)>=2 else 0, max_vec[2]/(max_vec[-3]+1e-10) if len(max_vec)>=3 else 0])
    max_avg = np.mean(max_ratios)
    if max_avg - min_avg > 1e-10: t = (sample_avg - min_avg) / (max_avg - min_avg)
    else: t = 0.5
    t = np.clip(t, 0, 1)
    return vals[0] + t * (vals[2] - vals[0])

def logic21_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
    sample_vec = extract_bands(sample, indices)
    if blank is not None:
        blank_vec = extract_bands(blank, indices)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    sample_ndi = (np.max(sample_vec) - np.min(sample_vec)) / (np.max(sample_vec) + np.min(sample_vec) + 1e-10)
    min_ndi = (np.max(min_vec) - np.min(min_vec)) / (np.max(min_vec) + np.min(min_vec) + 1e-10)
    mid_ndi = (np.max(mid_vec) - np.min(mid_vec)) / (np.max(mid_vec) + np.min(mid_vec) + 1e-10)
    max_ndi = (np.max(max_vec) - np.min(max_vec)) / (np.max(max_vec) + np.min(max_vec) + 1e-10)
    d_min = abs(sample_ndi - min_ndi) + 1e-10
    d_mid = abs(sample_ndi - mid_ndi) + 1e-10
    d_max = abs(sample_ndi - max_ndi) + 1e-10
    return idw_predict([d_min, d_mid, d_max], vals, power=2.0)

def logic22_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices, use_all=True)
    sample_vec = extract_bands(sample, indices, use_all=True)
    if blank is not None:
        blank_vec = np.array(blank)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    sample_deriv = np.diff(sample_vec)
    min_deriv = np.diff(min_vec)
    mid_deriv = np.diff(mid_vec)
    max_deriv = np.diff(max_vec)
    d_min = euclidean(sample_deriv, min_deriv) + 1e-10
    d_mid = euclidean(sample_deriv, mid_deriv) + 1e-10
    d_max = euclidean(sample_deriv, max_deriv) + 1e-10
    return idw_predict([d_min, d_mid, d_max], vals, power=1.0)

def logic23_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices, use_all=True)
    sample_vec = extract_bands(sample, indices, use_all=True)
    if blank is not None:
        blank_vec = np.array(blank)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    if len(sample_vec) < 3: return vals[1]
    sample_deriv2 = np.diff(np.diff(sample_vec))
    min_deriv2 = np.diff(np.diff(min_vec))
    mid_deriv2 = np.diff(np.diff(mid_vec))
    max_deriv2 = np.diff(np.diff(max_vec))
    d_min = euclidean(sample_deriv2, min_deriv2) + 1e-10
    d_mid = euclidean(sample_deriv2, mid_deriv2) + 1e-10
    d_max = euclidean(sample_deriv2, max_deriv2) + 1e-10
    return idw_predict([d_min, d_mid, d_max], vals, power=1.0)

def logic24_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices, use_all=True)
    sample_vec = extract_bands(sample, indices, use_all=True)
    if blank is not None:
        blank_vec = np.array(blank)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    def centroid(signal):
        if np.sum(signal) == 0: return 0
        indices_arr = np.arange(len(signal))
        return np.sum(indices_arr * signal) / np.sum(signal)
    cent_sample = centroid(sample_vec)
    cent_min = centroid(min_vec)
    cent_mid = centroid(mid_vec)
    cent_max = centroid(max_vec)
    if cent_max - cent_min > 1e-10: t = (cent_sample - cent_min) / (cent_max - cent_min)
    else: t = 0.5
    t = np.clip(t, 0, 1)
    return vals[0] + t * (vals[2] - vals[0])

def logic25_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices, use_all=True)
    sample_vec = extract_bands(sample, indices, use_all=True)
    if blank is not None:
        blank_vec = np.array(blank)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    energy_sample = np.sum(sample_vec**2)
    energy_min = np.sum(min_vec**2)
    energy_mid = np.sum(mid_vec**2)
    energy_max = np.sum(max_vec**2)
    if energy_max - energy_min > 1e-10: t = (energy_sample - energy_min) / (energy_max - energy_min)
    else: t = 0.5
    t = np.clip(t, 0, 1)
    return vals[0] + t * (vals[2] - vals[0])

def logic26_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices, use_all=True)
    sample_vec = extract_bands(sample, indices, use_all=True)
    if blank is not None:
        blank_vec = np.array(blank)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    def spectral_entropy(signal):
        prob = np.abs(signal) / (np.sum(np.abs(signal)) + 1e-10)
        return -np.sum(prob * np.log(prob + 1e-10))
    ent_sample = spectral_entropy(sample_vec)
    ent_min = spectral_entropy(min_vec)
    ent_mid = spectral_entropy(mid_vec)
    ent_max = spectral_entropy(max_vec)
    if ent_max - ent_min > 1e-10: t = (ent_sample - ent_min) / (ent_max - ent_min)
    else: t = 0.5
    t = np.clip(t, 0, 1)
    return vals[0] + t * (vals[2] - vals[0])

def logic27_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices, use_all=True)
    sample_vec = extract_bands(sample, indices, use_all=True)
    if blank is not None:
        blank_vec = np.array(blank)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    try:
        cal_matrix = np.array([min_vec, mid_vec, max_vec])
        scaler = StandardScaler()
        cal_scaled = scaler.fit_transform(cal_matrix)
        pca = PCA(n_components=min(2, len(cal_matrix)-1))
        pca.fit(cal_scaled)
        sample_scaled = scaler.transform(sample_vec.reshape(1, -1))
        sample_pca = pca.transform(sample_scaled)
        cal_pca = pca.transform(cal_scaled)
        d_min = euclidean(sample_pca[0], cal_pca[0]) + 1e-10
        d_mid = euclidean(sample_pca[0], cal_pca[1]) + 1e-10
        d_max = euclidean(sample_pca[0], cal_pca[2]) + 1e-10
    except:
        d_min = euclidean(sample_vec, min_vec) + 1e-10
        d_mid = euclidean(sample_vec, mid_vec) + 1e-10
        d_max = euclidean(sample_vec, max_vec) + 1e-10
    return idw_predict([d_min, d_mid, d_max], vals, power=1.5)

def logic28_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
    sample_vec = extract_bands(sample, indices)
    if blank is not None:
        blank_vec = extract_bands(blank, indices)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    ladder_values = np.linspace(vals[0], vals[2], 100)
    min_log = np.log(np.maximum(min_vec, 0) + 1e-10)
    max_log = np.log(np.maximum(max_vec, 0) + 1e-10)
    synthetic_spectra = []
    for t in np.linspace(0, 1, 100):
        synth = np.exp((1-t)*min_log + t*max_log)
        synthetic_spectra.append(synth)
    distances = [euclidean(sample_vec, synth) + 1e-10 for synth in synthetic_spectra]
    nearest_idx = np.argsort(distances)[:5]
    weights = 1 / np.array(distances)[nearest_idx]
    weights = weights / weights.sum()
    return np.sum(weights * np.array(ladder_values)[nearest_idx])

def logic29_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
    sample_vec = extract_bands(sample, indices)
    if blank is not None:
        blank_vec = extract_bands(blank, indices)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
    d_min = euclidean(sample_vec, min_vec) + 1e-10
    d_mid = euclidean(sample_vec, mid_vec) + 1e-10
    d_max = euclidean(sample_vec, max_vec) + 1e-10
    pred1 = idw_predict([d_min, d_mid, d_max], vals, power=1.0)
    V = mid_vec - min_vec
    S = sample_vec - min_vec
    alpha = np.clip(np.dot(S, V) / (np.dot(V, V) + 1e-10), 0, 1)
    pred2 = vals[0] + alpha * (vals[2] - vals[0])
    sim_min = max(0, 1 - cosine(sample_vec, min_vec)) + 1e-10
    sim_mid = max(0, 1 - cosine(sample_vec, mid_vec)) + 1e-10
    sim_max = max(0, 1 - cosine(sample_vec, max_vec)) + 1e-10
    pred3 = (sim_min*vals[0] + sim_mid*vals[1] + sim_max*vals[2]) / (sim_min + sim_mid + sim_max)
    votes = {'LOW': 0, 'MID': 0, 'HIGH': 0}
    for i in range(len(indices)):
        d_min_i = abs(sample_vec[i] - min_vec[i])
        d_mid_i = abs(sample_vec[i] - mid_vec[i])
        d_max_i = abs(sample_vec[i] - max_vec[i])
        if d_min_i <= d_mid_i and d_min_i <= d_max_i: votes['LOW'] += 1
        elif d_mid_i <= d_min_i and d_mid_i <= d_max_i: votes['MID'] += 1
        else: votes['HIGH'] += 1
    total = sum(votes.values())
    pred4 = (votes['LOW']*vals[0] + votes['MID']*vals[1] + votes['HIGH']*vals[2]) / total if total > 0 else vals[1]
    preds = np.array([pred1, pred2, pred3, pred4])
    std_pred = np.std(preds)
    confidences = 1 / (1 + std_pred)
    weights = [confidences, 1-confidences, 0.5*(1-confidences), 0.3*(1-confidences)]
    weights = np.array(weights) / np.sum(weights)
    return np.sum(weights * preds)

def logic30_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    blank = get_blank(d, nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
    sample_vec = extract_bands(sample, indices)
    if blank is not None:
        blank_vec = extract_bands(blank, indices)
        sample_vec = blank_correct(sample_vec, blank_vec)
        min_vec = blank_correct(min_vec, blank_vec)
        mid_vec = blank_correct(mid_vec, blank_vec)
        max_vec = blank_correct(max_vec, blank_vec)
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
    min_log = np.log(np.maximum(min_vec, 0) + 1e-10)
    max_log = np.log(np.maximum(max_vec, 0) + 1e-10)
    synth_spectra = [np.exp((1-t)*min_log + t*max_log) for t in np.linspace(0, 1, 50)]
    distances = [euclidean(sample_vec, synth) + 1e-10 for synth in synth_spectra]
    nearest_idx = np.argsort(distances)[:3]
    w = 1 / np.array(distances)[nearest_idx]
    pred5 = np.sum(w * np.array(ladder_values)[nearest_idx]) / np.sum(w)
    preds = np.array([pred1, pred2, pred3, pred4, pred5])
    mean_pred = np.mean(preds)
    std_pred = np.std(preds)
    valid_preds = preds[np.abs(preds - mean_pred) < 2 * std_pred]
    if len(valid_preds) == 0: return mean_pred
    valid_preds = np.clip(valid_preds, vals[0], vals[2])
    return np.mean(valid_preds)

FEATURE_NAMES_LIST = ['nm_410', 'nm_435', 'nm_460', 'nm_485', 'nm_510', 'nm_535', 'nm_560', 'nm_585', 'nm_610', 'nm_645', 'nm_680', 'nm_705', 'nm_730', 'nm_760', 'nm_810', 'nm_860', 'nm_900', 'nm_940', 'nm_320', 'nm_280', 'nm_200']

def wrap_details(val, name, target, override_features=None):
    try:
        val_float = float(val)
        if np.isnan(val_float): val_float = 0.0
    except:
        val_float = 0.0
        
    if override_features is not None:
        features_used = override_features
    else:
        indices = get_indices(target)
        features_used = [FEATURE_NAMES_LIST[i] for i in indices] if indices else []
    
    return {
        "value": val_float,
        "features_used": features_used,
        "details": {
            "Step 1 - Algorithm": name,
            "Step 2 - Target Nutrient": target,
            "Step 3 - Wavelengths Used": str(features_used),
            "Step 4 - Reference Values": str(get_vals(target)),
            "Step 5 - Raw Prediction": f"{val_float:.4f}"
        }
    }

# ==========================================
# 17 ADDITIONAL LOGICS (M31 - M47)
# ==========================================

from scipy.fft import dct, fft
import pywt
from scipy.signal import savgol_filter

# L1: Mid Anchor Pred
def logic31_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
    sample_vec = extract_bands(sample, indices)
    d_min = euclidean(sample_vec, min_vec) + 1e-10
    d_mid = euclidean(sample_vec, mid_vec) + 1e-10
    d_max = euclidean(sample_vec, max_vec) + 1e-10
    return idw_predict([d_min, d_mid, d_max], vals, power=1.0)
    
# L2: Mid Log Pred
def logic32_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
    sample_vec = extract_bands(sample, indices)
    sample_log = np.log1p(np.maximum(sample_vec, 0))
    min_log = np.log1p(np.maximum(min_vec, 0))
    mid_log = np.log1p(np.maximum(mid_vec, 0))
    max_log = np.log1p(np.maximum(max_vec, 0))
    d_min = euclidean(sample_log, min_log) + 1e-10
    d_mid = euclidean(sample_log, mid_log) + 1e-10
    d_max = euclidean(sample_log, max_log) + 1e-10
    return idw_predict([d_min, d_mid, d_max], vals, power=1.0)
    
# L3: Normalization Pred
def logic33_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
    sample_vec = extract_bands(sample, indices)
    def norm(s): return (s - np.min(s)) / (np.max(s) - np.min(s) + 1e-10)
    d_min = euclidean(norm(sample_vec), norm(min_vec)) + 1e-10
    d_mid = euclidean(norm(sample_vec), norm(mid_vec)) + 1e-10
    d_max = euclidean(norm(sample_vec), norm(max_vec)) + 1e-10
    return idw_predict([d_min, d_mid, d_max], vals, power=1.0)
    
# L4: Sensitivity Pred
def logic34_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices, use_all=True)
    sample_vec = extract_bands(sample, indices, use_all=True)
    d_min = euclidean(np.gradient(sample_vec), np.gradient(min_vec)) + 1e-10
    d_mid = euclidean(np.gradient(sample_vec), np.gradient(mid_vec)) + 1e-10
    d_max = euclidean(np.gradient(sample_vec), np.gradient(max_vec)) + 1e-10
    return idw_predict([d_min, d_mid, d_max], vals, power=1.0)
    
# L5: Matrix Correction
def logic35_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices, use_all=True)
    sample_vec = extract_bands(sample, indices, use_all=True)
    corr_matrix = np.corrcoef(np.array([min_vec, mid_vec, max_vec]).T)
    corr_matrix = np.nan_to_num(corr_matrix)
    sample_corr = np.dot(sample_vec, corr_matrix)
    min_corr = np.dot(min_vec, corr_matrix)
    mid_corr = np.dot(mid_vec, corr_matrix)
    max_corr = np.dot(max_vec, corr_matrix)
    d_min = euclidean(sample_corr, min_corr) + 1e-10
    d_mid = euclidean(sample_corr, mid_corr) + 1e-10
    d_max = euclidean(sample_corr, max_corr) + 1e-10
    return idw_predict([d_min, d_mid, d_max], vals, power=1.0)
    
# L6: Residual Pred
def logic36_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
    sample_vec = extract_bands(sample, indices)
    d_min = euclidean(sample_vec, min_vec) + 1e-10
    d_mid = euclidean(sample_vec, mid_vec) + 1e-10
    d_max = euclidean(sample_vec, max_vec) + 1e-10
    m1_pred = idw_predict([d_min, d_mid, d_max], vals, power=1.0)
    distances = [d_min, d_mid, d_max]
    nearest_idx = np.argmin(distances)
    residual = vals[nearest_idx] - m1_pred
    return m1_pred + residual * 0.5
    
# L7: Position Pred
def logic37_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
    sample_vec = extract_bands(sample, indices)
    distances = [euclidean(sample_vec, min_vec), euclidean(sample_vec, mid_vec), euclidean(sample_vec, max_vec)]
    nearest_idx = np.argmin(distances)
    return vals[nearest_idx]
    
# L8: Position Mid Pred
def logic38_predict(sample, d, nutrient):
    pos_pred = logic37_predict(sample, d, nutrient)
    vals = get_vals(nutrient)
    return (pos_pred + vals[1]) / 2.0
    
# L9: Relative Ranking Pred
def logic39_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices)
    sample_vec = extract_bands(sample, indices)
    distances = [euclidean(sample_vec, min_vec), euclidean(sample_vec, mid_vec), euclidean(sample_vec, max_vec)]
    sorted_idx = np.argsort(distances)
    weights = [1.0/1, 1.0/2, 1.0/3]
    total = sum(weights)
    return sum(weights[i] * vals[sorted_idx[i]] for i in range(3)) / total
    
# L10: Hybrid Pred
def logic40_predict(sample, d, nutrient):
    res = [
        logic31_predict(sample, d, nutrient),
        logic32_predict(sample, d, nutrient),
        logic33_predict(sample, d, nutrient),
        logic34_predict(sample, d, nutrient),
        logic37_predict(sample, d, nutrient),
        logic39_predict(sample, d, nutrient)
    ]
    return np.mean(res)
    
# DCT
def logic41_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices, use_all=True)
    sample_vec = extract_bands(sample, indices, use_all=True)
    d_min = euclidean(dct(sample_vec, norm='ortho')[:10], dct(min_vec, norm='ortho')[:10]) + 1e-10
    d_mid = euclidean(dct(sample_vec, norm='ortho')[:10], dct(mid_vec, norm='ortho')[:10]) + 1e-10
    d_max = euclidean(dct(sample_vec, norm='ortho')[:10], dct(max_vec, norm='ortho')[:10]) + 1e-10
    return idw_predict([d_min, d_mid, d_max], vals)
    
# DCT Modified
def logic42_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices, use_all=True)
    sample_vec = extract_bands(sample, indices, use_all=True)
    sample_log = np.log1p(np.maximum(sample_vec, 0))
    min_log = np.log1p(np.maximum(min_vec, 0))
    mid_log = np.log1p(np.maximum(mid_vec, 0))
    max_log = np.log1p(np.maximum(max_vec, 0))
    d_min = euclidean(dct(sample_log, norm='ortho')[:10], dct(min_log, norm='ortho')[:10]) + 1e-10
    d_mid = euclidean(dct(sample_log, norm='ortho')[:10], dct(mid_log, norm='ortho')[:10]) + 1e-10
    d_max = euclidean(dct(sample_log, norm='ortho')[:10], dct(max_log, norm='ortho')[:10]) + 1e-10
    return idw_predict([d_min, d_mid, d_max], vals)
    
# DWT
def logic43_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices, use_all=True)
    sample_vec = extract_bands(sample, indices, use_all=True)
    try:
        sample_dwt = pywt.wavedec(sample_vec, 'db2', level=2)[0]
        min_dwt = pywt.wavedec(min_vec, 'db2', level=2)[0]
        mid_dwt = pywt.wavedec(mid_vec, 'db2', level=2)[0]
        max_dwt = pywt.wavedec(max_vec, 'db2', level=2)[0]
    except:
        sample_dwt, min_dwt, mid_dwt, max_dwt = sample_vec, min_vec, mid_vec, max_vec
    d_min = euclidean(sample_dwt, min_dwt) + 1e-10
    d_mid = euclidean(sample_dwt, mid_dwt) + 1e-10
    d_max = euclidean(sample_dwt, max_dwt) + 1e-10
    return idw_predict([d_min, d_mid, d_max], vals)
    
# DWT Modified (Detrended)
def logic44_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices, use_all=True)
    sample_vec = extract_bands(sample, indices, use_all=True)
    x = np.arange(len(sample_vec))
    sample_detrend = sample_vec - np.polyval(np.polyfit(x, sample_vec, 1), x)
    min_detrend = min_vec - np.polyval(np.polyfit(x, min_vec, 1), x)
    mid_detrend = mid_vec - np.polyval(np.polyfit(x, mid_vec, 1), x)
    max_detrend = max_vec - np.polyval(np.polyfit(x, max_vec, 1), x)
    try:
        sample_dwt = pywt.wavedec(sample_detrend, 'db2', level=2)[0]
        min_dwt = pywt.wavedec(min_detrend, 'db2', level=2)[0]
        mid_dwt = pywt.wavedec(mid_detrend, 'db2', level=2)[0]
        max_dwt = pywt.wavedec(max_detrend, 'db2', level=2)[0]
    except:
        sample_dwt, min_dwt, mid_dwt, max_dwt = sample_detrend, min_detrend, mid_detrend, max_detrend
    d_min = euclidean(sample_dwt, min_dwt) + 1e-10
    d_mid = euclidean(sample_dwt, mid_dwt) + 1e-10
    d_max = euclidean(sample_dwt, max_dwt) + 1e-10
    return idw_predict([d_min, d_mid, d_max], vals)
    
# FFT
def logic45_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices, use_all=True)
    sample_vec = extract_bands(sample, indices, use_all=True)
    sample_fft = np.abs(fft(sample_vec))[:10]
    min_fft = np.abs(fft(min_vec))[:10]
    mid_fft = np.abs(fft(mid_vec))[:10]
    max_fft = np.abs(fft(max_vec))[:10]
    d_min = euclidean(sample_fft, min_fft) + 1e-10
    d_mid = euclidean(sample_fft, mid_fft) + 1e-10
    d_max = euclidean(sample_fft, max_fft) + 1e-10
    return idw_predict([d_min, d_mid, d_max], vals)
    
# FFT Modified
def logic46_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices, use_all=True)
    sample_vec = extract_bands(sample, indices, use_all=True)
    sample_log = np.log1p(np.maximum(sample_vec, 0))
    min_log = np.log1p(np.maximum(min_vec, 0))
    mid_log = np.log1p(np.maximum(mid_vec, 0))
    max_log = np.log1p(np.maximum(max_vec, 0))
    sample_fft = np.abs(fft(sample_log))[:10]
    min_fft = np.abs(fft(min_log))[:10]
    mid_fft = np.abs(fft(mid_log))[:10]
    max_fft = np.abs(fft(max_log))[:10]
    d_min = euclidean(sample_fft, min_fft) + 1e-10
    d_mid = euclidean(sample_fft, mid_fft) + 1e-10
    d_max = euclidean(sample_fft, max_fft) + 1e-10
    return idw_predict([d_min, d_mid, d_max], vals)
    
# SG_SV
def logic47_predict(sample, d, nutrient):
    indices = get_indices(nutrient)
    vals = get_vals(nutrient)
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, indices, use_all=True)
    sample_vec = extract_bands(sample, indices, use_all=True)
    try:
        sample_sg = savgol_filter(sample_vec, window_length=5, polyorder=2, deriv=2)
        min_sg = savgol_filter(min_vec, window_length=5, polyorder=2, deriv=2)
        mid_sg = savgol_filter(mid_vec, window_length=5, polyorder=2, deriv=2)
        max_sg = savgol_filter(max_vec, window_length=5, polyorder=2, deriv=2)
    except:
        sample_sg = np.gradient(np.gradient(sample_vec))
        min_sg = np.gradient(np.gradient(min_vec))
        mid_sg = np.gradient(np.gradient(mid_vec))
        max_sg = np.gradient(np.gradient(max_vec))
    sample_energy = np.sum(sample_sg**2)
    min_energy = np.sum(min_sg**2)
    mid_energy = np.sum(mid_sg**2)
    max_energy = np.sum(max_sg**2)
    
    d_min = abs(sample_energy - min_energy) + 1e-10
    d_mid = abs(sample_energy - mid_energy) + 1e-10
    d_max = abs(sample_energy - max_energy) + 1e-10
    return idw_predict([d_min, d_mid, d_max], vals)


# ==========================================
# M48: Custom IP Euclidean Distance Logic
# ==========================================
import numpy as np

def logic48_predict(sample, d, nutrient):
    # Mapping based on standard 21 wavelengths
    # WAVELENGTH_ORDER = [410, 435, 460, 485, 510, 535, 560, 585, 610, 645, 680, 705, 730, 760, 810, 860, 900, 940, 320, 280, 200]
    # A=0, B=1, C=2, D=3, E=4, F=5, G=6, H=7, I=8, J=9, K=10, L=11
    # R=17 (940nm)
    # U=18 (320nm), V=19 (280nm), W=20 (200nm)
    # Assuming S=16 (900nm), T=14 (810nm) as placeholders if undefined
    
    def calc_ip1(s):
        A, B, C, D, E, F, G, H, R = s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], s[17]
        group = [A, B, C, D, E, F, G, H, R]
        return (sum(x**2 for x in group) / (sum(group) + 1e-10)) / 100.0

    def calc_ip2(s):
        I, J, K, L = s[8], s[9], s[10], s[11]
        U, V, W = s[18], s[19], s[20]
        S, T = s[16], s[14]
        group = [I, S, J, T, U, V, W, K, L]
        return (sum(x**2 for x in group) / (sum(group) + 1e-10)) / 100.0

    def calc_ip3(s):
        U, V, W = s[18], s[19], s[20]
        group = [U, V, W]
        return (sum(x**2 for x in group) / (sum(group) + 1e-10)) / 100.0

    # Calculate IP for the sample
    sample_ip1 = calc_ip1(sample)
    sample_ip2 = calc_ip2(sample)
    sample_ip3 = calc_ip3(sample)
    
    # Get calibration vectors for the target nutrient
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, list(range(21)), use_all=True)
    vals = get_vals(nutrient)
    
    # Calculate IP for the calibration points
    cal_points = []
    for vec in [min_vec, mid_vec, max_vec]:
        cal_points.append({
            "ip1": calc_ip1(vec),
            "ip2": calc_ip2(vec),
            "ip3": calc_ip3(vec)
        })
        
    # Calculate Euclidean distance to each calibration point
    distances = []
    for cp in cal_points:
        d_val = np.sqrt(
            (sample_ip1 - cp["ip1"])**2 + 
            (sample_ip2 - cp["ip2"])**2 + 
            (sample_ip3 - cp["ip3"])**2
        )
        distances.append(d_val)
        
    # Inverse Distance Weighting
    weights = [1.0 / (d_val**2 + 1e-10) for d_val in distances]
    total_weight = sum(weights)
    norm_weights = [w / total_weight for w in weights]
    
    # Final predicted value
    prediction = sum(norm_weights[i] * vals[i] for i in range(3))
    
    return prediction


# ==========================================
# M49: IP Zone Classification Logic
# ==========================================
def logic49_predict(sample, d, nutrient):
    # Mapping based on standard 21 wavelengths
    A = sample[0]   # 410
    B = sample[1]   # 435
    C = sample[2]   # 460
    D = sample[3]   # 485
    E = sample[4]   # 510
    F = sample[5]   # 535
    G = sample[6]   # 560
    H = sample[7]   # 585
    I = sample[8]   # 610
    J = sample[9]   # 645
    S680 = sample[10] # 680
    L = sample[11]  # 705
    T = sample[12]  # 730 (defaulting T)
    K900 = sample[16] # 900
    R = sample[17]  # 940
    U320 = sample[18] # 320
    V280 = sample[19] # 280
    W200 = sample[20] # 200

    # 1.1 IPS Formulas
    def calc_ips(group):
        return (sum(x**2 for x in group) / (sum(group) + 1e-10)) / 100.0

    group1 = [A, B, C, D, E, F, G, H, R]
    group2 = [I, S680, J, T, U320, V280, W200, K900, L]
    group3 = [U320, V280, W200]

    ip1 = calc_ips(group1)
    ip2 = calc_ips(group2)
    ip3 = calc_ips(group3)

    # 1.3 Special Indices
    N_ip1 = (F / (J + 1e-10)) / 10.0
    N_ip3 = (F - H) / (F + H + 1e-10)
    P_ip1 = K900 / (S680 + 1e-10)
    P_ip2 = W200 / (S680 + 1e-10)

    def clamp(val, min_val, max_val):
        return max(min_val, min(val, max_val))

    # Helper for calculating prediction from position
    def calc_pred(ip_val, norm_min, norm_max, zone_min, zone_max):
        position = (ip_val - norm_min) / ((norm_max - norm_min) + 1e-10)
        position = clamp(position, 0, 1)
        return zone_min + position * (zone_max - zone_min)

    def in_range(val, r_min, r_max):
        return r_min <= val <= r_max

    predicted = 0.0

    # 2. NUTRIENT CLASSIFICATION ZONES
    if nutrient == 'N':
        norm_min, norm_max = 0.293, 0.340
        if in_range(ip3, 0.324, 0.336) and in_range(N_ip1, 5.80, 6.20):
            predicted = calc_pred(ip3, norm_min, norm_max, 50, 100)
        elif in_range(ip3, 0.313, 0.324) and in_range(N_ip1, 5.90, 6.44):
            predicted = calc_pred(ip3, norm_min, norm_max, 100, 200)
        elif in_range(ip3, 0.309, 0.313) and in_range(N_ip1, 5.92, 6.20):
            predicted = calc_pred(ip3, norm_min, norm_max, 200, 350)
        elif in_range(ip3, 0.293, 0.309) and in_range(N_ip1, 5.72, 6.17):
            predicted = calc_pred(ip3, norm_min, norm_max, 350, 500)
        else:
            predicted = calc_pred(ip3, norm_min, norm_max, 50, 500)

    elif nutrient == 'P':
        norm_min, norm_max = 2.66, 2.90
        if ip1 > 2.78 and ip2 > 1.13:
            predicted = calc_pred(ip1, norm_min, norm_max, 450, 850)
        elif ip1 > 2.70 and ip2 > 1.11 and ip1 < 2.75:
            predicted = calc_pred(ip1, norm_min, norm_max, 280, 450)
        elif (ip1 > 2.69 and ip2 > 1.12 and ip1 < 2.70) or (ip1 > 2.74 and ip2 > 1.15):
            predicted = calc_pred(ip1, norm_min, norm_max, 180, 280)
        elif ip1 > 2.68 and ip2 > 1.12 and ip1 < 2.69:
            predicted = calc_pred(ip1, norm_min, norm_max, 120, 180)
        elif (ip1 > 2.70 and ip2 > 1.11 and ip1 < 2.71) or (ip1 > 2.79 and ip2 > 1.14) or (ip1 > 2.76 and ip2 > 1.13):
            predicted = calc_pred(ip1, norm_min, norm_max, 50, 80)
        elif (ip1 > 2.73 and ip2 > 1.15) or (ip1 > 2.74 and ip2 > 1.14) or (ip1 > 2.76 and ip2 > 1.14):
            predicted = calc_pred(ip1, norm_min, norm_max, 25, 50)
        elif (ip1 > 2.74 and ip2 > 1.16) or (ip1 > 2.75 and ip2 > 1.14):
            predicted = calc_pred(ip1, norm_min, norm_max, 10, 25)
        else:
            predicted = calc_pred(ip1, norm_min, norm_max, 2, 10)

    elif nutrient == 'K':
        norm_min, norm_max = 6.0, 11.7
        if in_range(ip1, 8.05, 11.73) and in_range(ip2, 3.76, 4.19) and in_range(ip3, 0.88, 5.37):
            predicted = calc_pred(ip1, norm_min, norm_max, 50, 100)
        elif in_range(ip1, 6.96, 9.84) and in_range(ip2, 3.50, 4.01) and in_range(ip3, 0.45, 3.03):
            predicted = calc_pred(ip1, norm_min, norm_max, 100, 200)
        elif in_range(ip1, 6.59, 9.50) and in_range(ip2, 3.31, 3.97) and in_range(ip3, 0.26, 2.15):
            predicted = calc_pred(ip1, norm_min, norm_max, 200, 350)
        elif in_range(ip1, 7.44, 8.85) and in_range(ip2, 3.49, 3.84) and in_range(ip3, 0.67, 1.81):
            predicted = calc_pred(ip1, norm_min, norm_max, 350, 500)
        elif in_range(ip1, 7.27, 11.29) and in_range(ip2, 3.45, 3.93) and in_range(ip3, 0.57, 5.44):
            predicted = calc_pred(ip1, norm_min, norm_max, 500, 1000)
        elif in_range(ip1, 6.97, 11.58) and in_range(ip2, 3.61, 4.17) and in_range(ip3, 0.41, 4.94):
            predicted = calc_pred(ip1, norm_min, norm_max, 1000, 5000)
        else:
            predicted = calc_pred(ip1, norm_min, norm_max, 50, 1000)

    elif nutrient == 'OC':
        norm_min, norm_max = 6.0, 11.7
        if ip1 < 7.5: predicted = calc_pred(ip1, norm_min, norm_max, 0.1, 0.6)
        elif ip1 < 9.5: predicted = calc_pred(ip1, norm_min, norm_max, 0.6, 1.0)
        else: predicted = calc_pred(ip1, norm_min, norm_max, 1.0, 1.6)

    elif nutrient == 'Ca':
        norm_min, norm_max = 6.0, 11.7
        if ip1 < 7.5: predicted = calc_pred(ip1, norm_min, norm_max, 7, 20)
        elif ip1 < 9.5: predicted = calc_pred(ip1, norm_min, norm_max, 20, 35)
        else: predicted = calc_pred(ip1, norm_min, norm_max, 35, 50)

    elif nutrient == 'Mg':
        norm_min, norm_max = 6.0, 11.7
        if ip1 < 7.0: predicted = calc_pred(ip1, norm_min, norm_max, 0, 5)
        elif ip1 < 8.5: predicted = calc_pred(ip1, norm_min, norm_max, 5, 10)
        else: predicted = calc_pred(ip1, norm_min, norm_max, 10, 35)

    elif nutrient == 'S':
        norm_min, norm_max = 6.0, 11.7
        if ip1 < 7.5: predicted = calc_pred(ip1, norm_min, norm_max, 0, 5)
        elif ip1 < 9.0: predicted = calc_pred(ip1, norm_min, norm_max, 5, 10)
        else: predicted = calc_pred(ip1, norm_min, norm_max, 10, 30)

    elif nutrient == 'Fe':
        norm_min, norm_max = 6.0, 11.7
        if ip1 < 7.5: predicted = calc_pred(ip1, norm_min, norm_max, 0, 30)
        elif ip1 < 9.5: predicted = calc_pred(ip1, norm_min, norm_max, 30, 60)
        else: predicted = calc_pred(ip1, norm_min, norm_max, 60, 130)

    elif nutrient == 'Mn':
        norm_min, norm_max = 6.0, 11.7
        if ip1 < 7.5: predicted = calc_pred(ip1, norm_min, norm_max, 0, 15)
        elif ip1 < 9.5: predicted = calc_pred(ip1, norm_min, norm_max, 15, 30)
        else: predicted = calc_pred(ip1, norm_min, norm_max, 30, 50)

    elif nutrient == 'Cu':
        norm_min, norm_max = 3.2, 4.2
        if ip2 < 3.9: predicted = calc_pred(ip2, norm_min, norm_max, 0, 2.0)
        else: predicted = calc_pred(ip2, norm_min, norm_max, 2.0, 5.0)

    elif nutrient == 'Zn':
        norm_min, norm_max = 6.0, 11.7
        if ip1 < 8.0: predicted = calc_pred(ip1, norm_min, norm_max, 0, 3.0)
        elif ip1 < 9.5: predicted = calc_pred(ip1, norm_min, norm_max, 3.0, 8.0)
        else: predicted = calc_pred(ip1, norm_min, norm_max, 8.0, 25.0)
        
    else:
        # Default fallback for B or any unexpected targets
        norm_min, norm_max = 6.0, 11.7
        predicted = calc_pred(ip1, norm_min, norm_max, 0.1, 2.0)

    return predicted


# ==========================================
# M50: Mahalanobis Distance Logic
# ==========================================
import numpy as np

def logic50_predict(sample, d, nutrient):
    import json
    import os
    # 1. Wavelengths
    A, B, C, D, E, F, G, H = sample[0:8]
    I, J, S680, L = sample[8], sample[9], sample[10], sample[11]
    T = sample[12]
    K900, R = sample[16], sample[17]
    U320, V280, W200 = sample[18], sample[19], sample[20]

    def calc_ips(group):
        return (sum(x**2 for x in group) / (sum(group) + 1e-10)) / 100.0

    ip1 = calc_ips([A, B, C, D, E, F, G, H, R])
    ip2 = calc_ips([I, S680, J, T, U320, V280, W200, K900, L])
    ip3 = calc_ips([U320, V280, W200])

    x = np.array([ip1, ip2, ip3])

    # Dynamically load nutrient specific matrices
    matrices_path = os.path.join('logics', 'implementations', 'advanced_matrices.json')
    try:
        with open(matrices_path, 'r') as mf:
            all_matrices = json.load(mf)
    except:
        all_matrices = {}
    
    nut_m = all_matrices.get(nutrient, all_matrices.get('N', {}))
    if not nut_m:
        return 0.0 # Fallback

    mu_low = np.array(nut_m['centroids']['Low'])
    inv_cov_low = np.array(nut_m['covariances']['Low'])

    mu_medium = np.array(nut_m['centroids']['Medium'])
    inv_cov_medium = np.array(nut_m['covariances']['Medium'])

    mu_high = np.array(nut_m['centroids']['High'])
    inv_cov_high = np.array(nut_m['covariances']['High'])

    def calc_mahalanobis(x, mu, inv_cov):
        diff = x - mu
        return np.dot(np.dot(diff.T, inv_cov), diff)

    d_low = calc_mahalanobis(x, mu_low, inv_cov_low)
    d_med = calc_mahalanobis(x, mu_medium, inv_cov_medium)
    d_high = calc_mahalanobis(x, mu_high, inv_cov_high)

    distances = {"Low": d_low, "Medium": d_med, "High": d_high}
    pred_class = min(distances, key=distances.get)

    min_dist = distances[pred_class]
    max_dist = max(distances.values())

    sri_ranges = nut_m['sri_ranges']
    val_min = sri_ranges[pred_class]['val_min']
    val_max = sri_ranges[pred_class]['val_max']

    position = (min_dist - 0.15) / (max_dist - 0.15 + 1e-10)
    position = max(0, min(position, 1))

    predicted = val_min + position * (val_max - val_min)
    return predicted


# ==========================================
# M51: SAM + SRI Classification Logic
# ==========================================
import numpy as np
import math

def logic51_predict(sample, d, nutrient):
    import json
    import os
    # 1. Wavelengths
    A, B, C, D, E, F, G, H = sample[0:8]
    I, J, S680, L = sample[8], sample[9], sample[10], sample[11]
    T = sample[12]
    K900, R = sample[16], sample[17]
    U320, V280, W200 = sample[18], sample[19], sample[20]

    def calc_ips(group):
        return (sum(x**2 for x in group) / (sum(group) + 1e-10)) / 100.0

    ip1 = calc_ips([A, B, C, D, E, F, G, H, R])
    ip2 = calc_ips([I, S680, J, T, U320, V280, W200, K900, L])
    ip3 = calc_ips([U320, V280, W200])

    sri = (ip1 * ip3) / (ip2 + 1e-10)

    matrices_path = os.path.join('logics', 'implementations', 'advanced_matrices.json')
    try:
        with open(matrices_path, 'r') as mf:
            all_matrices = json.load(mf)
    except:
        all_matrices = {}
    
    nut_m = all_matrices.get(nutrient, all_matrices.get('N', {}))
    if not nut_m:
        return 0.0

    c_low = np.array(nut_m['centroids']['Low'])
    c_med = np.array(nut_m['centroids']['Medium'])
    c_high = np.array(nut_m['centroids']['High'])
    v = np.array([ip1, ip2, ip3])

    def calc_sam(v, c):
        dot_val = np.dot(v, c)
        norm_v = np.linalg.norm(v)
        norm_c = np.linalg.norm(c)
        cos_theta = dot_val / ((norm_v * norm_c) + 1e-10)
        cos_theta = np.clip(cos_theta, -1.0, 1.0)
        return math.acos(cos_theta) * (180.0 / math.pi)

    angle_low = calc_sam(v, c_low)
    angle_med = calc_sam(v, c_med)
    angle_high = calc_sam(v, c_high)

    hr = nut_m['high_rules']
    pred_class = None
    if sri < hr['Group_B']['sri_threshold'] and ip1 < hr['Group_B']['ip1_threshold'] and ip3 < hr['Group_B']['ip3_threshold']:
        pred_class = "High"
    elif sri > hr['Group_A']['sri_threshold']:
        pred_class = "High"
    elif 3.0 <= sri <= 8.0:
        pred_class = "Low" if angle_low < angle_med else "Medium"
    else:
        angles = {"Low": angle_low, "Medium": angle_med, "High": angle_high}
        pred_class = min(angles, key=angles.get)
        if pred_class == "High":
            pred_class = "Low" if angle_low < angle_med else "Medium"

    sri_ranges = nut_m['sri_ranges']
    sri_min = sri_ranges[pred_class]['sri_min']
    sri_max = sri_ranges[pred_class]['sri_max']
    n_min = sri_ranges[pred_class]['val_min']
    n_max = sri_ranges[pred_class]['val_max']

    position = (sri - sri_min) / ((sri_max - sri_min) + 1e-10)
    position = max(0, min(position, 1))

    predicted = n_min + position * (n_max - n_min)
    return predicted
