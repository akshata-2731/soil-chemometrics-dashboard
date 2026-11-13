from logics.implementations.logic_utils import logic51_predict, wrap_details

def predict(s, d, target="All"):
    val = logic51_predict(s, d, target)
    return wrap_details(val, "SAM + SRI Classification", target, override_features=['ip1', 'ip2', 'ip3', 'SRI'])
