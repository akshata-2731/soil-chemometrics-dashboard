import matplotlib.pyplot as plt
import os
from pathlib import Path

# Data without 'Wave', 'Spectra', or 'Omni'
data = [
    [1, "PedoMatrix", "Pedon (Soil) + Matrix (76 ML Models)", "Mathematical soil modeling across physical & chemical data layers", "High", "Enterprise AI & Research Labs"],
    [2, "TerraQuant", "Terra (Earth) + Quantitative (% / ppm)", "Definitive chemical nutrient quantification vs qualitative detection", "Very High", "Commercial Testing Labs & SaaS"],
    [3, "SoilLenz", "Soil + Lenz (Optical Sensing Engine)", "Non-destructive optical diagnostic lens peering into soil chemistry", "High", "Core Brand / Hardware-Software Suite"],
    [4, "OptiPedon", "Optics (Light) + Pedon (Unit of Soil)", "Optical photonics applied to pedological physical soil structures", "Maximum", "Soil Scientists & Agronomists"],
    [5, "ChemoSoil", "Chemometrics + Soil Chemistry", "Direct chemometric multi-target modeling (OC, N, P, K, pH, EC)", "Very High", "Certified Analytical Laboratories"],
    [6, "AlbedoMetrics", "Albedo (Reflectance) + Metrology", "Diffused surface reflectance metrology & optical physics standard", "Very High", "Academic & Scientific R&D"],
    [7, "StrataLytics", "Strata (Soil Horizons) + Analytics", "Layer-by-layer nutrient profiling and stratified soil diagnostics", "High", "Field Agronomy & Precision Farming"],
    [8, "NutriLenz", "Nutrient + Lenz (Visual Quantification)", "Instant optical visibility into soil macro & micro nutrient health", "High", "Commercial Farm & Fertilizer Testing"],
    [9, "PhotoTerra", "Photon (Light Physics) + Terra (Soil)", "Non-destructive photon-matter interaction for instant evaluation", "High", "Optical Instrument Manufacturers"],
    [10, "PedoMetric", "Pedometrics (Soil Math Science)", "The official scientific discipline of mathematical soil modeling", "Maximum", "Government & University Research"]
]

columns = [
    "#", 
    "Platform Name", 
    "Scientific Etymology & Meaning", 
    "Core Value Communicated to Researchers", 
    "Uniqueness", 
    "Best Target Market"
]

fig, ax = plt.subplots(figsize=(16, 8.5), dpi=300)
ax.axis('off')
fig.patch.set_facecolor('#ffffff')

plt.suptitle("SCIENTIFIC PLATFORM & DOMAIN IDENTITY MATRIX", 
             fontsize=17, fontweight='heavy', color='#0f172a', y=0.96)
plt.title("Curated Premium Names (Excluding 'Wave', 'Spectra', & 'Omni') for Soil Diagnostics Platform", 
          fontsize=11, color='#64748b', pad=14)

table = ax.table(
    cellText=data,
    colLabels=columns,
    cellLoc='left',
    loc='center',
    colWidths=[0.04, 0.16, 0.25, 0.28, 0.11, 0.20]
)

table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 2.1)

header_bg = '#0f766e'      # Deep Teal / Emerald (Scientific Earth & Precision tone)
header_fg = '#ffffff'
row_even_bg = '#f0fdfa'    # Soft Mint/Slate
row_odd_bg = '#ffffff'
border_color = '#cbd5e1'

for (row, col), cell in table.get_celld().items():
    cell.set_edgecolor(border_color)
    cell.set_linewidth(0.8)
    
    if row == 0:
        cell.set_facecolor(header_bg)
        cell.set_text_props(color=header_fg, fontweight='bold', fontsize=10.5)
        cell.set_height(0.065)
        if col == 0:
            cell.set_text_props(color=header_fg, fontweight='bold', ha='center')
    else:
        bg = row_even_bg if row % 2 == 0 else row_odd_bg
        cell.set_facecolor(bg)
        cell.set_height(0.065)
        
        if col == 0:
            cell.set_text_props(color='#475569', fontweight='bold', ha='center')
        elif col == 1:
            cell.set_text_props(color='#0f766e', fontweight='bold', fontsize=11)
        elif col == 4:
            txt = cell.get_text().get_text()
            if "Maximum" in txt:
                cell.set_facecolor('#dcfce7')
                cell.set_text_props(color='#15803d', fontweight='bold')
            elif "Very High" in txt:
                cell.set_facecolor('#ccfbf1')
                cell.set_text_props(color='#0f766e', fontweight='bold')
            else:
                cell.set_text_props(color='#334155', fontweight='semibold')
        else:
            cell.set_text_props(color='#334155')

artifact_dir = Path(r"C:\Users\hp\.gemini\antigravity\brain\5c582ecf-4ee1-4b1a-b76d-e943bc0c17cd")
artifact_dir.mkdir(parents=True, exist_ok=True)
out_artifact_path = artifact_dir / "Curated_Scientific_Platform_Names.png"
out_local_path = Path("Curated_Scientific_Platform_Names.png")

plt.tight_layout(rect=[0.02, 0.03, 0.98, 0.93])
plt.savefig(out_artifact_path, dpi=300, bbox_inches='tight')
plt.savefig(out_local_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"Generated successfully: {out_artifact_path}")
