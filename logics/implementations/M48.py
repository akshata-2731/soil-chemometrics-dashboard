from logics.implementations.logic_utils import logic48_predict, wrap_details

def predict(s, d, target="All"):
    if not d:
        return {
            "value": 0.0,
            "details": {"error": f"INCOMPLETE: Calibration data is required for {target}."}
        }
    val = logic48_predict(s, d, target)
    return wrap_details(val, "Custom_IP_Euclidean", target, override_features=['ip1', 'ip2', 'ip3'])
