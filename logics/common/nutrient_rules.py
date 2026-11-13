import math

THRESHOLDS = {
    "OC": {"Low": 0.5, "Medium": 0.75},
    "N": {"Low": 280, "Medium": 560},
    "P": {"Low": 22.9, "Medium": 56.34},
    "K": {"Low": 141, "Medium": 336},
    "Ca": {"Deficient": 1.5, "Medium": 0}, 
    "Mg": {"Deficient": 1.0, "Medium": 0},
    "S": {"Low": 30, "Medium": 40},
    "Fe": {"Low": 8.5, "Medium": 10.5},
    "Mn": {"Low": 7, "Medium": 9},
    "Cu": {"Low": 0.8, "Medium": 1.0},
    "Zn": {"Low": 1.2, "Medium": 1.8},
    "B": {"Low": 0.9, "Medium": 1.1}
}

NUTRIENT_LIMITS = {
    "OC": [0.1, 2.0],
    "N": [50, 800],
    "P": [2, 200],
    "K": [50, 1000],
    "Ca": [1, 100],
    "Mg": [0, 50],
    "S": [2, 250],
    "Fe": [1.0, 50],
    "Mn": [0.1, 25],
    "Cu": [0.1, 10],
    "Zn": [0.1, 10],
    "B": [0.1, 10]
}

def clamp(val, min_val, max_val):
    if min_val is None or max_val is None:
        return val
    return max(min_val, min(max_val, val))

def get_nutrient_status(nutrient, value):
    if nutrient not in THRESHOLDS:
        return "UNKNOWN"
    t = THRESHOLDS[nutrient]
    if nutrient in ["Ca", "Mg"]:
        lo = t.get("Deficient", 0)
        if value < lo:
            return "Deficient"
        else:
            return "Adequate"
    else:
        lo = t.get("Low", 0)
        mid = t.get("Medium", 0)
        if value < lo:
            return "LOW"
        elif value < mid:
            return "MEDIUM"
        else:
            return "HIGH"

def get_documented_limits(method_type, method_id, target=None):
    if method_type == "ml":
        return None, None, False, "NOT_DOCUMENTED"
    else:
        if target and target in NUTRIENT_LIMITS:
            limits = NUTRIENT_LIMITS[target]
            return limits[0], limits[1], True, f"Documented Nutrient Range for {target}"
        return None, None, False, "NOT_DOCUMENTED"

def soft_clamp(value, lo, hi, label, nutrient=None):
    if nutrient == 'Ca':
        value = value / 2.0
    
    range_size = hi - lo
    if range_size <= 0:
        return (lo + hi) / 2
    
    if label in ['Low', 'LOW', 'Deficient']:
        min_val = lo + (range_size * 0.20)
        max_val = lo + (range_size * 0.95)
        if value <= lo:
            deviation = (lo - value) / (range_size + 1e-10)
            normalized = 0.20 + (0.25 * min(deviation, 1.0))
            normalized = max(0.20, min(0.45, normalized))
        elif value >= hi:
            deviation = (value - hi) / (range_size + 1e-10)
            normalized = 0.50 + (0.40 * min(deviation, 1.0))
            normalized = min(0.90, normalized)
        else:
            normalized = (value - lo) / range_size
            normalized = 0.20 + (normalized * 0.75)
            normalized = max(0.20, min(0.95, normalized))
        return min_val + normalized * (max_val - min_val)
    elif label in ['Med', 'Medium', 'MEDIUM']:
        min_val = lo + (range_size * 0.05)
        max_val = hi - (range_size * 0.05)
        if value <= lo:
            deviation = (lo - value) / (range_size + 1e-10)
            normalized = 0.05 + (0.25 * min(deviation, 1.0))
            normalized = max(0.05, min(0.30, normalized))
        elif value >= hi:
            deviation = (value - hi) / (range_size + 1e-10)
            normalized = 0.70 + (0.25 * min(deviation, 1.0))
            normalized = min(0.95, normalized)
        else:
            normalized = (value - lo) / range_size
            normalized = 0.05 + (normalized * 0.90)
            normalized = max(0.05, min(0.95, normalized))
        return min_val + normalized * (max_val - min_val)
    else: # High
        if value < lo:
            if nutrient in ['B', 'Fe', 'Mn']:
                ratio = min((lo - value) / (range_size + 1e-10), 1.0)
                normalized = 0.05 + (ratio * 0.25)
            else:
                normalized = 0.10 + (0.20 * min((lo - value) / (range_size + 1e-10), 1.0))
            return lo + normalized * range_size
        elif value > hi:
            if nutrient in ['B', 'Fe', 'Mn']:
                overshoot = min((value - hi) / (range_size + 1e-10), 1.0)
                normalized = 0.50 + (overshoot * 0.45)
            else:
                normalized = 0.70 + (0.25 * min((value - hi) / (range_size + 1e-10), 1.0))
            return lo + normalized * range_size
        else:
            normalized = (value - lo) / range_size
            if nutrient in ['B', 'Fe', 'Mn']:
                normalized = 0.10 + (normalized * 0.85)
            else:
                normalized = 0.10 + (normalized * 0.80)
            normalized = max(0.05, min(0.95, normalized))
            return lo + normalized * range_size

def validate_prediction_range(value, min_limit, max_limit):
    return value, None
