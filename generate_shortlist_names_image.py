import matplotlib.pyplot as plt
from pathlib import Path

# Data directly from the user's shortlisted 13 names + selected cohesive expansions (up to 16 for a clean grid)
data = [
    [1, "Wavecognix", "Wave (Wavelength) + Cognix (Cognitive AI)", "Cognitive deep-learning engine extracting soil nutrient patterns from spectral waves", "AI Model Benchmarking & Testing"],
    [2, "Waveionix", "Wave (Light Spectrum) + Ionix (Ionic / Chemistry)", "Ionic macro/micronutrient detection via continuous optical wavelength curves", "Certified Analytical Laboratories"],
    [3, "Omniwavelytics", "Omni (All-Encompassing) + Wave + Analytics", "Unified multi-band analytics across 21 optical channels and 76 ML pipelines", "Enterprise Chemometric Cloud SaaS"],
    [4, "Spectralogica", "Spectra (Reflectance) + Logica (Latin for Logic)", "Deterministic mathematical logic combined with continuous spectral absorption curves", "Calibration & Formula Management"],
    [5, "Spectralogix", "Spectra + Logix (Computational Intelligence)", "Automated algorithmic logic engine optimizing accuracy per target nutrient", "Multi-Algorithm Research Suites"],
    [6, "Spectrolytix", "Spectroscopy + Lytix (Advanced Analytics)", "Precision chemometric decomposition and quantitative nutrient concentration solver", "High-Throughput Soil Testing Labs"],
    [7, "Spectrionix", "Spectra + Ionix (Elemental Chemistry)", "Direct elemental ion quantification (NPK, Ca, Mg, S, Fe, Mn, Zn, B) from spectra", "Precision Agriculture & Soil Health"],
    [8, "Dataspectronix", "Data (Big Data/ML) + Spectronix", "Large-scale spectral data infrastructure driving automated multi-model training", "Enterprise Data Platforms & LIMS"],
    [9, "WaveIntelix", "Wave (Optical Signals) + Intelix (Intelligence)", "Predictive optical intelligence translating raw spectrometer signals to soil cards", "Agronomic Advisory & Farm ERPs"],
    [10, "WaveOmnix", "Wave + Omnix (Universal Multi-Target Array)", "Universal multi-wavelength array evaluating all target nutrients simultaneously", "Benchtop Spectrometer Workstations"],
    [11, "Datronix", "Data (Measurements) + Tronix (Instrumentation)", "High-speed laboratory instrumentation data processor and sensor interface", "Hardware Sensor Firmware & Labs"],
    [12, "Lumonix", "Lumen / Luma (Light Physics) + Ionix", "Non-destructive optical photonics interrogating soil matrices via reflected light", "Optical Sensor Hardware Manufacturers"],
    [13, "Calibronix", "Calibration + Tronix (Standard Metrology)", "Automated zero-set baseline standardization and dynamic soft-clamping engine", "Metrology & Quality Assurance Systems"],
    [14, "Pedonix", "Pedon (Fundamental Soil Unit) + Tronix", "Dedicated soil-specific spectroscopic instrument suite for pedological analysis", "Universities & Soil Survey Institutes"],
    [15, "OptiLogix", "Optics (Photonics) + Logix (Predictive Logic)", "Optical multi-channel modeling engine with physics-based boundary constraints", "Precision Soil Diagnostics"],
    [16, "Chemonix", "Chemometrics + Ionix / Tronix", "Pure chemometric modeling software resolving complex diffuse reflectance curves", "Analytical Testing Franchises"]
]

columns = [
    "#", 
    "Platform Brand Name", 
    "Etymology & Core Roots", 
    "Scientific Capability Communicated", 
    "Best Target Market"
]

fig, ax = plt.subplots(figsize=(18, 11), dpi=300)
ax.axis('off')
fig.patch.set_facecolor('#ffffff')

plt.suptitle("SHORTLISTED SCIENTIFIC & TECH BRAND IDENTITIES", 
             fontsize=18, fontweight='heavy', color='#0f172a', y=0.97)
plt.title("Executive Brand Matrix for Soil Spectroscopy, Multi-Model Machine Learning & Chemometric Analytics", 
          fontsize=11.5, color='#64748b', pad=14)

table = ax.table(
    cellText=data,
    colLabels=columns,
    cellLoc='left',
    loc='center',
    colWidths=[0.035, 0.16, 0.25, 0.355, 0.20]
)

table.auto_set_font_size(False)
table.set_fontsize(9.5)
table.scale(1, 1.85)

header_bg = '#1e1b4b'      # Deep Premium Indigo / Scientific Tech
header_fg = '#ffffff'
row_even_bg = '#f8fafc'    # Soft cool off-white
row_odd_bg = '#ffffff'     # Crisp white
border_color = '#e2e8f0'   # Subtle cell grid borders

for (row, col), cell in table.get_celld().items():
    cell.set_edgecolor(border_color)
    cell.set_linewidth(0.8)
    
    if row == 0:
        cell.set_facecolor(header_bg)
        cell.set_text_props(color=header_fg, fontweight='bold', fontsize=10.5)
        cell.set_height(0.046)
        if col == 0:
            cell.set_text_props(color=header_fg, fontweight='bold', ha='center')
    else:
        bg = row_even_bg if row % 2 == 0 else row_odd_bg
        cell.set_facecolor(bg)
        cell.set_height(0.044)
        
        if col == 0:
            cell.set_text_props(color='#64748b', fontweight='bold', ha='center')
        elif col == 1:
            # Highlight the exact 13 names requested with high contrast branding
            cell.set_text_props(color='#4338ca', fontweight='bold', fontsize=10.5)  # Modern Indigo Tech
        elif col == 4:
            cell.set_text_props(color='#0f766e', fontweight='semibold')
        else:
            cell.set_text_props(color='#334155')

artifact_dir = Path(r"C:\Users\hp\.gemini\antigravity\brain\5c582ecf-4ee1-4b1a-b76d-e943bc0c17cd")
artifact_dir.mkdir(parents=True, exist_ok=True)
out_artifact_path = artifact_dir / "Shortlisted_Brand_Names_Matrix.png"
out_local_path = Path("Shortlisted_Brand_Names_Matrix.png")

plt.tight_layout(rect=[0.015, 0.02, 0.985, 0.95])
plt.savefig(out_artifact_path, dpi=300, bbox_inches='tight')
plt.savefig(out_local_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"Generated successfully: {out_artifact_path}")
