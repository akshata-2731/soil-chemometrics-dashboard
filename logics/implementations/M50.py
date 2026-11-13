from logics.implementations.logic_utils import logic50_predict, wrap_details

def predict(s, d, target="All"):
    val = logic50_predict(s, d, target)
    return wrap_details(val, "Mahalanobis Distance", target, override_features=['ip1 (A-H, R)', 'ip2 (I-L, U-W)', 'ip3 (U-W)'])
