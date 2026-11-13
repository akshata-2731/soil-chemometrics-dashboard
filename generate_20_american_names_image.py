import matplotlib.pyplot as plt
from pathlib import Path

# 20 American-style corporate, crisp, authoritative AgTech/ChemTech names (No Wave, Spectra, Omni, SoilLenz)
data = [
    [1, "TerraQuant", "Terra (Earth) + Quant (Quantitative)", "Definitive multi-nutrient ppm quantification vs estimation", "Commercial Soil Labs & SaaS"],
    [2, "PedoMatrix", "Pedon (Soil) + Matrix (76 Model Array)", "Unified machine learning matrix modeling soil chemistry", "Enterprise AI & Research Institutes"],
    [3, "AgroMetrics", "Agronomy + Metrology (Precision Measurement)", "Standardized high-throughput agricultural diagnostic scoring", "Large-Scale Farming & Agribusiness"],
    [4, "StrataLogic", "Strata (Soil Horizons) + Deterministic Logic", "Multi-depth nutrient profiling and boundary calibration", "Field Agronomy & Precision Ag"],
    [5, "ChemoSoil", "Chemometrics + Automated Soil Testing", "Direct multivariate regression for certified chemical outputs", "Certified Analytical Laboratories"],
    [6, "OptiPedon", "Optics (Photonics) + Pedon (Unit of Soil)", "Non-destructive optical sensing applied to soil pedology", "Academic Researchers & Soil Scientists"],
    [7, "VerdantIQ", "Verdant (Green Vitality) + Intelligence", "Predictive soil health engine driving high-yield crops", "Agronomic Advisory & Farm Management"],
    [8, "TerraPulse", "Terra (Soil) + Pulse (Optical Sensor Signal)", "Real-time non-destructive optical readings of soil status", "Handheld & Lab Diagnostic Hardware"],
    [9, "NutriGauge", "Nutrient (NPK, OC) + Gauge (Accurate Measure)", "Instant nutrient readouts and precision fertilizer metrics", "Commercial Fertilizer Companies"],
    [10, "AlbedoMetrics", "Albedo (Reflectance Physics) + Metrology", "Diffused surface reflectance modeling and light physics standard", "Sensor Metrology & Peer-Reviewed R&D"],
    [11, "FieldMatrix", "Field Operations + Multi-Model Algorithm Matrix", "Scalable field-to-lab calibration across 76 ML pipelines", "Contract Research & Ag Retailers"],
    [12, "PedoCore", "Pedology + Core Analytical Engine", "Centralized chemometric intelligence for national soil mapping", "State Agricultural Universities"],
    [13, "AgriChemIQ", "Agricultural Chemistry + Cognitive AI", "Deep learning resolution of complex macro/micronutrient overlaps", "Enterprise LIMS Software Integrators"],
    [14, "CulturaMetrics", "Agriculture / Cultivation + Metrology", "Precision measurement of soil biological and chemical balance", "Corporate Sustainability & Carbon Markets"],
    [15, "PhotoTerra", "Photon (Light Physics) + Terra (Soil)", "Instant photon-matter absorption analytics from UV to NIR", "Optical Spectroscopy Instrument Makers"],
    [16, "AcreLogic", "Acre (Farmland Land Unit) + Predictive Logic", "Actionable farm-level fertility insights from optical curves", "Crop Consultants & Precision Ag Retail"],
    [17, "SoluTerra", "Solution / Solum (True Soil) + Terra", "Comprehensive optical chemistry solving complex wet-lab delays", "Commercial Soil Testing Franchises"],
    [18, "PedoQuant", "Pedology + Quantitative Mathematical Solver", "Physics-constrained non-negative chemical concentration solver", "Global Soil Testing Standards Bodies"],
    [19, "YieldMatrix", "Yield Optimization + Multi-Model Machine Learning", "Direct correlation between optical soil health and crop tonnage", "Enterprise AgTech & Farm ERPs"],
    [20, "StrataLytics", "Strata (Soil Mineral Layers) + Analytics", "Continuous automated profiling across all 12 key nutrients", "Soil Survey Programs & Agronomists"]
]

columns = [
    "#", 
    "Platform Brand Name", 
    "Roots & Etymology", 
    "Core Scientific Value Communicated", 
    "Target Market (US & Global)"
]

fig, ax = plt.subplots(figsize=(18, 12), dpi=300)
ax.axis('off')
fig.patch.set_facecolor('#ffffff')

plt.suptitle("TOP 20 AMERICAN-STYLE AGTECH & CHEMOMETRIC BRAND IDENTITIES", 
             fontsize=18, fontweight='heavy', color='#0f172a', y=0.97)
plt.title("Authoritative, Commercial, and Scientific Names (Excluding 'Wave', 'Spectra', 'Omni', and 'SoilLenz')", 
          fontsize=11.5, color='#64748b', pad=14)

table = ax.table(
    cellText=data,
    colLabels=columns,
    cellLoc='left',
    loc='center',
    colWidths=[0.035, 0.16, 0.26, 0.33, 0.215]
)

table.auto_set_font_size(False)
table.set_fontsize(9.5)
table.scale(1, 1.85)

header_bg = '#1e293b'      # Deep Corporate Slate / US Tech Navy
header_fg = '#ffffff'
row_even_bg = '#f8fafc'    # Soft cool off-white
row_odd_bg = '#ffffff'     # Crisp white
border_color = '#e2e8f0'   # Clean subtle borders

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
            cell.set_text_props(color='#0284c7', fontweight='bold', fontsize=10.5)  # Clean US tech blue
        elif col == 4:
            cell.set_text_props(color='#0f766e', fontweight='semibold')
        else:
            cell.set_text_props(color='#334155')

artifact_dir = Path(r"C:\Users\hp\.gemini\antigravity\brain\5c582ecf-4ee1-4b1a-b76d-e943bc0c17cd")
artifact_dir.mkdir(parents=True, exist_ok=True)
out_artifact_path = artifact_dir / "Top_20_American_Style_Platform_Names.png"
out_local_path = Path("Top_20_American_Style_Platform_Names.png")

plt.tight_layout(rect=[0.015, 0.02, 0.985, 0.95])
plt.savefig(out_artifact_path, dpi=300, bbox_inches='tight')
plt.savefig(out_local_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"Generated 20-name matrix successfully: {out_artifact_path}")
