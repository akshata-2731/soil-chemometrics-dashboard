import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
from pathlib import Path

# Data for the table
data = [
    [1, "PolyWavelytics", "Poly (Multi) + Wave + Analytics", "Multi-band analysis across all 76 algorithms & 12 nutrients", "Very High", "Full AI Chemometric SaaS Platform"],
    [2, "TerraWave", "Terra (Soil/Earth) + Wave", "Non-destructive optical soil diagnostics from UV to NIR", "High", "Commercial Agri-Tech & Lab Testing"],
    [3, "WaveNexus", "Wave (Wavelengths) + Nexus (Hub)", "Convergence hub where optical signals meet ML algorithms", "High", "Multi-Model Evaluation & Testing Suite"],
    [4, "ChemWavelytics", "Chemistry + Wave + Analytics", "Direct chemometric prediction of chemical concentrations", "Very High", "Certified Analytical Laboratories"],
    [5, "PedoWave", "Pedon (Soil Unit) + Wave", "Formal pedological spectroscopy and soil physics", "Maximum", "Research Institutes & Soil Scientists"],
    [6, "WaveQuant", "Wave (Band) + Quantitative (% / ppm)", "Precision quantitative nutrient measurement vs detection", "High", "Quality Control & Precision Agronomy"],
    [7, "SpectroLytics", "Spectroscopy + Analytics", "Advanced chemometric decomposition & optical modeling", "High", "Spectrometer Hardware + Software Bundles"],
    [8, "PolySpectra", "Poly (Many) + Spectra (200-940 nm)", "Continuous multi-band chemometrics across ML pipelines", "High", "Research Portal & Model Benchmarking"],
    [9, "AlbedoMetrics", "Albedo (Reflectance) + Metrology", "Deep optical physics of diffuse soil surface reflectance", "Very High", "Sensor Metrology & Peer-Reviewed R&D"],
    [10, "StrataWave", "Strata (Soil Layers) + Wave", "Stratified soil profiling & comprehensive nutrient mapping", "High", "Field Testing & Soil Health Cards"]
]

columns = [
    "#", 
    "Scientific Platform Name", 
    "Etymology / Scientific Roots", 
    "What It Communicates to Researchers", 
    "Market Uniqueness", 
    "Best Target Audience"
]

# Set up the figure with high resolution and an Excel-like styling
fig, ax = plt.subplots(figsize=(16, 8.5), dpi=300)
ax.axis('off')

# Title section styled like an executive software report
fig.patch.set_facecolor('#ffffff')

plt.suptitle("SCIENTIFIC & CHEMOMETRIC BRAND IDENTITY MATRIX", 
             fontsize=17, fontweight='heavy', color='#0f172a', y=0.96)
plt.title("Candidate Platform Names for Soil Spectroscopy & Multi-Model Chemometrics System", 
          fontsize=11, color='#64748b', pad=14)

# Create table
table = ax.table(
    cellText=data,
    colLabels=columns,
    cellLoc='left',
    loc='center',
    colWidths=[0.04, 0.17, 0.22, 0.28, 0.12, 0.21]
)

table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 2.1)

# Color styling for headers and rows
header_bg = '#1e3a8a'      # Deep Navy Blue (Corporate / Excel Master style)
header_fg = '#ffffff'
row_even_bg = '#f8fafc'    # Soft cool slate
row_odd_bg = '#ffffff'     # Crisp white
border_color = '#cbd5e1'   # Subtle cell grid borders

for (row, col), cell in table.get_celld().items():
    cell.set_edgecolor(border_color)
    cell.set_linewidth(0.8)
    
    if row == 0:
        # Header formatting
        cell.set_facecolor(header_bg)
        cell.set_text_props(color=header_fg, fontweight='bold', fontsize=10.5)
        cell.set_height(0.065)
        if col == 0:
            cell.set_text_props(color=header_fg, fontweight='bold', ha='center')
    else:
        # Data row formatting
        bg = row_even_bg if row % 2 == 0 else row_odd_bg
        cell.set_facecolor(bg)
        cell.set_height(0.065)
        
        # Center the rank column
        if col == 0:
            cell.set_text_props(color='#475569', fontweight='bold', ha='center')
            
        # Highlight the name column in bold deep blue
        elif col == 1:
            cell.set_text_props(color='#0369a1', fontweight='bold', fontsize=10.5)
            
        # Highlight uniqueness tags
        elif col == 4:
            txt = cell.get_text().get_text()
            if "Maximum" in txt:
                cell.set_facecolor('#dcfce7')
                cell.set_text_props(color='#15803d', fontweight='bold')
            elif "Very High" in txt:
                cell.set_facecolor('#e0f2fe')
                cell.set_text_props(color='#0369a1', fontweight='bold')
            else:
                cell.set_text_props(color='#334155', fontweight='semibold')
        else:
            cell.set_text_props(color='#334155')

# Save to artifacts directory and workspace
artifact_dir = Path(r"C:\Users\hp\.gemini\antigravity\brain\5c582ecf-4ee1-4b1a-b76d-e943bc0c17cd")
artifact_dir.mkdir(parents=True, exist_ok=True)
out_artifact_path = artifact_dir / "Scientific_Platform_Names_Excel_Table.png"
out_local_path = Path("Scientific_Platform_Names_Excel_Table.png")

plt.tight_layout(rect=[0.02, 0.03, 0.98, 0.93])
plt.savefig(out_artifact_path, dpi=300, bbox_inches='tight')
plt.savefig(out_local_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"Image successfully saved to: {out_artifact_path}")
print(f"Local copy saved to: {out_local_path}")
