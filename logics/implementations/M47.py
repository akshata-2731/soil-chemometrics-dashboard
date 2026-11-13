from logics.implementations.logic_utils import logic47_predict, wrap_details

def predict(s, d, target="All"):
    if not d:
        return {
            "value": 0.0,
            "details": {"error": f"INCOMPLETE: Calibration data is required for {target}."}
        }
    val = logic47_predict(s, d, target)
    return wrap_details(val, "SG_SV", target)
