import matplotlib.pyplot as plt
from pathlib import Path

# 20 Complex, Heavy-Duty Industrial/Analytical Instrument Names (Hach/Tach style, -ex, -on, -or, Metrology)
data = [
    [1, "PedoTach", "Pedon (Soil Unit) + Tach (Precision Speed/Metrology)", "High-velocity pedological diagnostic instrument; translates sensor signals into rapid nutrient readouts", "Certified Lab Benchtop Hardware"],
    [2, "Agronach", "Agronomy + -ach (Heavy Industrial Suffix)", "Automated agricultural chemometric analyzer for rapid macro- and micro-element quantification", "Industrial Field Apparatus & Enterprise Ag"],
    [3, "OptiTach", "Optics (Photonics) + Tach (Metrology Gauge)", "High-throughput optical interrogation unit measuring photon absorbance without sample destruction", "Ultra-Fast Optical Testing Systems"],
    [4, "ChemoTach", "Chemometrics + Tachometer (Rapid Calculation)", "Instantaneous multi-algorithm chemometric regression engine resolving complex sensor curves", "Analytical Chemical Workstations"],
    [5, "Pedonex", "Pedon (Soil) + Nexus / Next-Gen Analytical", "Next-generation pedological analytical platform linking optical reflectance to certified NPK/OC curves", "Commercial Laboratory SaaS Suite"],
    [6, "Albedox", "Albedo (Reflectance Physics) + Index / Flux", "Surface reflectance and scattering coefficient metrology engine; computes exact multi-band absorbance", "Optical Metrology & Sensor R&D"],
    [7, "ZoilTach", "Solum / Soil + Tach (Precision Metrology)", "High-gain optical calibration engine for continuous non-destructive soil matrix quantification", "Heavy-Duty Soil Testing Hardware"],
    [8, "Nutrixor", "Nutrient + Matrix Factor / Solver", "Deconstructs complex diffuse reflectance curves into discrete elemental concentrations (ppm / %)", "Automated Nutrient Analyzers"],
    [9, "StrataNorm", "Strata (Soil Horizons) + Normalized Standard", "Standardized baseline normalization across diverse mineral textures, organic matter, and moisture levels", "ISO-Compliant Quality Assurance Tools"],
    [10, "PedoMetricus", "Latinized Pedometrics (Mathematical Soil Science)", "Rigorous formal mathematical and statistical pedology running multi-algorithm benchmarking", "Academic Research & Soil Surveys"],
    [11, "VektorPed", "Spectral Vector (21 Channels) + Pedon (Soil)", "High-dimensional multi-band optical vector modeling for non-linear soil property prediction", "Advanced Chemometric Software"],
    [12, "ChemoDyn", "Chemometrics + Dynamic Boundary Modeling", "Dynamic two-stage classification and continuous high-gain regression engine for nutrient limits", "Proprietary AI Prediction Engines"],
    [13, "QuantaSolum", "Quanta (Discrete Photons) + Solum (True Soil)", "Photon energy quantification applied to true soil biological, organic, and mineral matrices", "Cutting-Edge Optical Physics Labs"],
    [14, "OptiMatrix", "Optical Interrogation + Multi-Model Matrix", "Parallel multi-threaded evaluation of 76 machine learning pipelines on optical reflectance data", "Enterprise LIMS Software Platforms"],
    [15, "TerraTach", "Terra (Earth) + Tach (High-Throughput Gauge)", "Rapid non-destructive soil diagnostic controller replacing traditional slow wet-chemistry digestion", "Contract Testing Facilities"],
    [16, "SoluNorm", "Solum (Soil) + Solution + Normalized Metrology", "Analytical optical engine resolving physical sensor drift and ambient calibration variance", "Field Calibration & Metrology Tools"],
    [17, "AgriTach", "Agriculture + Tach (Standardized Measurement)", "Direct farm-to-cloud diagnostic device providing instant agronomic fertility recommendations", "Ag Retailers & Fertilizer Franchises"],
    [18, "PedoQuant", "Pedology + Quantitative Mathematical Solver", "Physics-constrained non-negative chemical concentration solver preventing mathematical artifacts", "State & National Testing Standards"],
    [19, "Chronosol", "Chronos (Time/Speed) + Solum (Soil Chemistry)", "Instantaneous temporal soil diagnostics replacing weeks of conventional laboratory turnaround", "Fast-Turnaround Commercial Labs"],
    [20, "FormuTach", "Formulation / Chemical Logic + Tach", "Automated calibration logic engine matching mathematical formulas with continuous sensor arrays", "Calibration & Logic Management Suites"]
]

columns = [
    "#", 
    "Analytical Instrument Name", 
    "Etymology & Engineering Roots", 
    "Scientific Capability Communicated", 
    "Primary Target Segment"
]

fig, ax = plt.subplots(figsize=(18.5, 12.5), dpi=300)
ax.axis('off')
fig.patch.set_facecolor('#ffffff')

plt.suptitle("INDUSTRIAL & METROLOGY INSTRUMENT BRAND IDENTITIES", 
             fontsize=18, fontweight='heavy', color='#0f172a', y=0.97)
plt.title("High-Tech, Complex Names (Hach/Tach Style, -ex, -on, -or, Precision Metrology) for Soil Spectroscopy & Chemometrics", 
          fontsize=11.5, color='#64748b', pad=14)

table = ax.table(
    cellText=data,
    colLabels=columns,
    cellLoc='left',
    loc='center',
    colWidths=[0.035, 0.155, 0.275, 0.335, 0.20]
)

table.auto_set_font_size(False)
table.set_fontsize(9.5)
table.scale(1, 1.85)

header_bg = '#0f172a'      # Deep German Industrial Obsidian Slate
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
        cell.set_height(0.045)
        if col == 0:
            cell.set_text_props(color=header_fg, fontweight='bold', ha='center')
    else:
        bg = row_even_bg if row % 2 == 0 else row_odd_bg
        cell.set_facecolor(bg)
        cell.set_height(0.043)
        
        if col == 0:
            cell.set_text_props(color='#64748b', fontweight='bold', ha='center')
        elif col == 1:
            cell.set_text_props(color='#0369a1', fontweight='bold', fontsize=10.5)  # Heavy Industrial Blue
        elif col == 4:
            cell.set_text_props(color='#475569', fontweight='semibold')
        else:
            cell.set_text_props(color='#1e293b')

artifact_dir = Path(r"C:\Users\hp\.gemini\antigravity\brain\5c582ecf-4ee1-4b1a-b76d-e943bc0c17cd")
artifact_dir.mkdir(parents=True, exist_ok=True)
out_artifact_path = artifact_dir / "Top_20_Industrial_Analytical_Names.png"
out_local_path = Path("Top_20_Industrial_Analytical_Names.png")

plt.tight_layout(rect=[0.015, 0.02, 0.985, 0.95])
plt.savefig(out_artifact_path, dpi=300, bbox_inches='tight')
plt.savefig(out_local_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"Generated successfully: {out_artifact_path}")
