from logics.implementations.logic_utils import logic49_predict, wrap_details

def predict(s, d, target="All"):
    val = logic49_predict(s, d, target)
    
    # Dynamically show only the features actually used for the target nutrient
    if target == 'N': used = ['ip3', 'N_ip1']
    elif target == 'P': used = ['ip1', 'ip2']
    elif target == 'K': used = ['ip1', 'ip2', 'ip3']
    elif target == 'Cu': used = ['ip2']
    else: used = ['ip1'] # OC, Ca, Mg, S, Fe, Mn, Zn, B all use only IP1
    
    return wrap_details(val, "IP Zone Classification Logic", target, override_features=used)
