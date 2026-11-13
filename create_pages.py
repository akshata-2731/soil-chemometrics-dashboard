pages = ['Calibration', 'LogicLibrary', 'ActualPredicted', 'History', 'Settings']
for p in pages:
    code = f"""import React from 'react';\n\nfunction {p}() {{\n  return <div><div className='card-title'><span className='dot'></span>{p}</div><div className='alert alert-info'>UI Placeholder for {p}</div></div>;\n}}\n\nexport default {p};\n"""
    with open(f'frontend/src/pages/{p}.jsx', 'w') as f:
        f.write(code)
