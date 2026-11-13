import matplotlib.pyplot as plt
from pathlib import Path

# 20 Fresh names with tech/slang endings (-ix, -onix, -lytix, -ox) avoiding Wave/Spectra repetition
data = [
    [1, "Pedonix", "Pedon (Soil Unit) + -ix", "AI-driven pedological diagnostic engine for rapid, non-destructive nutrient readouts", "Soil Testing & Agricultural Institutes"],
    [2, "Terranix", "Terra (Earth/Soil) + -anix", "Multi-sensor earth intelligence platform translating optical readings into soil metrics", "Commercial Testing Franchises & SaaS"],
    [3, "Chemonix", "Chemometrics + -onix", "Multi-algorithm multivariate regression engine for certified chemical ppm outputs", "Certified Analytical & Soil Testing Labs"],
    [4, "Nutrionix", "Nutrient (NPK, OC) + Ionix", "Direct elemental ion quantification across all 12 macro- and micronutrient targets", "Commercial Fertilizer & Agribusiness"],
    [5, "Albedox", "Albedo (Optical Reflectance) + -ox", "Surface reflectance and scattering coefficient metrology across UV to NIR bands", "Optical Metrology & Sensor R&D"],
    [6, "Pedolytix", "Pedology + -lytix (Analytics)", "Specialized soil analytics suite running 76 chemometric pipelines simultaneously", "Enterprise Laboratory Workstations"],
    [7, "Stratonix", "Strata (Soil Horizons) + -onix", "Multi-depth nutrient profiling and layer-by-layer soil chemistry mapping", "Precision Field Agronomy & Mapping"],
    [8, "Optilytix", "Optics (Photonics) + -lytix", "Advanced optical data science and machine learning calibration workstation", "Hardware + Software Sensor Bundles"],
    [9, "Solumix", "Solum (True Soil Horizon) + -ix", "Quantitative chemical analysis across the complete biological and mineral soil matrix", "Soil Survey & Carbon Credit Projects"],
    [10, "Quantonix", "Quantitative (% / ppm) + -onix", "High-gain quantitative nutrient concentration solver replacing qualitative estimation", "Precision Lab Standards & Testing"],
    [11, "Humionix", "Humus (Soil Carbon) + Ionix", "High-precision optical detection of Organic Carbon (OC) and soil biological health", "Carbon Markets & Soil Health Advisory"],
    [12, "Luxonix", "Lux (Light Measurement) + -onix", "Precision sensor metrology interrogating optical channels from 200 nm to 940 nm", "Optical Sensor Hardware Manufacturers"],
    [13, "Matrixonix", "Algorithm Matrix (76 Models) + -onix", "Parallel multi-threaded execution matrix selecting champion models per nutrient", "Enterprise AI & Multi-Model Software"],
    [14, "Reflectix", "Diffuse Reflectance + -ix", "Automated diffuse reflectance chemometric decomposition and baseline correction", "Spectrometer Integration & Firmware"],
    [15, "Calibrix", "Calibration Standard + -ix", "Dynamic reference-tile standardization and soft-clamped boundary enforcement", "Quality Assurance & Metrology Suites"],
    [16, "Ionolytix", "Ionic Chemistry + -lytix", "Multi-spectral resolution of individual nutrient ionic signatures in soil solutions", "Specialized Chemistry & Testing Labs"],
    [17, "Sensolytix", "Sensor Array (21 Channels) + -lytix", "End-to-end multi-wavelength sensor integration and real-time inference engine", "Handheld & Mobile Testing Devices"],
    [18, "PedoQuantix", "Pedon + Quantitative Solver + -ix", "Physics-constrained non-negative chemical concentration solver preventing artifacts", "State & Global Testing Standards"],
    [19, "Acrolytix", "Acre (Farmland Unit) + -lytix", "Actionable farm-level fertility metrics and variable-rate fertilizer calculators", "Crop Consultants & Precision Ag Retail"],
    [20, "CogniTerra", "Cognitive AI + Terra (Earth/Soil)", "Self-learning predictive soil diagnostic engine continuously improving with new data", "Next-Gen AgTech & Cloud ERPs"]
]

columns = [
    "#", 
    "Brand Identity Name", 
    "Roots & Slang Phonation", 
    "Core Scientific Capability Communicated", 
    "Target Commercial Sector"
]

fig, ax = plt.subplots(figsize=(18.5, 12.2), dpi=300)
ax.axis('off')
fig.patch.set_facecolor('#ffffff')

plt.suptitle("NEW TECH-SLANG BRAND IDENTITIES (-ix, -onix, -lytix, -ox)", 
             fontsize=18, fontweight='heavy', color='#0f172a', y=0.97)
plt.title("High-Tech Compounds Derived from Soil Science, Chemometrics, Optical Physics & Elemental Chemistry", 
          fontsize=11.5, color='#64748b', pad=14)

table = ax.table(
    cellText=data,
    colLabels=columns,
    cellLoc='left',
    loc='center',
    colWidths=[0.035, 0.155, 0.27, 0.355, 0.20]
)

table.auto_set_font_size(False)
table.set_fontsize(9.5)
table.scale(1, 1.85)

header_bg = '#0f172a'      # Modern Deep Tech Slate
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
        cell.set_height(0.043)
        
        if col == 0:
            cell.set_text_props(color='#64748b', fontweight='bold', ha='center')
        elif col == 1:
            # Highlight brand names in high-tech cyan/blue
            cell.set_text_props(color='#0284c7', fontweight='bold', fontsize=10.5)
        elif col == 4:
            cell.set_text_props(color='#0f766e', fontweight='semibold')
        else:
            cell.set_text_props(color='#1e293b')

artifact_dir = Path(r"C:\Users\hp\.gemini\antigravity\brain\5c582ecf-4ee1-4b1a-b76d-e943bc0c17cd")
artifact_dir.mkdir(parents=True, exist_ok=True)
out_artifact_path = artifact_dir / "Tech_Slang_Brand_Identities_Matrix.png"
out_local_path = Path("Tech_Slang_Brand_Identities_Matrix.png")

plt.tight_layout(rect=[0.015, 0.02, 0.985, 0.95])
plt.savefig(out_artifact_path, dpi=300, bbox_inches='tight')
plt.savefig(out_local_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"Generated successfully: {out_artifact_path}")
